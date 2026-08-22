#!/usr/bin/env python3
"""Live CiteRAG eval — hits hosted API only (no local uvicorn/docker).

Default base: https://rag-citation-tool.vercel.app/api  (Vercel rewrite → Render)
Override:  CITERAG_API_BASE=https://your-service.onrender.com

Usage:
  python scripts/run_live_eval.py
  python scripts/run_live_eval.py --limit 5
  python scripts/run_live_eval.py --base https://citerag-api.onrender.com
  python scripts/run_live_eval.py --skip-seed

Writes docs/reports/<timestamp>_live/
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = os.environ.get(
    "CITERAG_API_BASE", "https://rag-citation-tool.vercel.app/api"
).rstrip("/")
DEFAULT_KEY = os.environ.get("DEMO_API_KEY", "demo-public-key")
GOLDEN = ROOT / "tests/eval_datasets/demo_corpus_golden.json"


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=ROOT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def http_json(
    method: str,
    url: str,
    body: dict | list | None = None,
    api_key: str = DEFAULT_KEY,
    timeout: float = 180.0,
) -> tuple[int, dict | list | str]:
    data = None
    headers = {
        "Accept": "application/json",
        "X-API-Key": api_key,
        "User-Agent": "citerag-live-eval/1.0",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = resp.getcode()
            try:
                return code, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return code, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {"detail": str(e)}
        except json.JSONDecodeError:
            payload = raw or str(e)
        return e.code, payload
    except Exception as e:
        return 0, {"error": str(e)}


def detect_refusal(text: str) -> bool:
    t = (text or "").lower()
    needles = [
        "don't have enough information",
        "do not have enough information",
        "cannot answer",
        "unable to answer",
        "not enough context",
        "no information available",
        "does not contain",
        "not found in the provided",
        "not mentioned in the",
    ]
    return any(n in t for n in needles)


def main() -> int:
    ap = argparse.ArgumentParser(description="Live CiteRAG eval (hosted API only)")
    ap.add_argument("--base", default=DEFAULT_BASE, help="API base URL")
    ap.add_argument("--key", default=DEFAULT_KEY, help="X-API-Key (demo key)")
    ap.add_argument("--golden", default=str(GOLDEN))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-seed", action="store_true")
    ap.add_argument(
        "--wake-seconds",
        type=int,
        default=120,
        help="Max seconds to wait for cold start on /health",
    )
    args = ap.parse_args()
    base = args.base.rstrip("/")

    items = json.loads(Path(args.golden).read_text())
    if args.limit > 0:
        items = items[: args.limit]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    out_dir = ROOT / "docs" / "reports" / f"{ts}_live"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Live base: {base}")
    t0 = time.time()

    # Wake / health
    health = None
    health_code = 0
    deadline = time.time() + max(args.wake_seconds, 5)
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        health_code, health = http_json("GET", f"{base}/health", timeout=60)
        print(f"  health try {attempt}: HTTP {health_code} -> {health!r}"[:200])
        if health_code == 200 and isinstance(health, dict):
            break
        if health_code in (404, 401, 403):
            break  # won't recover by waiting
        time.sleep(5)

    if health_code != 200:
        meta = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "git_sha": _git_sha(),
            "mode": "live",
            "base": base,
            "status": "api_unreachable",
            "health_http": health_code,
            "health": health,
            "duration_sec": round(time.time() - t0, 2),
            "fix": (
                "Hosted API did not return 200 /health. "
                "Redeploy Render (render.yaml name citerag-api), set OPENAI_API_KEY, "
                "confirm public URL, update vercel.json rewrite if hostname changed."
            ),
        }
        (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        (out_dir / "metrics.json").write_text(
            json.dumps(
                {
                    "skipped": True,
                    "reason": f"api_unreachable HTTP {health_code}",
                },
                indent=2,
            )
            + "\n"
        )
        report = f"""# CiteRAG LIVE eval — FAILED (API down)

