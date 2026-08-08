"""Unit tests for audit report generation."""

from src.evaluation.audit_report import generate_audit_report


def test_generate_audit_report():
    report = generate_audit_report(
        collection_name="test_collection",
        baseline_metrics={"faithfulness": 0.72, "citation_accuracy": 0.65},
        optimized_metrics={"faithfulness": 0.94, "citation_accuracy": 0.91},
        improvements=["Added hybrid search", "Added reranking"],
        sample_questions=[
            {"question": "Q1", "before_answer": "bad", "after_answer": "good"}
        ],
    )
    assert report["collection"] == "test_collection"
    assert report["baseline_metrics"]["faithfulness"] == 0.72
    assert report["optimized_metrics"]["faithfulness"] == 0.94
    assert len(report["improvements"]) == 2
    assert len(report["sample_questions"]) == 1
    assert "faithfulness" in report["summary"]
