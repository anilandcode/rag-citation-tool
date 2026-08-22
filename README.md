# CiteRAG — Citation-Grounded RAG Platform

Production-oriented RAG pipeline with measurable citation accuracy.
Built on LlamaIndex + hybrid search + optional Cohere rerank.

**Live frontend:** [Landing](https://rag-citation-tool.vercel.app) · [Demo](https://rag-citation-tool.vercel.app/demo) · [App](https://rag-citation-tool.vercel.app/app)

---

## Architecture (v0.2)

```
Vercel (static)                     Render / Docker (API)
┌─────────────────────┐             ┌──────────────────────────┐
│ /          landing  │   /api/*    │ FastAPI CiteRAG          │
│ /demo      live UI  │ ─────────►  │ /health /demo/seed       │
│ /app       dashboard│  rewrite    │ /query /ingest           │
│ /assets/config.js   │             │ auto-seed data/demo      │
└─────────────────────┘             └──────────────────────────┘
```

Production UI calls **same-origin `/api`**, proxied by Vercel to the Render service
`https://citerag-api.onrender.com` (see `vercel.json`). Override anytime in App → Settings.

---

## Quick start (local)

```bash
cd rag-citation-tool
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-api.txt
cp .env.example .env
# set OPENAI_API_KEY=...  (COHERE_API_KEY optional)

# API
uvicorn src.api.main:app --reload --port 8000

# Static UI (other terminal)
python3 -m http.server 8080
# open http://localhost:8080/demo
```

Smoke:

```bash
curl -s localhost:8000/health | jq .
curl -s -X POST localhost:8000/demo/seed -H "X-API-Key: demo-public-key" | jq .
curl -s -X POST localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-public-key" \
  -d '{"question":"What is the refund policy for annual subscriptions?"}' | jq .
```

---

## Deploy API (Render)

1. Push this repo to GitHub (`anilandcode/rag-citation-tool`).
2. [Render](https://dashboard.render.com) → **New** → **Blueprint** → select repo (`render.yaml`).
   - Or: New Web Service → Docker → root Dockerfile.
3. Set secrets:
   - `OPENAI_API_KEY` (required)
   - `COHERE_API_KEY` (optional; hybrid works without it)
   - `API_KEY` (optional lock for `/ingest`)
4. After first deploy, confirm:
   - `https://citerag-api.onrender.com/health`
5. If the service name/URL differs from `citerag-api.onrender.com`, update the rewrite in `vercel.json` and redeploy frontend.

CLI (after `render login`):

```bash
render blueprints apply
# or create service manually from Dockerfile
```

---

## Deploy frontend (Vercel)

Already connected. Push to `main` auto-deploys.

```bash
vercel --prod
```

`vercel.json` proxies `/api/*` → Render. CORS on the API also allows the Vercel origin directly.

---

## Surfaces

| Surface | Path | Role |
|---------|------|------|
| Marketing | `/` | Landing |
| Live Demo | `/demo` | 3-pane sample Q&A + verification |
| Dashboard | `/app` | Upload, playground, report, API settings |

---

## API

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/health` | open | `indexed`, `sources`, `chunks` |
| POST | `/demo/seed` | demo key | indexes `data/demo` only |
| POST | `/query` | demo key | answer + citations + verification |
| POST | `/ingest` | API key if set | uploads → `data/uploads` |
| POST | `/evaluate*` | API key | needs `requirements-eval.txt` |
| POST | `/audit-report/{collection}` | API key | measured if golden set provided |

Keys (`X-API-Key` header):

- `DEMO_API_KEY` (default `demo-public-key`) → seed + query
- `API_KEY` (optional) → ingest + eval; if empty, ingest is open (local only)

---

## Demo corpus

Tracked in git under `data/demo/`:

- `refund-policy.md`
- `terms-2026.md`
- `pricing.md`
- `README_DEMO.md` — suggested questions

Boot with `DEMO_AUTO_SEED=true` (default) loads this corpus when OpenAI embeddings are available.

---

## Env vars

See `.env.example`. Important:

| Var | Default | Purpose |
|-----|---------|---------|
| `OPENAI_API_KEY` | — | LLM + embeddings |
| `COHERE_API_KEY` | — | rerank (optional) |
| `CORS_ORIGINS` | localhost + Vercel | browser access |
| `DEMO_API_KEY` | `demo-public-key` | public demo |
| `DEMO_AUTO_SEED` | `true` | seed on startup |
| `ALLOW_NO_RERANK` | `true` | run without Cohere |
| `LLM_MODEL` | `gpt-4o-mini` | cost-friendly demo |

---

## Tests

```bash
python3 -m compileall src/
pytest tests/unit/ -v
# integration smoke (needs deps)
OPENAI_API_KEY=sk-test python3 -c "import src.api.main; print('import ok')"
```

## Job demo + measured reports

- One-pager: [`docs/JOB_DEMO.md`](docs/JOB_DEMO.md)
- **Live eval (canonical):** `python scripts/run_live_eval.py` → `docs/reports/<timestamp>_live/`
- Hosted smoke: `bash scripts/smoke_hosted.sh`
- Golden set: `tests/eval_datasets/demo_corpus_golden.json` (aligned to `data/demo/`)
- Checklist: [`docs/demo-checklist.md`](docs/demo-checklist.md)

Testing policy: **live hosted API only** for acceptance/job packs (no local Docker).

---

## Known limits (v0.1/0.2)

- One in-memory index per process (ingest overwrites)
- Restart loses index unless auto-seed or external store
- Citation verify is sequential LLM calls (latency)
- Starter Render may cold-start (first request slow)
- Full RAGAS/DeepEval needs `pip install -r requirements-eval.txt`

---

## CLI

```bash
python -m src.cli ingest --input-dir ./data/demo
python -m src.cli query "What is the refund policy?" --input-dir ./data/demo
python -m src.cli eval tests/eval_datasets/demo_corpus_golden.json --input-dir ./data/demo
# Prefer live pack for job demos:
python scripts/run_live_eval.py
```
