# Module Reference

Deep-dive documentation for each module: data structures, function signatures, internal flow, edge cases, and extension points.

---

## Ingestion (`src/ingestion/pipeline.py`)

**Purpose**: Load documents from disk, split into chunks, and enrich with metadata.

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| `load_documents()` | Function | Reads files from `input_dir` using `SimpleDirectoryReader`. Supports PDF, DOCX, MD, TXT. |
| `chunk_documents()` | Function | Splits documents into nodes using `SemanticSplitterNodeParser` (buffer_size=1, breakpoint_percentile=95). Enriches each node with metadata. |
| `run_ingestion()` | Function | Orchestrator: load → chunk → return nodes. Raises `ValueError` if no documents found. |
| `extract_section_header()` | Helper | Scans chunk text for markdown headings or ALL-CAPS lines. |
| `classify_document_type()` | Helper | Extracts file extension from metadata `file_name`. |

### Metadata Enrichment (per chunk)

```json
{
    "source": "policy.pdf",
    "page": "3",
    "section": "Refund Procedures",
    "doc_type": "pdf",
    "indexed_at": "2026-08-06T14:22:00.000Z"
}
```

### Log Events

| Event | Level | Payload |
|-------|-------|---------|
| `loading_documents` | INFO | `input_dir`, `extensions` |
| `documents_loaded` | INFO | `count` |
| `chunking_start` | INFO | `document_count` |
| `chunking_complete` | INFO | `chunk_count` |
| `ingestion_start` | INFO | `input_dir` |
| `ingestion_failed` | ERROR | `reason`, `input_dir` |
| `ingestion_complete` | INFO | `document_count`, `chunk_count` |

### Extension Points

- Add `PdfReader` for structure-aware PDF parsing (tables, headers)
- Add `file_name` → document type classifier for richer `doc_type` values
- Add chunk deduplication (hash-based) for overlapping documents

---

## Retrieval (`src/retrieval/pipeline.py`)

**Purpose**: Build indices, execute hybrid vector+keyword search, and rerank results.

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| `build_vector_index()` | Function | Creates `VectorStoreIndex`. Supports in-memory and Pinecone backends. |
| `build_vector_retriever()` | Function | Wraps index with `similarity_top_k=20` retriever. |
| `build_bm25_retriever()` | Function | Creates BM25 keyword retriever from raw nodes. |
| `build_hybrid_retriever()` | Function | Fuses vector + BM25 via `QueryFusionRetriever` with reciprocal rank fusion. |
| `build_reranker()` | Function | Creates `CohereRerank` postprocessor (model: `rerank-english-v3.0`, reranks to top 5). |
| `build_full_retrieval_pipeline()` | Orchestrator | Builds all components and returns `(index, hybrid_retriever, reranker)`. |

### Search Flow

```
User Query
    │
    ▼
┌──────────────────┐    ┌──────────────────┐
│ Vector Retriever │    │  BM25 Retriever   │
│ (top_k=20)       │    │  (top_k=20)       │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌──────────────────────┐
         │  QueryFusionRetriever│
         │  reciprocal_rerank   │
         │  top_k=20            │
         └──────────┬───────────┘
                     ▼
         ┌──────────────────────┐
         │  CohereRerank        │
         │  model: rerank-v3    │
         │  top_n=5             │
         └──────────┬───────────┘
                     ▼
               Final Chunks → LLM
```

### Pinecone Integration

Set `use_pinecone=True` on `build_vector_index()` or `build_full_retrieval_pipeline()`. Requires `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` env vars. The Pinecone client and index are created lazily inside `_create_pinecone_store()`.

### Log Events

| Event | Level | Payload |
|-------|-------|---------|
| `building_index` | INFO | `node_count`, `backend` |
| `index_ready` | INFO | `top_k`, `rerank_top_n` |

### Extension Points

- Add Weaviate backend (native hybrid search, no separate BM25 needed)
- Add query expansion (generate multiple query variants, fuse results)
- Add time-decay or recency boosting for date-sensitive documents

---

## Generation (`src/generation/pipeline.py`)

**Purpose**: Generate citation-grounded answers and verify each citation against source chunks.

### Data Structures

