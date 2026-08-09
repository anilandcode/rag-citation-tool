# CiteRAG — Citation-Grounded RAG Platform

Production-ready RAG pipeline with measurable citation accuracy.
Built on LlamaIndex + hybrid search + cross-encoder reranking + RAGAS/DeepEval.

**Live:** [rag-citation-tool.vercel.app](https://rag-citation-tool.vercel.app) · [Live Demo](https://rag-citation-tool.vercel.app/demo) · [Dashboard](https://rag-citation-tool.vercel.app/app)

---

## Quick Start (Full Stack)

### 1. Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY required, COHERE_API_KEY recommended)

# Seed demo corpus and start server
cp data/demo/*.md data/
uvicorn src.api.main:app --reload --port 8000

# Or seed via API
curl -X POST http://localhost:8000/demo/seed -H "X-API-Key: demo-public-key"
```

### 2. Frontend

Point any browser at the Vercel deployment or open `index.html` locally.

```bash
# If running locally, open these in browser:
open http://localhost:8000  # (not an HTTP server — use Vercel or Python's http.server)
python3 -m http.server 8080  # then visit http://localhost:8080
```

### 3. Demo Flow

```bash
# Health check
curl http://localhost:8000/health

# Seed demo documents
curl -X POST http://localhost:8000/demo/seed -H "X-API-Key: demo-public-key"

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-public-key" \
  -d '{"question":"What is the refund policy for annual subscriptions?"}'
```

---

## Surfaces

| Surface | URL | Description |
|---------|-----|-------------|
| **Marketing** | `/` | Landing page with 12 sections, design tokens |
| **Live Demo** | `/demo` | 3-pane UI — ask questions against sample docs, see citations + verification |
| **Dashboard** | `/app` | Corpus upload, playground, audit report, settings |

---

## Architecture

```
ingestion/  → Document loaders, semantic chunking, metadata enrichment
retrieval/  → Hybrid vector+BM25 search, Cohere cross-encoder reranking
generation/ → Citation-grounded prompts, citation extraction + verification
evaluation/ → RAGAS metrics, DeepEval CI/CD gates, audit reports
api/        → FastAPI with CORS, auth, demo seed, 8 endpoints
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | Open | Health check + index status |
| `POST` | `/demo/seed` | Demo key | Ingest `data/demo/` corpus |
| `POST` | `/ingest` | API key | Upload files, build index |
| `POST` | `/query` | Demo key | Citation-grounded answer + verification |
| `POST` | `/evaluate` | API key | RAGAS evaluation batch |
| `POST` | `/evaluate-single` | API key | DeepEval single-response check |
| `POST` | `/audit-report/{collection}` | API key | Audit report generation |

### Auth

- Set `API_KEY` in `.env` to require `X-API-Key` header on all endpoints
- Set `DEMO_API_KEY` for public `/demo/seed` and `/query` access (default: `demo-public-key`)
- Leave both empty for fully open mode

---

## Demo Corpus

Four sample markdown files in `data/demo/`:

| File | Content |
|------|---------|
| `refund-policy.md` | Annual subscription refund within 30 days |
| `terms-2026.md` | Data ownership, acceptable use, liability |
| `pricing.md` | Starter/Professional/Enterprise plans |

See `data/demo/README_DEMO.md` for suggested questions.

---

## Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `OPENAI_API_KEY` | Yes | — | For LLM generation and embeddings |
| `COHERE_API_KEY` | Recommended | — | For cross-encoder reranking |
| `PINECONE_API_KEY` | Optional | — | For persistent vector storage |
| `CORS_ORIGINS` | Optional | `*` | Comma-separated allowed origins |
| `API_KEY` | Optional | — | Required X-API-Key header |
| `DEMO_API_KEY` | Optional | `demo-public-key` | Public demo key |
| `LLM_MODEL` | Optional | `gpt-4o` | Generation model |
| `LLM_EVAL_MODEL` | Optional | `gpt-4o-mini` | Evaluation judge model |

---

## Tests

```bash
# Import smoke test
OPENAI_API_KEY=sk-test python3 tests/integration/test_smoke.py

# Unit tests
pytest tests/unit/ -v

# Compile check
python3 -m compileall src/
```

---

## Known Architecture Limitations (v0.1)

| Limitation | Impact | v0.2 Plan |
|------------|--------|-----------|
| Single global index | One corpus per process; ingest overwrites | Per-collection registry |
| In-memory index lost on restart | Server restart requires re-ingestion | Load-from-store startup |
| No authentication on public demo | `/query` open with demo key | API key rotation, JWT |
| Blocking sync calls in async handlers | Concurrent requests serialize | Threadpool executor |
| Sequential citation verification | Latency scales with citation count | Batched LLM verification |
| Substring source matching | `policy.pdf` matches `old_policy.pdf` | Exact + page disambiguation |
| Manual audit report numbers | Report card shows sample data | Measured `run_audit()` pipeline |
| Refusals not tracked separately | Reported as 0 citations | Dedicated refusal-rate metric |

---

## Deployment

### Vercel (Frontend)
Connected to GitHub. Auto-deploys on push to `main`. Static files served with rewrite rules for SPA routing.

### Backend
FastAPI runs on Railway, Render, Fly.io, or local. Configure `CORS_ORIGINS` to your Vercel domain.

```bash
# Example Render start command
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

---

## CLI Commands

```bash
python -m src.cli ingest --input-dir ./data
python -m src.cli query "What is the refund policy?"
python -m src.cli eval tests/eval_datasets/sample_golden.json
python -m src.cli verify "What are supported file formats?"
```
