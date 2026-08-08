"""FastAPI application with ingestion, query, and evaluation endpoints."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, HTTPException, Body, Depends, Request
from typing import Optional

from src.api.schemas import (
    QueryRequest,
    QueryResponse,
    IngestResponse,
    AuditReportResponse,
    CitationDetail,
    VerificationDetail,
    VerificationReport,
)
from src.api import state
from src.ingestion.pipeline import run_ingestion
from src.retrieval.pipeline import build_full_retrieval_pipeline
from src.generation.pipeline import (
    build_query_engine,
    extract_citations,
    verify_citations,
)
from src.evaluation.ragas_harness import run_ragas_evaluation
from src.evaluation.deepeval_harness import evaluate_single_response
from src.evaluation.audit_report import generate_audit_report, run_audit
from src.api.auth import verify_api_key, rate_limit
from src.utils.langfuse_tracer import get_langfuse, init_langfuse_llama_index
from src.utils.logging import get_logger

log = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup")
    init_langfuse_llama_index()
    yield
    log.info("shutdown")


app = FastAPI(title="RAG Citation API", version="0.1.0", lifespan=lifespan)


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    files: Optional[list[UploadFile]] = None,
    client: str = Depends(verify_api_key),
    _rate: str = Depends(rate_limit),
):
    """Ingest and index documents. If files are uploaded, saves them to ./data first."""
    from pathlib import Path

    if files:
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        for file in files:
            content = await file.read()
            file_path = data_dir / Path(file.filename or "uploaded_doc").name
            file_path.write_bytes(content)

    nodes = run_ingestion(input_dir="./data")
    state.set_nodes(nodes)
    log.info("ingest_complete", chunks=len(nodes))

    _, hybrid_retriever, reranker = build_full_retrieval_pipeline(nodes)
    state.set_hybrid_retriever(hybrid_retriever)
    state.set_reranker(reranker)

    query_engine = build_query_engine(
        retriever=hybrid_retriever,
        node_postprocessors=[reranker],
    )
    state.set_query_engine(query_engine)

    return IngestResponse(
        status="ok",
        documents_indexed=len({n.metadata.get("source") for n in nodes}),
        chunks_created=len(nodes),
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG pipeline and receive a citation-grounded answer with verification."""
    qe = state.get_query_engine()
    if qe is None:
        log.warning("query_rejected", reason="no_index")
        raise HTTPException(status_code=400, detail="No documents indexed. Call /ingest first.")

    langfuse = get_langfuse()
    trace = langfuse.trace(name="rag-query", input={"question": request.question})

    response = qe.query(request.question)
    source_nodes = response.source_nodes

    citations = extract_citations(str(response))
    verification_dc = verify_citations(str(response), source_nodes)

    trace.update(
        output={"answer": str(response)},
        metadata={
            "citations_found": len(citations),
            "citation_accuracy": verification_dc.accuracy if verification_dc.total_citations > 0 else 0,
            "sources_retrieved": len(source_nodes),
        },
    )

    log.info(
        "query_complete",
        question=request.question[:100],
        citations=len(citations),
        accuracy=verification_dc.accuracy,
        is_refusal=verification_dc.is_refusal,
    )

    return QueryResponse(
        answer=str(response),
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
            "citation_accuracy": verification_dc.accuracy if verification_dc.total_citations > 0 else 0.0,
            "citations_found": len(citations),
            "citations_verified": verification_dc.verified,
            "is_refusal": verification_dc.is_refusal,
            "sources_retrieved": len(source_nodes),
        },
    )


@app.post("/evaluate", response_model=dict)
async def evaluate(eval_data: list[dict] = Body(...)):
    """Run RAGAS evaluation on provided Q&A pairs."""
    if not eval_data:
        raise HTTPException(status_code=400, detail="eval_data is required")

    results = run_ragas_evaluation(eval_data)
    return results


@app.post("/evaluate-single", response_model=dict)
async def evaluate_single(request: QueryRequest):
    """Evaluate a single query response using DeepEval metrics."""
    qe = state.get_query_engine()
    if qe is None:
        raise HTTPException(status_code=400, detail="No documents indexed. Call /ingest first.")

    response = qe.query(request.question)
    context = [node.text for node in response.source_nodes]

    results = evaluate_single_response(
        question=request.question,
        actual_output=str(response),
        retrieval_context=context,
    )
    return results


@app.post("/audit-report/{collection}", response_model=AuditReportResponse)
async def audit_report(
    collection: str,
    golden_dataset: list[dict] = Body(None),
    improvements: Optional[str] = None,
):
    """Run a real audit: ingest, query golden questions, evaluate.

    If golden_dataset is provided, runs the full pipeline and returns measured metrics.
    Otherwise, returns a manual report (backward-compatible with old query-param API).
    """
    import json

    improvement_list = (
        [i.strip() for i in improvements.split(",")]
        if improvements else []
    )

    if golden_dataset:
        report = run_audit(
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


@app.get("/health")
async def health():
    return {"status": "ok", "indexed": state.get_nodes() is not None}
