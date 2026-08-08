"""DeepEval CI/CD integration for citation accuracy gates."""

from deepeval.metrics import FaithfulnessMetric, ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase


def build_faithfulness_metric(threshold: float = 0.9) -> FaithfulnessMetric:
    return FaithfulnessMetric(threshold=threshold)


def build_precision_metric(threshold: float = 0.85) -> ContextualPrecisionMetric:
    return ContextualPrecisionMetric(threshold=threshold)


def evaluate_single_response(
    question: str,
    actual_output: str,
    retrieval_context: list[str],
    faithfulness_threshold: float = 0.9,
    precision_threshold: float = 0.85,
) -> dict:
    """Evaluate a single RAG response and return metrics."""
    test_case = LLMTestCase(
        input=question,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
    )

    faithfulness_metric = build_faithfulness_metric(faithfulness_threshold)
    precision_metric = build_precision_metric(precision_threshold)

    faithfulness_metric.measure(test_case)
    precision_metric.measure(test_case)

    return {
        "faithfulness": faithfulness_metric.score,
        "faithfulness_passed": faithfulness_metric.is_successful(),
        "contextual_precision": precision_metric.score,
        "precision_passed": precision_metric.is_successful(),
    }
