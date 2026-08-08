# API Reference

Base URL: `http://localhost:8000` (dev) or your deployed URL.

All responses are JSON. Timestamps are ISO 8601 UTC.

---

## Endpoints

### `GET /health`

Returns server health and index status.

**Response** `200`
```json
{
    "status": "ok",
    "indexed": true
}
```

---

### `POST /ingest`

Upload documents and build the retrieval index. Accepts multipart file uploads or reads from `./data/` on disk if no files provided.

**Request** (multipart/form-data)
```
files: [file1.pdf, file2.docx]  (optional)
```

**Response** `200`
```json
{
    "status": "ok",
    "documents_indexed": 3,
    "chunks_created": 42
}
```

**Notes**
- Overwrites the current index. Previous documents are replaced.
- Uploaded filenames are sanitized via `Path(...).name` — directory traversal attempts (`../../etc/x`) are stripped to the base filename only. Only `.pdf`, `.docx`, `.md`, `.txt` extensions are processed.
- Triggers full ingestion pipeline: load → chunk → metadata → index.

**Log Events**: `ingest_complete` (chunks=N)

---

### `POST /query`

Query the RAG pipeline and receive a citation-grounded answer with verification.

**Request** `application/json`
```json
{
    "question": "What is the refund policy for annual subscriptions?",
    "doc_collection": "default"
}
```

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `question` | string | yes | — | The user's question |
| `doc_collection` | string | no | `"default"` | Reserved for multi-collection support (v0.2) |

**Response** `200`
```json
{
    "answer": "Annual subscriptions can be refunded within 30 days. [Source: policy.pdf, Page 2]",
    "citations": [
        {
            "source": "policy.pdf",
            "page": "2",
            "claim": "Annual subscriptions can be refunded within 30 days"
        }
    ],
    "verification": {
        "total_citations": 1,
        "verified": 1,
        "accuracy": 1.0,
        "details": [
            {
                "citation": {
                    "source": "policy.pdf",
                    "page": "2",
                    "claim": "Annual subscriptions can be refunded within 30 days"
                },
                "supported": true,
                "source_text": "Annual subscriptions may be refunded within 30 days of purchase..."
            }
        ]
    }
}
```

**Error** `400`
```json
{
    "detail": "No documents indexed. Call /ingest first."
}
```

**Notes**
- Every query is traced to Langfuse with input, output, and citation metadata.
- Verification uses LLM judge (falls back to substring on network errors).
- `accuracy` = `verified / total_citations`.

**Log Events**: `query_rejected` (reason="no_index"), `query_complete` (question, citations, accuracy)

---

### `POST /evaluate`

Run RAGAS evaluation on a batch of Q&A pairs. Use this for benchmarking or regression testing.

**Request** `application/json`
```json
[
    {
        "question": "What is the refund policy?",
        "ground_truth": "Refunds are available within 30 days.",
        "answer": "Refunds are available within 30 days. [Source: policy.pdf, Page 2]",
        "contexts": ["Refunds are available within 30 days for all products."]
    }
]
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `question` | string | yes | The user's question |
| `ground_truth` | string | yes | Expected correct answer |
| `answer` | string | yes | The actual RAG response |
| `contexts` | list[string] | yes | Retrieved chunks used |

**Response** `200`
```json
{
    "faithfulness": 0.94,
    "answer_relevancy": 0.89,
    "context_precision": 0.87,
    "context_recall": 0.91
}
```

**Notes**
- Uses `GPT-4o-mini` as evaluation judge by default (configurable via `LLM_EVAL_MODEL`).
- Metrics return `0.0` if computation fails (malformed data, missing context).
- Requires `datasets` package (HuggingFace).

---

### `POST /evaluate-single`

Evaluate a single query response using DeepEval's threshold-gated metrics. Designed for CI/CD pipelines.

**Request** `application/json`
```json
{
    "question": "What is the refund policy?",
    "doc_collection": "default"
}
```

**Response** `200`
```json
{
    "faithfulness": 0.92,
    "faithfulness_passed": true,
    "contextual_precision": 0.88,
    "precision_passed": true
}
```

| Field | Type | Notes |
|-------|------|-------|
| `faithfulness` | float | Score 0.0–1.0 |
| `faithfulness_passed` | bool | Whether score ≥ 0.9 threshold |
| `contextual_precision` | float | Score 0.0–1.0 |
| `precision_passed` | bool | Whether score ≥ 0.85 threshold |

**Notes**
- Requires indexed documents (runs `/ingest` first if needed).
- `faithfulness_passed` and `precision_passed` are CI/CD gate signals.

---

### `GET /audit-report/{collection}`

Generate a before/after audit report comparing baseline vs. optimized metrics.

**Query Parameters**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `baseline_faithfulness` | float | `0.0` | Pre-fix faithfulness score |
| `optimized_faithfulness` | float | `0.0` | Post-fix faithfulness score |
| `improvements` | string | — | Comma-separated list of improvements made |
| `sample_questions_json` | string | — | JSON array of `{"question","before_answer","after_answer"}` objects |

**Example Request**
```
GET /audit-report/client_docs?baseline_faithfulness=0.72&optimized_faithfulness=0.94&improvements=Hybrid+search,Cohere+reranking&sample_questions_json=[{"question":"Refund policy?","before_answer":"bad answer","after_answer":"good answer"}]
```

**Response** `200`
```json
{
    "collection": "client_docs",
    "baseline_metrics": {"faithfulness": 0.72},
    "optimized_metrics": {"faithfulness": 0.94},
    "improvements": ["Hybrid search", "Cohere reranking"],
    "sample_questions": [
        {"question": "Refund policy?", "before_answer": "bad answer", "after_answer": "good answer"}
    ],
    "summary": "faithfulness: 0.72 → 0.94 (↑0.22)"
}
```