**When:** {meta['timestamp']}  
**Base:** `{base}`  
**Health HTTP:** {health_code}  
**Body:** `{json.dumps(health)[:500]}`

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
"""
        (out_dir / "REPORT.md").write_text(report)
        pointer = {
            "latest": out_dir.name,
            "path": f"docs/reports/{out_dir.name}",
            "timestamp": meta["timestamp"],
            "status": "api_unreachable",
        }
        (ROOT / "docs" / "reports" / "latest.json").write_text(
            json.dumps(pointer, indent=2) + "\n"
        )
        print(f"Wrote failure pack: {out_dir}")
        return 2

    # Seed
    seed_result = None
    if not args.skip_seed:
        print("POST /demo/seed ...")
        sc, seed_result = http_json(
            "POST", f"{base}/demo/seed", body={}, timeout=300
        )
        print(f"  seed HTTP {sc}: {seed_result!r}"[:240])
        if sc not in (200, 201):
            # retry health after seed fail
            print("Seed failed; continuing if already indexed...")
        time.sleep(1)
        _, health = http_json("GET", f"{base}/health", timeout=60)

    indexed = isinstance(health, dict) and health.get("indexed")
    if not indexed:
        meta = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "git_sha": _git_sha(),
            "mode": "live",
            "base": base,
            "status": "not_indexed",
            "health": health,
            "seed": seed_result,
        }
        (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        (out_dir / "REPORT.md").write_text(
            f"# LIVE eval — index empty\n\nhealth={health}\nseed={seed_result}\n"
        )
        print("ERROR: API up but not indexed after seed")
        return 3

    # Query golden
    rows = []
    n_ok = 0
    n_cite = 0
    n_refuse_ok = 0
    n_refuse_fail = 0
    queries_path = out_dir / "queries.jsonl"

    with queries_path.open("w") as qf:
        for i, item in enumerate(items, 1):
            qid = item.get("id", f"q{i}")
            question = item["question"]
            expect_refusal = bool(item.get("expect_refusal", False))
            print(f"[{i}/{len(items)}] {qid}")
            code, payload = http_json(
                "POST",
                f"{base}/query",
                body={"question": question},
                timeout=180,
            )
            answer = ""
            citations = []
            verification = None
            err = None
            if code != 200:
                err = payload
            elif isinstance(payload, dict):
                answer = payload.get("answer") or ""
                citations = payload.get("citations") or []
                verification = payload.get("verification")
                n_ok += 1
            else:
                err = payload

            is_refusal = detect_refusal(answer)
            if citations:
                n_cite += 1
            if expect_refusal:
                if is_refusal:
                    n_refuse_ok += 1
                else:
                    n_refuse_fail += 1

            row = {
                "id": qid,
                "question": question,
                "expect_refusal": expect_refusal,
                "expected_sources": item.get("expected_sources") or [],
                "http": code,
                "answer": answer,
                "citations": citations,
                "verification": verification,
                "is_refusal": is_refusal,
                "error": err,
                "category": item.get("category"),
            }
            qf.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows.append(row)
            time.sleep(0.3)  # gentle on free tier

    duration = round(time.time() - t0, 2)
    stats = {
        "n_questions": len(items),
        "n_http_200": n_ok,
        "n_with_citations": n_cite,
        "n_refusal_expected_ok": n_refuse_ok,
        "n_refusal_expected_fail": n_refuse_fail,
    }
    # Live path does not run RAGAS client-side (needs eval deps + answers/contexts).
    # Citation verify accuracy comes from API verification object when present.
    ver_vals = []
    for r in rows:
        v = r.get("verification") or {}
        if isinstance(v, dict) and v.get("accuracy") is not None:
            try:
                ver_vals.append(float(v["accuracy"]))
            except (TypeError, ValueError):
                pass
    metrics = {
        "mode": "live_api",
        "mean_verify_accuracy": round(sum(ver_vals) / len(ver_vals), 4)
        if ver_vals
        else None,
        "verify_n": len(ver_vals),
        "ragas": {
            "skipped": True,
            "reason": (
                "RAGAS runs on API via POST /evaluate when requirements-eval "
                "installed on host + API_KEY. This live pack uses /query verification."
            ),
        },
        "pass_rate_http": round(n_ok / len(items), 4) if items else 0,
        "refusal_recall": round(n_refuse_ok / max(1, n_refuse_ok + n_refuse_fail), 4),
    }

    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "mode": "live",
        "base": base,
        "status": "ok",
        "health": health,
        "seed": seed_result,
        "n_questions": len(items),
        "duration_sec": duration,
        "golden": os.path.relpath(args.golden, ROOT),
        "command": f"python scripts/run_live_eval.py --base {base}",
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (out_dir / "pipeline_stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    (out_dir / "gates.json").write_text(
        json.dumps({"skipped": True, "reason": "live pack uses API verification"}, indent=2)
        + "\n"
    )

    samples = []
    for r in rows[:5]:
        samples.append(
            f"### {r['id']} (HTTP {r['http']})\n"
            f"**Q:** {r['question']}\n\n"
            f"**A:** {(r.get('answer') or '')[:500]}\n\n"
            f"- refusal={r.get('is_refusal')} cites={len(r.get('citations') or [])}\n"
        )

    report = f"""# CiteRAG LIVE evaluation report

**Generated:** {meta['timestamp']}  
**Git:** `{meta['git_sha']}`  
**API base:** `{base}`  
**Duration:** {duration}s  
**Mode:** hosted only (no local Docker)

## Health (after wake)

```json
{json.dumps(health, indent=2)[:800]}
```

## Pipeline stats

| Metric | Value |
|--------|------:|
| HTTP 200 answers | {stats['n_http_200']} / {stats['n_questions']} |
| With ≥1 citation | {stats['n_with_citations']} |
| Refusal OK | {stats['n_refusal_expected_ok']} |
| Refusal miss | {stats['n_refusal_expected_fail']} |
| Mean API verify accuracy | {metrics['mean_verify_accuracy']} (n={metrics['verify_n']}) |

## Samples

{chr(10).join(samples)}

## Reproduce

```bash
python scripts/run_live_eval.py
# or
CITERAG_API_BASE=https://<your-render>.onrender.com python scripts/run_live_eval.py
```

## Notes

- This pack is **live traffic** against the public demo API.
- RAGAS full four-metric suite is optional server-side (`POST /evaluate` + API_KEY).
- Free Render may cold-start; script waits up to `--wake-seconds`.
"""
    (out_dir / "REPORT.md").write_text(report)
    pointer = {
        "latest": out_dir.name,
        "path": f"docs/reports/{out_dir.name}",
        "timestamp": meta["timestamp"],
        "mode": "live",
        "status": "ok",
    }
    (ROOT / "docs" / "reports" / "latest.json").write_text(
        json.dumps(pointer, indent=2) + "\n"
    )
    print(f"\nDONE live pack: {out_dir}")
    print(json.dumps(stats, indent=2))
    return 0 if n_ok == len(items) and n_refuse_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
