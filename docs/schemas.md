# Data Model Reference

All data structures used across the system: Pydantic schemas, dataclasses, and internal representations.

---

## Pydantic Schemas (`src/api/schemas.py`)

These are the API contract types — what gets serialized/deserialized over HTTP.

### QueryRequest

```python
class QueryRequest(BaseModel):
    question: str                          # The user's question
    doc_collection: str = "default"        # Reserved for multi-collection (v0.2)
```

### CitationDetail

```python
class CitationDetail(BaseModel):
    source: str       # Filename of source document, e.g. "policy.pdf"
    page: str         # Page number or label, e.g. "2"
    claim: str        # The sentence the citation annotates
```

### VerificationDetail

```python
class VerificationDetail(BaseModel):
    citation: CitationDetail    # The citation being verified
    supported: bool             # LLM judge verdict
    source_text: str            # First 500 chars of the source chunk
```

### VerificationReport

```python
class VerificationReport(BaseModel):
    total_citations: int                          # Total citations in the response
    verified: int                                 # Citations confirmed by LLM judge
    accuracy: float                               # verified / total_citations
    details: list[VerificationDetail]             # Per-citation breakdown
```

### QueryResponse

```python
class QueryResponse(BaseModel):
    answer: str                                   # The LLM's response with inline citations
    citations: list[CitationDetail]               # Parsed citation objects
    verification: VerificationReport              # Verification results
    evaluation: dict | None = None                # Reserved for per-query RAGAS scores (v0.2)
```

### IngestResponse

```python
class IngestResponse(BaseModel):
    status: str                    # "ok"
    documents_indexed: int         # Count of unique source documents
    chunks_created: int            # Total chunks after semantic splitting
```

### AuditReportResponse

```python
class AuditReportResponse(BaseModel):
    collection: str                              # Collection name
    baseline_metrics: dict                       # Pre-fix metrics, e.g. {"faithfulness": 0.72}
    optimized_metrics: dict                      # Post-fix metrics, e.g. {"faithfulness": 0.94}
    improvements: list[str]                      # List of improvements applied
    sample_questions: list[dict] = []            # Before/after examples
    summary: str                                 # Human-readable delta summary
```

---

## Dataclasses (`src/generation/pipeline.py`)

These are internal types used by the generation and verification pipeline.

### Citation

```python
@dataclass
class Citation:
    source: str       # Extracted from [Source: X, Page Y]
    page: str         # Extracted from [Source: X, Page Y]
    claim: str = ""   # Sentence preceding the citation marker (extracted by _extract_claim_before_marker)
```

### CitationVerification

```python
@dataclass
class CitationVerification:
    citation: Citation           # The citation being verified
    supported: bool              # LLM judge verdict or substring match fallback
    source_text: str = ""        # First 500 chars of the source chunk
```

### CitationVerificationReport

```python
@dataclass
class CitationVerificationReport:
    total_citations: int
    verified: int
    accuracy: float
    details: list[CitationVerification]
```

> **Note**: The dataclass `CitationVerificationReport` is distinct from the Pydantic schema `VerificationReport`. The API layer manually maps between them in the `/query` endpoint. This avoids name collisions while keeping the generation module decoupled from HTTP concerns.

---

## Internal Types

### Settings (`src/config/settings.py`)

```python
class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = ""
    cohere_api_key: str = ""
    pinecone_api_key: str = ""

    # Index config
    pinecone_index_name: str = "rag-citation"

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    # Model selection
    llm_model: str = "gpt-4o"
    llm_eval_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-large"
    rerank_model: str = "rerank-english-v3.0"

    # Tuning
    rerank_top_n: int = 5
    retrieval_top_k: int = 20
```

All settings have env var equivalents (uppercase, e.g. `OPENAI_API_KEY`). See `config/` section in the [Module Reference](modules/README.md#config) for usage cross-reference.

### StructuredRecord (`src/utils/logging.py`)

```python
class StructuredRecord:
    timestamp: float      # Unix timestamp
    iso: str              # ISO 8601 UTC string
    module: str           # Component name, e.g. "ingestion"
    level: str            # DEBUG, INFO, WARNING, ERROR
    event: str            # Machine-readable event name, e.g. "chunking_complete"
    payload: dict         # Arbitrary key-value context
```

### LlamaIndex Objects

The system heavily uses LlamaIndex types for the retrieval pipeline. Key objects:

| Object | Type | Source |
|--------|------|--------|
| `nodes` | `list[TextNode]` | Output of `chunk_documents()` |
| `index` | `VectorStoreIndex` | Output of `build_vector_index()` |
| `retriever` | `QueryFusionRetriever` | Output of `build_hybrid_retriever()` |
| `reranker` | `CohereRerank` | Output of `build_reranker()` |
| `query_engine` | `RetrieverQueryEngine` | Output of `build_query_engine()` |
| `response` | `Response` | Output of `query_engine.query()`. Has `.response` (text) and `.source_nodes` (list[NodeWithScore]) |
