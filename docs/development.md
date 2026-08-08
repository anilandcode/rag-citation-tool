# Development Guide

Setup, conventions, testing, and extension patterns for the RAG Citation Tool.

---

## Getting Started

### Prerequisites

- Python 3.11+
- API keys: OpenAI, Cohere, Pinecone, Langfuse (all optional for dev — in-memory index works without Pinecone)

### Setup

```bash
cd rag-citation-tool

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Development Server

```bash
# Start API server with hot reload
uvicorn src.api.main:app --reload --port 8000

# Or use the npm scripts
npm run dev
```

### CLI Usage

```bash
# Ingest documents from ./data/
python -m src.cli ingest --input-dir ./data

# Query
python -m src.cli query "What is the refund policy?"

# Evaluate on golden dataset
python -m src.cli eval tests/eval_datasets/sample_golden.json

# Verify citations
python -m src.cli verify "What are supported file formats?"
```

### Running Tests

```bash
pytest tests/unit/ -v
```

### Smoke Test (Catch Import Errors Before They Ship)

This one-liner validates that every core module imports cleanly and the API app object is reachable. Run it after any structural change:

```bash
python3 -c "
import os; os.environ.update({'OPENAI_API_KEY':'sk-test','COHERE_API_KEY':'test','PINECONE_API_KEY':'test'})
from src.api.main import app
from src.ingestion.pipeline import run_ingestion
from src.retrieval.pipeline import build_full_retrieval_pipeline
from src.generation.pipeline import build_query_engine, extract_citations, verify_citations
from src.evaluation.ragas_harness import run_ragas_evaluation
from src.evaluation.deepeval_harness import evaluate_single_response
from src.evaluation.audit_report import generate_audit_report
from src.utils.logging import get_logger
from src.utils.langfuse_tracer import get_langfuse
print('All modules imported successfully')
"
```

If this prints `All modules imported successfully`, every import chain, `NameError`, and module-level syntax issue is clean. If it fails, the stack trace tells you exactly which module and line. This test would have caught all four fatal bugs from the 2026-08-06 evaluation.

---

## Project Conventions

### Code Style

- Follow PEP 8 with 4-space indentation
- Module-level docstrings describe the module's purpose
- Function docstrings describe behavior, not implementation
- Use type hints on public function signatures
- Internal helpers prefixed with `_` (e.g., `_extract_claim_before_marker`)
- Dataclasses for internal data transport, Pydantic for API boundaries

### Import Order

1. Standard library
2. Third-party packages (llama_index, fastapi, etc.)
3. Internal modules (`src.*`)

Within each group, sort alphabetically.

### Naming

| Thing | Convention | Example |
|-------|-----------|---------|
| Modules | `snake_case` | `ragas_harness.py` |
| Classes | `PascalCase` | `CitationVerificationReport` |
| Functions | `snake_case` | `build_query_engine` |
| Variables | `snake_case` | `verified_count` |
| Constants | `UPPER_SNAKE` | `CITATION_PROMPT` |
| Log events | `snake_case` | `documents_loaded` |

### Logging

Every module imports its own logger:
```python
from src.utils.logging import get_logger
log = get_logger("module_name")
```

Log at entry/exit points of major functions with key parameters and results. Log warnings for known degradation paths (fallbacks, missing data). Log errors only for failure states.

See [Logging Reference](logging.md) for the complete event catalog.

---

## Adding a New Feature

### 1. Extend Configuration

Add new settings to `src/config/settings.py`:
```python
class Settings(BaseSettings):
    my_new_setting: str = "default_value"
```

Add the env var to `.env.example`.

### 2. Add New Module

Create `src/my_feature/pipeline.py`:
```python
"""My new feature module."""

from src.utils.logging import get_logger

log = get_logger("my_feature")

def my_function():
    log.info("my_function_start")
    # ...
    log.info("my_function_complete")
```

### 3. Wire to API

Add a new endpoint in `src/api/main.py`:
```python
@app.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    result = my_function()
    return result
```

### 4. Add Tests

Create `tests/unit/test_my_feature.py`:
```python
def test_my_function():
    result = my_function()
    assert result is not None
```

### 5. Add Documentation

- Update `docs/modules/README.md` with a new section
- If it has an API surface, update `docs/api.md`
- If it emits new log events, update `docs/logging.md`

---

## Testing Strategy

- **Unit tests**: `tests/unit/` — Pure function tests. No network, no LLM calls. Test logic and data transformations.
- **Golden datasets**: `tests/eval_datasets/` — JSON files with question/answer/context pairs for RAGAS evaluation. Add client-specific datasets here.
- **API smoke tests**: Run the dev server and curl `/health`, `/ingest`, `/query`.

### Running a Full Regression

```bash
# 1. Start fresh
rm -rf data/