```python
@dataclass
class Citation:
    source: str          # e.g. "policy.pdf"
    page: str            # e.g. "2"
    claim: str           # extracted sentence preceding the citation marker

@dataclass
class CitationVerification:
    citation: Citation
    supported: bool      # LLM judge verdict
    source_text: str     # first 500 chars of source chunk

@dataclass
class CitationVerificationReport:
    total_citations: int
    verified: int
    accuracy: float      # verified / total
    details: list[CitationVerification]
```

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| `build_query_engine()` | Function | Creates `RetrieverQueryEngine` with citation-enforcing prompt template. |
| `extract_citations()` | Function | Regex-parses `[Source: X, Page Y]` from response text. Extracts preceding claim sentence. |
| `verify_citations()` | Function | For each citation, finds source node by metadata, asks LLM judge "Is the claim supported?", returns `CitationVerificationReport`. |
| `find_node_by_metadata()` | Helper | Searches source_nodes for a match on `source` or `file_name` metadata. |
| `_extract_claim_before_marker()` | Helper | Walks backwards from citation bracket to find sentence boundary. Skips over prior `[Source: ...]` blocks. Requires whitespace after `.`, `!`, `?` for sentence breaks. |
| `source_name_in_text()` | Fallback | Substring match when LLM verification is unavailable. |

### Citation Prompt Template

The LLM receives context chunks + question with these rules:
1. Every factual claim MUST cite `[Source: filename, Page X]`
2. If context doesn't contain the answer, say "I don't have enough information to answer this"
3. Don't make up information or cite sources not provided
4. Place citations immediately after the supported claim

### Verification Flow

```
LLM Response: "Refunds available within 30 days. [Source: policy.pdf, Page 2]"
                                       │
                                       ▼
                           extract_citations()
                           ┌─────────────────────────┐
                           │ source: "policy.pdf"    │
                           │ page: "2"               │
                           │ claim: "Refunds ..."    │
                           └──────────┬──────────────┘
                                      │
                               find_node_by_metadata()
                                      │
                              ┌───────▼───────┐
                              │  Found node?  │
                              └───┬───────┬───┘
                             Yes  │       │  No → unsupported
                                  ▼       │
                          LLM judge      │
                          "Is claim      │
                          supported?"    │
                          ┌─────┴─────┐  │
                          │ Yes │ No  │  │
                          └──┬──┴──┬──┘  │
                             │     │     │
                          supported  unsupported
```

### Error Handling

- Network errors (`ConnectionError`, `TimeoutError`, `OSError`) → fall back to substring match, log warning
- Other exceptions → log warning with citation details, fall back to substring match
- Source node not found → log warning, mark unsupported

### Log Events

| Event | Level | Payload |
|-------|-------|---------|
| `verification_start` | INFO | `citation_count` |
| `verification_skip` | INFO | `reason="no_citations_found"` |
| `verification_network_fallback` | WARNING | `source`, `error` |
| `verification_llm_failed` | WARNING | `source`, `claim`, `error` |
| `source_node_missing` | WARNING | `source` |
| `verification_complete` | INFO | `total_citations`, `verified`, `accuracy` |

### Extension Points

- Add NLI (natural language inference) model for faster verification (no LLM call)
- Add span-level citation extraction (cite specific sentences, not whole page)
- Add citation format flexibility (handle `[1]`, `(Author, 2024)` styles)

---

## Evaluation (`src/evaluation/`)

**Purpose**: Measure RAG quality, enforce CI/CD gates, and generate client-facing reports.

### Modules

| File | Purpose |
|------|---------|
| `ragas_harness.py` | Runs RAGAS metrics (faithfulness, answer relevancy, context precision, context recall) on evaluation datasets |
| `deepeval_harness.py` | Evaluates single responses with threshold-gated metrics for CI/CD |
| `audit_report.py` | Generates before/after comparison reports for client deliverables |

### RAGAS Metrics

| Metric | What It Measures | Use |
|--------|-----------------|-----|
| `faithfulness` | Is the answer supported by retrieved context? | Primary citation quality signal |
| `answer_relevancy` | Does the answer address the question? | Generative quality |
| `context_precision` | Are retrieved chunks relevant? | Retrieval quality |
| `context_recall` | Did we retrieve all needed chunks? | Coverage |

### DeepEval Metrics

| Metric | Threshold | Use |
|--------|-----------|-----|
| `FaithfulnessMetric` | 0.9 (default) | CI/CD gate — block deploy if faithfulness drops |
| `ContextualPrecisionMetric` | 0.85 (default) | CI/CD gate — block deploy if retrieval degrades |

