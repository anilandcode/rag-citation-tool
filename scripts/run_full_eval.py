#!/usr/bin/env python3
"""Run CiteRAG end-to-end on a golden set and persist a job-demo report pack.

Usage (from repo root, venv active, OPENAI_API_KEY set):

  python scripts/run_full_eval.py
  python scripts/run_full_eval.py --golden tests/eval_datasets/demo_corpus_golden.json
  python scripts/run_full_eval.py --skip-ragas --skip-verify   # cheaper smoke
  python scripts/run_full_eval.py --limit 5

Writes:
  docs/reports/<timestamp>_demo-corpus/
    meta.json, metrics.json, gates.json, queries.jsonl, REPORT.md
  docs/reports/latest.json  (pointer)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env if present
_env = ROOT / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


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


def _bool_env(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _source_hit(answer: str, expected: list[str]) -> bool:
    if not expected:
        return True
    low = answer.lower()
    return any(s.lower() in low for s in expected)


def main() -> int:
    parser = argparse.ArgumentParser(description="CiteRAG full eval → docs/reports/")
    parser.add_argument(
        "--golden",
        default=str(ROOT / "tests/eval_datasets/demo_corpus_golden.json"),
    )
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "data/demo"),
        help="Document directory to ingest",
    )
    parser.add_argument("--limit", type=int, default=0, help="Max questions (0=all)")
    parser.add_argument("--skip-ragas", action="store_true")
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip per-claim LLM verification (faster/cheaper)",
    )
    parser.add_argument(
        "--skip-deepeval",
        action="store_true",
        default=True,
        help="Skip DeepEval (default on — heavy). Pass --run-deepeval to enable.",
    )
    parser.add_argument("--run-deepeval", action="store_true")
    parser.add_argument(
        "--out-name",
        default="",
        help="Report folder suffix (default: timestamp_demo-corpus)",
    )
    args = parser.parse_args()
    if args.run_deepeval:
        args.skip_deepeval = False

    if not os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") == "sk-...":
        print("ERROR: OPENAI_API_KEY required", file=sys.stderr)
        return 2

    # Cheap defaults for demo eval
    os.environ.setdefault("ALLOW_NO_RERANK", "true")
    os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")
    os.environ.setdefault("LLM_EVAL_MODEL", "gpt-4o-mini")

    from src.config.settings import settings
    from src.generation.pipeline import (
        _detect_refusal,
        build_query_engine,
        extract_citations,
        verify_citations,
    )
    from src.ingestion.pipeline import run_ingestion
    from src.retrieval.pipeline import build_full_retrieval_pipeline

    golden_path = Path(args.golden)
    items = json.loads(golden_path.read_text())
    if args.limit and args.limit > 0:
        items = items[: args.limit]

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    folder_name = args.out_name or f"{ts}_demo-corpus"
    out_dir = ROOT / "docs" / "reports" / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print(f"Ingesting {args.corpus} ...")
    nodes = run_ingestion(input_dir=args.corpus)
    if not nodes:
        print("ERROR: no nodes ingested", file=sys.stderr)
        return 1
    sources = sorted({n.metadata.get("source", "?") for n in nodes})
    print(f"  chunks={len(nodes)} sources={sources}")

    print("Building hybrid retrieval pipeline ...")
    _, hybrid, reranker = build_full_retrieval_pipeline(nodes)
    post = [reranker] if reranker is not None else []
    qe = build_query_engine(retriever=hybrid, node_postprocessors=post)

    queries_path = out_dir / "queries.jsonl"
    eval_rows = []
    query_rows = []
    n_refuse_ok = 0
    n_refuse_fail = 0
    n_cite = 0
    n_source_ok = 0
    n_answer = 0
    ver_acc_sum = 0.0
    ver_n = 0

    with queries_path.open("w") as qf:
        for i, item in enumerate(items, 1):
            qid = item.get("id", f"q{i}")
            question = item["question"]
            ground_truth = item.get("ground_truth", "")
            expect_refusal = bool(item.get("expect_refusal", False))
            expected_sources = item.get("expected_sources") or []
            print(f"[{i}/{len(items)}] {qid}: {question[:70]}...")

            err = None
            answer = ""
            contexts: list[str] = []
            citations = []
            verification = None
            is_refusal = False

            try:
                response = qe.query(question)
                answer = str(response)
                contexts = [getattr(n, "text", str(n)) for n in response.source_nodes]
                citations = [
                    {"source": c.source, "page": c.page, "claim": c.claim}
                    for c in extract_citations(answer)
                ]
                is_refusal = _detect_refusal(answer)
                if not args.skip_verify and not is_refusal and citations:
                    report = verify_citations(answer, response.source_nodes)
                    verification = {
                        "total_citations": report.total_citations,
                        "verified": report.verified,
                        "accuracy": report.accuracy,
                        "is_refusal": report.is_refusal,
                    }
                    ver_acc_sum += report.accuracy
                    ver_n += 1
                elif is_refusal:
                    verification = {
                        "total_citations": 0,
                        "verified": 0,
                        "accuracy": 1.0,
                        "is_refusal": True,
                    }
            except Exception as exc:
                err = str(exc)[:400]
                print(f"  ERROR: {err}")

            if answer:
                n_answer += 1
            if citations:
                n_cite += 1
            if expect_refusal:
                if is_refusal:
                    n_refuse_ok += 1
                else:
                    n_refuse_fail += 1
            if not expect_refusal and answer and _source_hit(answer, expected_sources):
                n_source_ok += 1

            row = {
                "id": qid,
                "question": question,
                "ground_truth": ground_truth,
                "expect_refusal": expect_refusal,
                "expected_sources": expected_sources,
                "answer": answer,
                "contexts": contexts,
                "citations": citations,
                "is_refusal": is_refusal,
                "verification": verification,
                "error": err,
                "category": item.get("category"),
            }
            qf.write(json.dumps(row, ensure_ascii=False) + "\n")
            query_rows.append(row)

            if not expect_refusal and answer and not err:
                eval_rows.append(
                    {
                        "question": question,
                        "ground_truth": ground_truth,
                        "answer": answer,
                        "contexts": contexts,
                    }
                )

    duration = round(time.time() - t0, 2)

    # RAGAS
    metrics = {
        "faithfulness": None,
        "answer_relevancy": None,
        "context_precision": None,
        "context_recall": None,
        "skipped": True,
        "reason": "skipped by flag or empty eval set",
    }
    if not args.skip_ragas and eval_rows:
        try:
            print(f"Running RAGAS on {len(eval_rows)} non-refusal answers ...")
            from src.evaluation.ragas_harness import run_ragas_evaluation

            metrics = run_ragas_evaluation(eval_rows)
            metrics["skipped"] = False
            metrics["n_eval_rows"] = len(eval_rows)
        except Exception as exc:
            metrics = {
                "faithfulness": None,
                "answer_relevancy": None,
                "context_precision": None,
                "context_recall": None,
                "skipped": True,
                "reason": f"ragas_failed: {exc}"[:300],
                "n_eval_rows": len(eval_rows),
            }
            print(f"RAGAS failed: {exc}")

    # DeepEval optional (first non-refusal)
    gates: dict = {"skipped": True, "cases": []}
    if not args.skip_deepeval:
        try:
            from src.evaluation.deepeval_harness import evaluate_single_response

            cases = []
            for row in query_rows:
                if row.get("expect_refusal") or not row.get("answer") or row.get("error"):
                    continue
                g = evaluate_single_response(
                    question=row["question"],
                    actual_output=row["answer"],
                    retrieval_context=row.get("contexts") or [],
                )
                cases.append({"id": row["id"], **g})
                if len(cases) >= 3:
                    break
            gates = {
                "skipped": False,
                "cases": cases,
                "all_passed": all(
                    c.get("faithfulness_passed") and c.get("precision_passed")
                    for c in cases
                )
                if cases
                else False,
            }
        except Exception as exc:
            gates = {"skipped": True, "reason": str(exc)[:300], "cases": []}

    pipeline_stats = {
        "n_questions": len(items),
        "n_answers": n_answer,
        "n_with_citations": n_cite,
        "n_refusal_expected_ok": n_refuse_ok,
        "n_refusal_expected_fail": n_refuse_fail,
        "n_source_hint_ok": n_source_ok,
        "n_non_refusal": len(eval_rows),
        "mean_verify_accuracy": round(ver_acc_sum / ver_n, 4) if ver_n else None,
        "verify_n": ver_n,
    }

    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "corpus": os.path.relpath(args.corpus, ROOT),
        "golden": os.path.relpath(str(golden_path), ROOT),
        "llm_model": getattr(settings, "llm_model", os.environ.get("LLM_MODEL")),
        "embed_model": getattr(
            settings, "embedding_model", os.environ.get("EMBEDDING_MODEL")
        ),
        "cohere_rerank": _bool_env("COHERE_API_KEY"),
        "pinecone": False,
        "skip_ragas": args.skip_ragas,
        "skip_verify": args.skip_verify,
        "skip_deepeval": args.skip_deepeval,
        "n_questions": len(items),
        "n_chunks": len(nodes),
        "sources": sources,
        "duration_sec": duration,
        "command": "python scripts/run_full_eval.py"
        + (f" --limit {args.limit}" if args.limit else "")
        + (" --skip-ragas" if args.skip_ragas else "")
        + (" --skip-verify" if args.skip_verify else ""),
    }

    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (out_dir / "gates.json").write_text(json.dumps(gates, indent=2) + "\n")
    (out_dir / "pipeline_stats.json").write_text(
        json.dumps(pipeline_stats, indent=2) + "\n"
    )

    # Human REPORT.md
    def fmt_m(key: str) -> str:
        v = metrics.get(key)
        if v is None:
            return "n/a"
        try:
            return f"{float(v):.3f}"
        except (TypeError, ValueError):
            return str(v)

    sample_lines = []
    for row in query_rows[:5]:
        sample_lines.append(
            f"### {row['id']}\n"
            f"**Q:** {row['question']}\n\n"
            f"**A:** {row['answer'][:500]}{'…' if len(row.get('answer') or '') > 500 else ''}\n\n"
            f"- refusal={row.get('is_refusal')} · citations={len(row.get('citations') or [])}\n"
        )

    report = f"""# CiteRAG evaluation report

