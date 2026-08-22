# Evaluation reports

Timestamped packs from `scripts/run_full_eval.py`.

## Latest

See [`latest.json`](./latest.json) for the pointer.

## Layout

```
docs/reports/<YYYY-mm-dd_HHMMSS>_demo-corpus/
  meta.json           # git sha, models, flags, duration
  metrics.json        # RAGAS four metrics (or skipped)
  gates.json          # DeepEval cases (optional)
  pipeline_stats.json # citation/refusal counts
  queries.jsonl       # one line per question
  REPORT.md           # human narrative
```

## Regenerate

```bash
cd rag-citation-tool
source .venv/bin/activate
pip install -r requirements-api.txt
pip install -r requirements-eval.txt   # RAGAS
export OPENAI_API_KEY=...              # or use .env
python scripts/run_full_eval.py
```

## Rules

- **Do not hand-edit** metric numbers in `REPORT.md` or `metrics.json`
- Label any manually written narrative as commentary only
- Sample corpus = `data/demo/` (synthetic). Client audits use their docs + a new folder name
- Commit report packs you want on the public portfolio; keep client data out of git

## Job use

Link from [`JOB_DEMO.md`](../JOB_DEMO.md) and the README.
