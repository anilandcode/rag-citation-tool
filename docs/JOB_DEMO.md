# CiteRAG — job demo one-pager

**Live:** [Landing](https://rag-citation-tool.vercel.app) · [Demo](https://rag-citation-tool.vercel.app/demo) · [App](https://rag-citation-tool.vercel.app/app)  
**Code:** https://github.com/anilandcode/rag-citation-tool  
**Built by:** [anilpervaiz.com](https://anilpervaiz.com) · hello@anilpervaiz.com

## What it is

Citation-grounded RAG stack: ingest → hybrid retrieve (vector + BM25 + RRF) → optional Cohere rerank → generation with forced `[Source: file, Page X]` → claim verification → refuse when silent → RAGAS / audit reports.

Not a chat wrapper. Not multi-tenant SaaS billing. A **working production path** you can demo and hire for audits/custom installs.

## Reproduce in ~10 minutes

```bash
git clone https://github.com/anilandcode/rag-citation-tool.git
cd rag-citation-tool
cp .env.example .env   # set OPENAI_API_KEY
bash scripts/demo_local.sh
# open http://127.0.0.1:8080/demo
```

Measured pack:

```bash
source .venv/bin/activate
pip install -r requirements-eval.txt
python scripts/run_full_eval.py
# open docs/reports/<latest>/REPORT.md
```

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

See [`docs/reports/latest.json`](./reports/latest.json). Bootstrap pack documents hosted API status; **measured RAGAS** needs:

```bash
cp .env.example .env   # set OPENAI_API_KEY
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-eval.txt
python scripts/run_full_eval.py
```

## Hosted API note (2026-08-22)

`citerag-api.onrender.com/health` returned **404**. Until Render is restored, demos use **local** `bash scripts/demo_local.sh`. Frontend on Vercel remains up.

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
