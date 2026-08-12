"""FastAPI application with ingestion, query, evaluation, and demo seed."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Body, Depends, FastAPI, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from src.api import state
from src.api.auth import rate_limit, verify_api_key, verify_demo_key
from src.api.schemas import (
    AuditReportResponse,
    CitationDetail,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    VerificationDetail,
    VerificationReport,
)
from src.config.settings import settings
from src.generation.pipeline import (
    build_query_engine,
    extract_citations,
    verify_citations,
)
from src.ingestion.pipeline import run_ingestion
from src.retrieval.pipeline import build_full_retrieval_pipeline
from src.utils.langfuse_tracer import get_langfuse, init_langfuse_llama_index
from src.utils.logging import get_logger

log = get_logger("api")

DEMO_DIR = Path("data/demo")
UPLOAD_DIR = Path("data/uploads")
ALLOWED_UPLOAD_EXT = {".pdf", ".md", ".txt", ".docx"}


def _index_pipeline(nodes):
    _, hybrid_retriever, reranker = build_full_retrieval_pipeline(nodes)
    state.set_nodes(nodes)
    state.set_hybrid_retriever(hybrid_retriever)
    state.set_reranker(reranker)
    post = [reranker] if reranker is not None else []
    query_engine = build_query_engine(
        retriever=hybrid_retriever,
        node_postprocessors=post,
    )
    state.set_query_engine(query_engine)
    return nodes


def seed_demo_corpus() -> dict:
    """Ingest only data/demo markdown/txt into the in-memory index."""
    if not DEMO_DIR.exists():
        raise FileNotFoundError(f"Missing demo corpus directory: {DEMO_DIR}")

    files = [
        p
        for p in DEMO_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".md", ".txt"}
    ]
    if not files:
        raise FileNotFoundError("No .md/.txt files in data/demo/")

    nodes = run_ingestion(input_dir=str(DEMO_DIR))
    _index_pipeline(nodes)
    docs = len({n.metadata.get("source") for n in nodes})
    log.info("demo_seed_complete", documents=docs, chunks=len(nodes))
    return {
        "status": "ok",
        "documents_indexed": docs,
        "chunks_created": len(nodes),
        "sources": sorted({n.metadata.get("source", "?") for n in nodes}),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", auto_seed=settings.demo_auto_seed)
    init_langfuse_llama_index()
    if settings.demo_auto_seed:
        try:
            await run_in_threadpool(seed_demo_corpus)
            log.info("startup_seed_ok")
        except Exception as exc:
            # Boot without index if keys/missing data — UI still loads offline
            log.warning("startup_seed_failed", error=str(exc)[:200])
    yield
    log.info("shutdown")


app = FastAPI(title="CiteRAG API", version="0.2.0", lifespan=lifespan)

_origins = [o.strip() for o in (settings.cors_origins or "").split(",") if o.strip()]
if not _origins:
    _origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    nodes = state.get_nodes()
    sources = sorted({n.metadata.get("source", "?") for n in nodes}) if nodes else []
    return {
        "status": "ok",
        "indexed": nodes is not None and len(nodes) > 0,
        "chunks": len(nodes) if nodes else 0,
        "documents": len(sources),
        "sources": sources,
        "version": "0.2.0",
    }


@app.post("/demo/seed", response_model=IngestResponse)
async def demo_seed(
    _client: str = Depends(verify_demo_key),
    _rate: str = Depends(rate_limit),
):
    """Public demo seed — indexes data/demo only (does not wipe uploads path)."""
    try:
        result = await run_in_threadpool(seed_demo_corpus)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        log.warning("demo_seed_failed", error=str(exc)[:200])
        raise HTTPException(
            status_code=500,
            detail=f"Demo seed failed: {exc}",
        ) from exc
    return IngestResponse(
        status=result["status"],
        documents_indexed=result["documents_indexed"],
        chunks_created=result["chunks_created"],
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    files: Optional[list[UploadFile]] = None,
    _client: str = Depends(verify_api_key),
    _rate: str = Depends(rate_limit),
):
    """Upload documents and rebuild the index from data/uploads (+ any prior uploads)."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    if files:
        for file in files:
            raw_name = Path(file.filename or "uploaded_doc").name
            suffix = Path(raw_name).suffix.lower()
            if suffix and suffix not in ALLOWED_UPLOAD_EXT:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {suffix}. Allowed: {sorted(ALLOWED_UPLOAD_EXT)}",
                )
            content = await file.read()
            if len(content) > 15 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File too large (max 15MB)")
            (UPLOAD_DIR / raw_name).write_bytes(content)

    # Prefer uploads dir; fall back to legacy ./data if empty
    ingest_dir = UPLOAD_DIR if any(UPLOAD_DIR.iterdir()) else Path("./data")
    if not ingest_dir.exists() or not any(
        p.is_file() and p.suffix.lower() in ALLOWED_UPLOAD_EXT for p in ingest_dir.rglob("*")
    ):
        raise HTTPException(
            status_code=400,
            detail="No documents to ingest. Upload files or call /demo/seed.",
        )

    def _run():
        nodes = run_ingestion(input_dir=str(ingest_dir))
        _index_pipeline(nodes)
        return nodes

    try:
        nodes = await run_in_threadpool(_run)
    except Exception as exc:
        log.warning("ingest_failed", error=str(exc)[:200])
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}") from exc

    log.info("ingest_complete", chunks=len(nodes))
    return IngestResponse(
        status="ok",
        documents_indexed=len({n.metadata.get("source") for n in nodes}),
        chunks_created=len(nodes),
    )


