# CiteRAG LIVE eval — FAILED (API down)

**When:** 2026-08-22T12:35:59.727489+00:00  
**Base:** `https://rag-citation-tool.vercel.app/api`  
**Health HTTP:** 404  
**Body:** `"Not Found\n"`

## Blocker

Live testing requires a reachable hosted API. This run stopped before queries.

## Fix (hosted only — no local Docker required for *testing*)

1. Log into Render: `render login`
2. Blueprint or Web Service from this repo (`render.yaml` / Dockerfile)
3. Env: `OPENAI_API_KEY`, `DEMO_AUTO_SEED=true`, `DEMO_API_KEY=demo-public-key`,
   `ALLOW_NO_RERANK=true`, `CORS_ORIGINS=https://rag-citation-tool.vercel.app`
4. Confirm: `curl -sS https://<service>.onrender.com/health`
5. If URL ≠ `citerag-api.onrender.com`, update `vercel.json` rewrite and redeploy Vercel
6. Re-run: `python scripts/run_live_eval.py`

Frontend-only smoke (no API): `bash scripts/smoke_hosted.sh`
