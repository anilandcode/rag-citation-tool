# CiteRAG evaluation report — Phase 0/1 bootstrap

**Generated:** 2026-08-22  
**Git base:** `c0ec581` (+ phase 0/1 files)  
**Status:** Scaffold + infrastructure. **Not** a measured RAGAS run.

> Do not treat null metrics as product KPIs. Regenerate with `python scripts/run_full_eval.py` after setting `OPENAI_API_KEY`.

## What shipped (Phase 0 + 1)

| Item | Path |
|------|------|
| Corpus-true golden (17 Qs, 3 refusals) | `tests/eval_datasets/demo_corpus_golden.json` |
| Full eval runner | `scripts/run_full_eval.py` |
| Local demo script | `scripts/demo_local.sh` |
| Job one-pager | `docs/JOB_DEMO.md` |
| Demo checklist | `docs/demo-checklist.md` |
| Unit tests (refusal + golden shape) | `tests/unit/test_refusal_and_golden.py` |
| CLI eval on golden | `src/cli.py` |

## Hosted smoke (2026-08-22)

| Check | Result |
|-------|--------|
| Vercel `/demo` | **200** HTML |
| Vercel `/api/health` → Render | **404 Not Found** |
| Direct `citerag-api.onrender.com/health` | **404 Not Found** |

**Implication:** Public live query path is down until the Render service is fixed or redeployed. **Interview path = local** (`bash scripts/demo_local.sh`).

## Local prerequisites (this machine at build time)

- `.venv` — missing  
- `.env` — missing  
- `pytest` system module — missing  

## RAGAS / pipeline metrics

| Metric | Score |
|--------|------:|
| Faithfulness | n/a |
| Answer relevancy | n/a |
| Context precision | n/a |
| Context recall | n/a |

## Your next 15 minutes (to get a real job pack)

```bash
cd rag-citation-tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-api.txt
pip install -r requirements-eval.txt
cp .env.example .env
# put real OPENAI_API_KEY in .env

# A) interactive demo
bash scripts/demo_local.sh
# open http://127.0.0.1:8080/demo

# B) measured report
python scripts/run_full_eval.py
# open docs/reports/<new-timestamp>_demo-corpus/REPORT.md
# commit that folder
```

Optional Render fix:

1. Render dashboard → ensure web service exists from this repo Dockerfile  
2. Set `OPENAI_API_KEY`, `DEMO_AUTO_SEED=true`, `CORS_ORIGINS=...vercel.app`  
3. Confirm `https://<service>.onrender.com/health` returns JSON  
4. Update `vercel.json` rewrite if hostname changed  

## Golden set summary

Aligned to `data/demo/`:

- refund-policy.md — annual/monthly/enterprise/process  
- terms-2026.md — ownership, age, uptime, liability, last updated  
- pricing.md — Starter/Pro/trial  
- multi-source price+refund  
- 3 refusal traps (phone, password, capital)

## Known limits

- In-memory index  
- Hosted API currently 404  
- Verify step costs LLM calls  
- Sample corpus is synthetic