@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    _client: str = Depends(verify_demo_key),
    _rate: str = Depends(rate_limit),
):
    """Query the RAG pipeline and return citation-grounded answer + verification."""
    qe = state.get_query_engine()
    if qe is None:
        log.warning("query_rejected", reason="no_index")
        raise HTTPException(
            status_code=400,
            detail="No documents indexed. Call /demo/seed or /ingest first.",
        )

    def _run_query():
        response = qe.query(request.question)
        source_nodes = response.source_nodes
        text = str(response)
        citations = extract_citations(text)
        verification_dc = verify_citations(text, source_nodes)
        return text, source_nodes, citations, verification_dc

    try:
        text, source_nodes, citations, verification_dc = await run_in_threadpool(
            _run_query
        )
    except Exception as exc:
        log.warning("query_failed", error=str(exc)[:200])
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc

    try:
        langfuse = get_langfuse()
        if settings.langfuse_public_key:
            trace = langfuse.trace(
                name="rag-query", input={"question": request.question}
            )
            trace.update(
                output={"answer": text},
                metadata={
                    "citations_found": len(citations),
                    "citation_accuracy": verification_dc.accuracy,
                    "sources_retrieved": len(source_nodes),
                    "is_refusal": verification_dc.is_refusal,
                },
            )
    except Exception:
        pass

    log.info(
        "query_complete",
        question=request.question[:100],
        citations=len(citations),
        accuracy=verification_dc.accuracy,
        is_refusal=verification_dc.is_refusal,
    )

    return QueryResponse(
        answer=text,
        citations=[
            CitationDetail(source=c.source, page=c.page, claim=c.claim)
            for c in citations
        ],
        verification=VerificationReport(
            total_citations=verification_dc.total_citations,
            verified=verification_dc.verified,
            accuracy=verification_dc.accuracy,
            is_refusal=verification_dc.is_refusal,
            details=[
                VerificationDetail(
                    citation=CitationDetail(
                        source=vd.citation.source,
                        page=vd.citation.page,
                        claim=vd.citation.claim,
                    ),
                    supported=vd.supported,
                    source_text=vd.source_text,
                )
                for vd in verification_dc.details
            ],
        ),
        evaluation={
            "citation_accuracy": verification_dc.accuracy,
            "citations_found": len(citations),
            "citations_verified": verification_dc.verified,
            "is_refusal": verification_dc.is_refusal,
            "sources_retrieved": len(source_nodes),
        },
    )


@app.post("/evaluate", response_model=dict)
async def evaluate(
    eval_data: list[dict] = Body(...),
    _client: str = Depends(verify_api_key),
):
    if not eval_data:
        raise HTTPException(status_code=400, detail="eval_data is required")
    from src.evaluation.ragas_harness import run_ragas_evaluation

    return await run_in_threadpool(run_ragas_evaluation, eval_data)


@app.post("/evaluate-single", response_model=dict)
async def evaluate_single(
    request: QueryRequest,
    _client: str = Depends(verify_api_key),
):
    qe = state.get_query_engine()
    if qe is None:
        raise HTTPException(status_code=400, detail="No documents indexed.")

    from src.evaluation.deepeval_harness import evaluate_single_response

    def _run():
        response = qe.query(request.question)
        context = [node.text for node in response.source_nodes]
        return evaluate_single_response(
            question=request.question,
            actual_output=str(response),
            retrieval_context=context,
        )

    return await run_in_threadpool(_run)


@app.post("/audit-report/{collection}", response_model=AuditReportResponse)
async def audit_report(
    collection: str,
    golden_dataset: list[dict] = Body(None),
    improvements: Optional[str] = None,
    _client: str = Depends(verify_api_key),
):
    from src.evaluation.audit_report import generate_audit_report, run_audit

    improvement_list = (
        [i.strip() for i in improvements.split(",")] if improvements else []
    )

    if golden_dataset:
        report = await run_in_threadpool(
            run_audit,
            collection_name=collection,
            golden_dataset=golden_dataset,
            documents_dir="./data",
            improvements=improvement_list,
        )
    else:
        report = generate_audit_report(
            collection_name=collection,
            baseline_metrics={"faithfulness": 0.0},
            optimized_metrics={"faithfulness": 0.0},
            improvements=improvement_list,
            sample_questions=[],
        )
    return report
