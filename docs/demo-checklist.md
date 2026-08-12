# CiteRAG demo checklist

## Local
- [ ] `pip install -r requirements-api.txt`
- [ ] `.env` has `OPENAI_API_KEY`
- [ ] `uvicorn src.api.main:app --port 8000`
- [ ] `curl localhost:8000/health` → `"indexed": true` after seed
- [ ] `python3 -m http.server 8080` → open `/demo`
- [ ] Preset refund question returns citations + verification
- [ ] Refusal question shows Honest refusal badge
- [ ] `/app` Settings shows API base; health green

## Production
- [ ] Render service healthy at `/health`
- [ ] Vercel rewrite `/api/*` points at correct Render host
- [ ] https://rag-citation-tool.vercel.app/demo health dot green
- [ ] Load Sample Docs works (or auto-seed already indexed)
- [ ] Live query returns non-offline answer
- [ ] CORS does not block browser console
