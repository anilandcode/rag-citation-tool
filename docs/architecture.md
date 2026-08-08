# RAG Citation Tool — System Documentation

An AI-native documentation pack for the RAG Citation Tool. Every section below is written for both human developers and AI coding agents to understand the system's architecture, data flow, and extension points.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        API / CLI                              │
│  POST /ingest  POST /query  POST /evaluate  GET /audit-report │
│  CLI: ingest │ query │ eval │ verify                          │
└──────────┬────────────────────────────────────┬───────────────┘
           │                                    │
    ┌──────▼──────┐                    ┌───────▼────────┐
    │  INGESTION  │                    │   GENERATION    │
    │  load docs  │                    │  citation-gnd   │
    │  chunk      │                    │  verify cites   │
    │  metadata   │                    │  refusal logic  │
    └──────┬──────┘                    └───────┬────────┘
           │                                    │
    ┌──────▼───────────────────────────────────▼────────┐
    │                   RETRIEVAL                        │
    │  vector index  +  BM25 keyword  +  rerank          │
    │  (in-memory or Pinecone)                           │
    └──────────────────────┬─────────────────────────────┘
                           │
    ┌──────────────────────▼─────────────────────────────┐
    │                  EVALUATION                         │
    │  RAGAS (faithfulness, precision, recall, relevancy) │
    │  DeepEval (CI/CD quality gates)                     │
    │  Audit Reports (before/after comparisons)            │
    └────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────┐
    │              OBSERVABILITY                          │
    │  Langfuse tracing  +  structured logging            │
    └────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion**: Documents (PDF, DOCX, MD, TXT) are loaded from `./data/`, split via semantic chunking, and enriched with metadata (source, page, section, doc_type, indexed_at). Returns a list of LlamaIndex `Node` objects.

2. **Retrieval**: Nodes are indexed into a vector store (in-memory or Pinecone). Queries are run through a hybrid retriever that merges vector similarity + BM25 keyword results via reciprocal rank fusion, then re-ranked with a Cohere cross-encoder. Top-N chunks surface.

3. **Generation**: Retrieved chunks + user query are passed to an LLM with a citation-enforcing prompt template. The LLM must format citations as `[Source: filename, Page X]` inline. A post-generation verification step parses citations, extracts the preceding claim sentence, and verifies each claim against its source chunk using an LLM judge (with substring fallback on network errors).

4. **Evaluation**: RAGAS computes faithfulness, answer relevancy, context precision, and context recall on evaluation datasets. DeepEval provides threshold-gated quality checks. Audit reports compare baseline vs. optimized metrics for client deliverables.

5. **Observability**: Langfuse captures full trace data per query (input, output, metadata). The structured logger emits module-tagged, timestamped events to stderr in text or JSON format.

### Module Map

| Module | Path | Purpose |
|--------|------|---------|
| **config** | `src/config/` | Settings (env vars + defaults), LLM/embedding model factories |
| **ingestion** | `src/ingestion/` | Document loading, semantic chunking, metadata enrichment |
| **retrieval** | `src/retrieval/` | Vector + BM25 hybrid search, Cohere reranking, Pinecone integration |
| **generation** | `src/generation/` | Citation-grounded prompt, citation extraction, claim verification |
| **evaluation** | `src/evaluation/` | RAGAS metrics, DeepEval gates, audit report generation |
| **api** | `src/api/` | FastAPI endpoints, Pydantic schemas, module-level state |
| **utils** | `src/utils/` | Langfuse tracer, structured logger |
| **cli** | `src/cli.py` | Argparse CLI for ingest/query/eval/verify |
| **tests** | `tests/` | Unit tests, golden evaluation datasets |

### Key Design Decisions

- **LlamaIndex for retrieval** (not LangChain) — higher accuracy on document-heavy workloads (~92% vs ~85%), especially with table-rich PDFs
- **Hybrid search is non-negotiable** — pure vector search fails on exact identifiers (product codes, error numbers, policy references); BM25 compensates
- **Citation verification is the differentiator** — every claim is checked against its source chunk, not just formatted as a citation
- **Evaluation is sold, not hidden** — RAGAS scores are part of the client-facing audit report, proving improvement with numbers
- **Two index backends** — in-memory for dev/demo, Pinecone for production persistence
- **Logging is structured** — designed for both human debugging and machine parsing