# 2. Add test documents
cp tests/eval_datasets/sample_docs/*.txt data/

# 3. Ingest + build index
python -m src.cli ingest --input-dir ./data

# 4. Run evaluation
python -m src.cli eval tests/eval_datasets/sample_golden.json

# 5. Verify a query
python -m src.cli verify "What is the refund policy?"

# 6. Run unit tests
pytest tests/unit/ -v
```

---

## Docker

### Build and Run

```bash
docker compose build
docker compose up -d
```

This starts:
- `app` on port 8000 (API)
- `langfuse` on port 3000 (observability UI)
- `langfuse-db` (PostgreSQL 16)

### Development with Docker

Mount your local source for hot reload:
```yaml
# docker-compose.override.yml (create locally)
services:
  app:
    volumes:
      - ./src:/app/src
    command: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### Server won't start: `NameError` or `ImportError`

Run the smoke test above. If it fails, check that all four core modules define their logger:

```python
# Every module that uses log.info/log.warning/log.error MUST have:
from src.utils.logging import get_logger
log = get_logger("module_name")
```

The modules that need this: `api/main.py` (`"api"`), `retrieval/pipeline.py` (`"retrieval"`), `generation/pipeline.py` (`"generation"`), `ingestion/pipeline.py` (`"ingestion"`).

### `/query` returns 400 "No documents indexed"

This is normal on first run. Call `POST /ingest` first. If the server restarted, the in-memory index was cleared — re-ingest.

### Citation verification always returns 0% accuracy

Check that your documents have `source` metadata populated (ingestion does this automatically). If using the Pinecone backend, ensure the index name matches `PINECONE_INDEX_NAME`. Verify the LLM judge (`LLM_EVAL_MODEL`) has network access.

### Langfuse traces not appearing

Check `LANGFUSE_HOST` — if running outside Docker, use `http://localhost:3000`. Inside Docker, use `http://langfuse:3000`. Langfuse in dev mode works without API keys set (they can be empty strings).

### "No module named 'pinecone'" on import

The Pinecone client is imported lazily only when `use_pinecone=True`. If you see this error, you're running in Pinecone mode without the dependency. Either install `pip install pinecone-client` or use the default in-memory backend.

### asyncpg / psycopg2 errors in Docker

These are from the Langfuse container, not the app. The `langfuse-db` service needs a few seconds to become healthy on first start. If Langfuse crashes, `docker compose restart langfuse` usually fixes it after the DB is ready.

---

## Known Architecture Limitations (v0.1)

These are intentional tradeoffs for the initial release. They are documented so you don't debug them as bugs.

| Limitation | Impact | Fix in v0.2 |
|------------|--------|-------------|
| **Single-tenancy** | One document set per process. A second `/ingest` overwrites the first. | Per-collection registry (keyed by `doc_collection`) |
| **In-memory index lost on restart** | Server restart requires re-ingestion. Pinecone mode persists vectors but not BM25. | Load-from-store startup path; persist BM25 nodes |
| **No authentication** | `/ingest`, `/query`, `/audit-report` are open endpoints | API-key / JWT auth via FastAPI `Depends` |
| **Blocking sync calls in async handlers** | CPU/IO-heavy operations block the event loop; concurrent requests serialize | Threadpool executor or background task queue |
| **Sequential citation verification** | One LLM call per citation; latency scales linearly with citation count | Batch-verify all citations in a single LLM call |
| **Substring source matching** | `policy.pdf` matches `old_policy.pdf` in `find_node_by_metadata()` | Exact filename matching with page disambiguation |
| **Manual audit report numbers** | `/audit-report` takes metrics as query params, doesn't measure them | `run_audit()` pipeline that executes baseline vs optimized |
| **No refusals tracking** | Correct refusals (0 citations) are reported as `accuracy: 0.0` | Separate refusal-rate metric; exclude refusals from accuracy denominator |
| **Citation parser misses variants** | Only matches the literal `[Source: X, Page Y]` format | Broader regex for `p.`, `pg`, `Section`, page-optional formats |
| **Unpinned dependencies** | `>=` floors in requirements.txt; a fresh install may resolve to breaking versions | Pin exact tested versions; add lockfile; CI import smoke test |

- Semantic chunking is CPU-bound but runs once per ingestion
- Embedding generation is network-bound (OpenAI API)
- Query latency: ~1-2s (2 API calls — embedding + generation)
- Verification adds ~0.5-1s per citation (LLM judge call)
- In-memory index: all chunks in RAM (works for ~10K chunks, ~50MB)
- Pinecone: scales to millions of chunks

---

## Directory Reference

```
rag-citation-tool/
├── src/
│   ├── api/              # FastAPI app, schemas, state
│   ├── cli.py            # CLI entry point
│   ├── config/           # Settings, model factories
│   ├── evaluation/       # RAGAS, DeepEval, audit reports
│   ├── generation/       # Citation-grounded prompts, verification
│   ├── ingestion/        # Document loading, chunking, metadata
│   ├── retrieval/        # Hybrid search, reranking, Pinecone
│   └── utils/            # Logging, Langfuse tracing
├── tests/
│   ├── eval_datasets/    # Golden Q&A JSON files
│   └── unit/             # Python unit tests
├── docs/                 # This documentation
├── data/                 # Ingested documents (gitignored)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```
