# CiteRAG demo checklist — LIVE only

Last updated: 2026-08-22

**Policy:** All product testing is against **hosted** surfaces. No local Docker / local uvicorn for acceptance.

## Surfaces

| Surface | URL |
|---------|-----|
| Landing | https://rag-citation-tool.vercel.app/ |
| Demo UI | https://rag-citation-tool.vercel.app/demo |
| App | https://rag-citation-tool.vercel.app/app |
| API (via Vercel) | https://rag-citation-tool.vercel.app/api/health |
| API (Render direct) | https://citerag-api.onrender.com/health |

## Preflight

```bash
bash scripts/smoke_hosted.sh
python scripts/run_live_eval.py --limit 3   # short wake + 3 questions
python scripts/run_live_eval.py            # full golden → docs/reports/*_live/
```

## Pass criteria (live)

- [ ] `GET /health` → 200, `"indexed": true` (after seed or auto-seed)
- [ ] `POST /demo/seed` → 200 when cold index
- [ ] Refund question → answer + citations + verification
- [ ] Refusal question (billing phone) → honest refusal
- [ ] `docs/reports/<ts>_live/REPORT.md` committed for job pack
- [ ] Vercel `/demo` loads without console CORS errors

## If API is 404 / down

Testing **cannot** proceed live until Render is restored:

1. `render login`
2. Deploy blueprint (`render.yaml`) or Docker web service from this repo
3. Set `OPENAI_API_KEY` (and optional `COHERE_API_KEY`) in Render dashboard
4. `curl -sS https://<service>.onrender.com/health`
5. Align `vercel.json` rewrite host if URL changed
6. Re-run `python scripts/run_live_eval.py`

Do **not** fall back to local Docker for “official” test reports.

## Interview SOP (live)

1. T-10: `curl` health (wake cold start)
2. Open https://rag-citation-tool.vercel.app/demo
3. Refund + refusal
4. Show latest `docs/reports/*_live/REPORT.md`