### Audit Report Structure

```python
{
    "collection": "client_docs",
    "baseline_metrics": {"faithfulness": 0.72, "citation_accuracy": 0.65},
    "optimized_metrics": {"faithfulness": 0.94, "citation_accuracy": 0.91},
    "improvements": ["Added hybrid search", "Added Cohere reranking"],
    "sample_questions": [
        {"question": "What is the refund policy?", "before_answer": "...", "after_answer": "..."}
    ],
    "summary": "faithfulness: 0.72 → 0.94 (↑0.22)\ncitation_accuracy: 0.65 → 0.91 (↑0.26)"
}
```

### Log Events

None currently — evaluation runs are driven by HTTP requests or CLI commands. Audit report generation is pure data transformation.

### Extension Points

- Add per-metric trend tracking across evaluation runs
- Add automatic regression detection (alert if faithfulness drops below threshold)
- Generate PDF audit reports for client delivery

---

## API (`src/api/`)

See [API Reference](api.md) for full endpoint documentation.

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application with 6 endpoints, lifespan context manager |
| `schemas.py` | Pydantic models for all request/response types |
| `state.py` | Module-level singleton state (nodes, query engine, retrievers, reranker) |

### Design Note

The API uses module-level state (`src/api/state.py`) rather than dependency injection or a database. This means:
- Single-tenancy: one document set at a time
- State persists across requests within the process lifetime
- Ingest replaces state entirely (new documents overwrite old)
- Stateless by restart — restarting the server clears the index

---

## Utils (`src/utils/`)

| File | Purpose |
|------|---------|
| `logging.py` | Structured logger with text and JSON output modes |
| `langfuse_tracer.py` | Langfuse integration for trace-level observability |

See [Logging Reference](logging.md) for full documentation.

---

## CLI (`src/cli.py`)

**Purpose**: Command-line interface for development, debugging, and scripting.

### Commands

```bash
python -m src.cli ingest --input-dir ./data
python -m src.cli query "What is the refund policy?"
python -m src.cli eval tests/eval_datasets/sample_golden.json
python -m src.cli verify "What are supported file formats?"
```

### Design Note

The CLI re-ingests on every query (no persistence between invocations). This is intentional for development — it guarantees a fresh index from current disk state. In production, use the API server instead, which maintains state across requests.

---

## Config (`src/config/`)

| File | Purpose |
|------|---------|
| `settings.py` | `BaseSettings` class from `pydantic_settings`. Reads from env vars / `.env` file. All settings have defaults except API keys. |
| `models.py` | Factory functions for LLM, eval LLM, and embedding model instances. |

### Settings Reference

| Setting | Default | Env Var | Used By |
|---------|---------|---------|---------|
| `openai_api_key` | `""` | `OPENAI_API_KEY` | `get_llm()`, `get_eval_llm()`, `get_embed_model()` |
| `cohere_api_key` | `""` | `COHERE_API_KEY` | `build_reranker()` |
| `pinecone_api_key` | `""` | `PINECONE_API_KEY` | `_create_pinecone_store()` |
| `pinecone_index_name` | `"rag-citation"` | `PINECONE_INDEX_NAME` | `_create_pinecone_store()` |
| `langfuse_public_key` | `""` | `LANGFUSE_PUBLIC_KEY` | `get_langfuse()` |
| `langfuse_secret_key` | `""` | `LANGFUSE_SECRET_KEY` | `get_langfuse()` |
| `langfuse_host` | `"http://localhost:3000"` | `LANGFUSE_HOST` | `get_langfuse()` |
| `llm_model` | `"gpt-4o"` | `LLM_MODEL` | `get_llm()` |
| `llm_eval_model` | `"gpt-4o-mini"` | `LLM_EVAL_MODEL` | `get_eval_llm()` |
| `embedding_model` | `"text-embedding-3-large"` | `EMBEDDING_MODEL` | `get_embed_model()` |
| `rerank_model` | `"rerank-english-v3.0"` | `RERANK_MODEL` | `build_reranker()` |
| `rerank_top_n` | `5` | `RERANK_TOP_N` | `build_reranker()` |
| `retrieval_top_k` | `20` | `RETRIEVAL_TOP_K` | `build_vector_retriever()`, `build_bm25_retriever()`, `build_hybrid_retriever()` |
