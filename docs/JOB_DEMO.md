# CiteRAG — job demo one-pager

**Live:** [Landing](https://rag-citation-tool.vercel.app) · [Demo](https://rag-citation-tool.vercel.app/demo) · [App](https://rag-citation-tool.vercel.app/app)  
**Code:** https://github.com/anilandcode/rag-citation-tool  
**Built by:** [anilpervaiz.com](https://anilpervaiz.com) · hello@anilpervaiz.com

## What it is

Citation-grounded RAG stack: ingest → hybrid retrieve (vector + BM25 + RRF) → optional Cohere rerank → generation with forced `[Source: file, Page X]` → claim verification → refuse when silent → RAGAS / audit reports.

Not a chat wrapper. Not multi-tenant SaaS billing. A **working production path** you can demo and hire for audits/custom installs.

## Reproduce in ~10 minutes (live)

```bash
# 1) API must be healthy on Render
curl -sS https://rag-citation-tool.vercel.app/api/health

# 2) Open demo
open https://rag-citation-tool.vercel.app/demo

# 3) Measured live pack
python scripts/run_live_eval.py
# open docs/reports/<latest>_live/REPORT.md
```

If `/health` is 404, restore Render first (see Hosted API note). Do not use local Docker for job evidence.

## Architecture (modules)

| Step | Module |
|------|--------|
| Ingest + metadata | `src/ingestion/pipeline.py` |
| Hybrid + RRF | `src/retrieval/pipeline.py` |
| Cite / verify / refuse | `src/generation/pipeline.py` |
| RAGAS | `src/evaluation/ragas_harness.py` |
| Audit | `src/evaluation/audit_report.py` |
| HTTP | `src/api/main.py` |

## Demo script (5 min)

1. Landing production table  
2. `/demo`: annual refund → citation + verify  
3. `/demo`: billing phone → honest refusal  
4. Open latest `docs/reports/.../REPORT.md` metrics  
5. Point at GitHub modules  

**Backup if hosted API is cold:** local `demo_local.sh` + report pack screenshots.

## Latest report

See [`docs/reports/latest.json`](./reports/latest.json). Measured packs are `*_live` from:

```bash
python scripts/run_live_eval.py
```

## Hosted API note (2026-08-22)

`citerag-api.onrender.com/health` returned **404**. Live testing is blocked until Render is redeployed with `OPENAI_API_KEY`. Frontend on Vercel stays up; `/demo` cannot query until API is back.

Restore:

1. `render login`
2. Deploy this repo (blueprint `render.yaml` or Docker)
3. Set secrets on the service
4. Confirm health JSON
5. Fix `vercel.json` rewrite if the hostname changed
6. `python scripts/run_live_eval.py`

## Honest limits

- Free Render API can cold-start  
- In-memory index per process  
- Verify step is sequential LLM calls  
- Demo corpus is synthetic sample docs under `data/demo/`

## Offer

| Path | How |
|------|-----|
| Try demo | /demo |
| Accuracy audit | mailto:hello@anilpervaiz.com |
| Custom pipeline | same stack on your docs |
