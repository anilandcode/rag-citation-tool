"""Audit report generation — before/after comparison for client deliverables.

Includes run_audit() which runs a golden dataset through the full RAG pipeline
and emits measured metrics, not hand-typed numbers.
"""

from typing import Optional

from src.utils.logging import get_logger

log = get_logger("audit")


def generate_audit_report(
    collection_name: str,
    baseline_metrics: dict,
    optimized_metrics: dict,
    improvements: list[str],
    sample_questions: Optional[list[dict]] = None,
) -> dict:
    return {
        "collection": collection_name,
        "baseline_metrics": baseline_metrics,
        "optimized_metrics": optimized_metrics,
        "improvements": improvements,
        "sample_questions": sample_questions or [],
        "summary": _build_summary(baseline_metrics, optimized_metrics),
    }


def _build_summary(baseline: dict, optimized: dict) -> str:
    parts = []
    for key in baseline:
        before_val = baseline.get(key, 0)
        after_val = optimized.get(key, 0)
        try:
            before = float(before_val) if before_val is not None else 0.0
            after = float(after_val) if after_val is not None else 0.0
            delta = after - before
            direction = "↑" if delta > 0 else "↓" if delta < 0 else "→"
            parts.append(f"{key}: {before:.2f} → {after:.2f} ({direction}{abs(delta):.2f})")
        except (ValueError, TypeError):
            parts.append(f"{key}: {before_val} → {after_val}")
    return "\n".join(parts)


def run_audit(
    collection_name: str,
    golden_dataset: list[dict],
    documents_dir: str = "./data",
    improvements: Optional[list[str]] = None,
) -> dict:
    """Run a full audit: ingest documents, query golden questions, evaluate.

    Args:
        collection_name: Name for the audit report.
        golden_dataset: List of {"question": "...", "ground_truth": "..."} dicts.
        documents_dir: Path to the document corpus to ingest.
        improvements: List of improvements to document in the report.

    Returns:
        A dict with baseline_metrics, optimized_metrics, improvements,
        sample_questions, and summary — identical shape to generate_audit_report().
    """
    from src.ingestion.pipeline import run_ingestion
    from src.retrieval.pipeline import build_full_retrieval_pipeline
    from src.generation.pipeline import build_query_engine
    from src.evaluation.ragas_harness import run_ragas_evaluation

    log.info("audit_start", collection=collection_name, questions=len(golden_dataset))

    # 1. Ingest documents
    nodes = run_ingestion(input_dir=documents_dir)
    if not nodes:
        log.error("audit_failed", reason="no_documents")
        return _empty_audit(collection_name, "No documents found", improvements or [])

    # 2. Build retrieval pipeline + query engine
    _, hybrid_retriever, reranker = build_full_retrieval_pipeline(nodes)
    qe = build_query_engine(
        retriever=hybrid_retriever,
        node_postprocessors=[reranker],
    )

    # 3. Query every golden question
    eval_data = []
    sample_questions = []

    for item in golden_dataset:
        question = item["question"]
        ground_truth = item.get("ground_truth", "")

        try:
            response = qe.query(question)
            answer = str(response)
            contexts = [node.text for node in response.source_nodes]
        except Exception:
            answer = ""
            contexts = []

        eval_data.append({
            "question": question,
            "ground_truth": ground_truth,
            "answer": answer,
            "contexts": contexts,
        })

        if len(sample_questions) < 5:
            sample_questions.append({
                "question": question,
                "answer": answer,
                "ground_truth": ground_truth,
            })

    # 4. Run RAGAS evaluation
    metrics = run_ragas_evaluation(eval_data)

    log.info(
        "audit_complete",
        faithfulness=metrics.get("faithfulness", 0),
        answer_relevancy=metrics.get("answer_relevancy", 0),
    )

    return generate_audit_report(
        collection_name=collection_name,
        baseline_metrics=metrics,
        optimized_metrics=metrics,
        improvements=improvements or ["Full pipeline evaluation"],
        sample_questions=sample_questions,
    )


def _empty_audit(collection_name: str, reason: str, improvements: list[str]) -> dict:
    return generate_audit_report(
        collection_name=collection_name,
        baseline_metrics={"faithfulness": 0.0},
        optimized_metrics={"faithfulness": 0.0},
        improvements=improvements,
        sample_questions=[{"question": reason}],
    )
