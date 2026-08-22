# CiteRAG demo checklist

Last updated: 2026-08-22 (Phase 0/1)

## Local (reliable interview path)

```bash
cd rag-citation-tool
bash scripts/demo_local.sh
# open http://127.0.0.1:8080/demo
```

Manual:

- [ ] `python3 -m venv .venv && source .venv/bin/activate`
- [ ] `pip install -r requirements-api.txt`
- [ ] `.env` has real `OPENAI_API_KEY` (not `sk-...`)
- [ ] `uvicorn src.api.main:app --port 8000`
- [ ] `curl -s localhost:8000/health | jq .` → prefer `"indexed": true`
- [ ] If not indexed: `curl -s -X POST localhost:8000/demo/seed -H "X-API-Key: demo-public-key"`
- [ ] `python3 -m http.server 8080` → open `/demo`
- [ ] Preset refund question returns citations + verification
- [ ] Refusal question (billing phone) shows honest refusal
- [ ] `/app` Settings shows API base; health green

## Full eval + report pack

```bash
source .venv/bin/activate
pip install -r requirements-eval.txt   # for RAGAS
python scripts/run_full_eval.py
# → docs/reports/<timestamp>_demo-corpus/REPORT.md
```

Cheaper smoke (no RAGAS, no claim verify):

```bash
python scripts/run_full_eval.py --skip-ragas --skip-verify --limit 5
```

- [ ] `docs/reports/latest.json` points at newest folder
- [ ] `REPORT.md` metrics not hand-edited

## Production (public link)

- [ ] Render `/health` (may cold-start 30–60s)
- [ ] Vercel rewrite `/api/*` → correct Render host
- [ ] https://rag-citation-tool.vercel.app/demo
- [ ] If cold: use local path above; keep screenshots in latest report

## Interview T-10 SOP

1. Start `bash scripts/demo_local.sh` **or** wake Render health
2. Run refund + refusal once
3. Open `docs/reports/latest` REPORT.md as backup
4. Screen-share `/demo` then report metrics