**Generated:** {meta['timestamp']}  
**Git:** `{meta['git_sha']}`  
**Corpus:** `{meta['corpus']}` ({meta['n_chunks']} chunks)  
**Golden:** `{meta['golden']}` ({meta['n_questions']} questions)  
**Duration:** {meta['duration_sec']}s  
**Models:** LLM `{meta['llm_model']}` · embed `{meta['embed_model']}`  
**Cohere rerank:** {meta['cohere_rerank']}

> Numbers below were produced by `scripts/run_full_eval.py`. Do not hand-edit metrics.

## Pipeline stats

| Metric | Value |
|--------|------:|
| Answers produced | {pipeline_stats['n_answers']} / {pipeline_stats['n_questions']} |
| Answers with ≥1 citation | {pipeline_stats['n_with_citations']} |
| Refusal expected → refused | {pipeline_stats['n_refusal_expected_ok']} |
| Refusal expected → failed | {pipeline_stats['n_refusal_expected_fail']} |
| Non-refusal with expected source hint in answer | {pipeline_stats['n_source_hint_ok']} |
| Mean citation verify accuracy | {pipeline_stats['mean_verify_accuracy']} (n={pipeline_stats['verify_n']}) |

## RAGAS (non-refusal rows)

| Metric | Score |
|--------|------:|
| Faithfulness | {fmt_m('faithfulness')} |
| Answer relevancy | {fmt_m('answer_relevancy')} |
| Context precision | {fmt_m('context_precision')} |
| Context recall | {fmt_m('context_recall')} |

