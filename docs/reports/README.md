# Evaluation reports

Timestamped packs from **live** eval (`scripts/run_live_eval.py`).

## Latest

See [`latest.json`](./latest.json).

## Layout

```
docs/reports/<YYYY-mm-dd_HHMMSS>_live/
  meta.json           # API base, health, git sha, duration
  metrics.json        # live verify accuracy, pass rates
  pipeline_stats.json
  queries.jsonl       # one line per live /query
  REPORT.md
```

Bootstrap / offline scaffolds may exist historically; **job-facing packs must be `*_live`**.

## Regenerate (hosted only)

```bash
# API must be up (Render)
bash scripts/smoke_hosted.sh
python scripts/run_live_eval.py
```

Env overrides:

- `CITERAG_API_BASE` — default `https://rag-citation-tool.vercel.app/api`
- `DEMO_API_KEY` — default `demo-public-key`

## Rules

- Official metrics come from **live** `/query` (+ optional hosted `/evaluate`)
- Do not hand-edit numbers
- No local Docker runs as acceptance evidence