Skipped: `{metrics.get('skipped')}` {metrics.get('reason') or ''}

## DeepEval gates

Skipped: `{gates.get('skipped')}`  
Cases: `{json.dumps(gates.get('cases') or [], indent=2)[:800]}`

## Sample answers

{chr(10).join(sample_lines)}

## Reproduce

```bash
cd rag-citation-tool
source .venv/bin/activate
python scripts/run_full_eval.py --golden tests/eval_datasets/demo_corpus_golden.json
```

## Known limits

- In-memory index; process restart loses state unless re-seeded
- Hosted Render API may cold-start; local uvicorn is the reliable interview path
- Citation verify is sequential LLM calls (cost/latency)
- Sample corpus is synthetic demo docs under `data/demo/`, not a client corpus
"""
    (out_dir / "REPORT.md").write_text(report)

    pointer = {
        "latest": folder_name,
        "path": f"docs/reports/{folder_name}",
        "timestamp": meta["timestamp"],
        "git_sha": meta["git_sha"],
    }
    (ROOT / "docs" / "reports" / "latest.json").write_text(
        json.dumps(pointer, indent=2) + "\n"
    )

    print("\n=== DONE ===")
    print(f"Report: {out_dir}")
    print(json.dumps(pipeline_stats, indent=2))
    print(json.dumps({k: metrics.get(k) for k in (
        "faithfulness", "answer_relevancy", "context_precision", "context_recall", "skipped"
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
