"""RAGAS evaluation harness for citation-grounded RAG."""

from typing import Optional

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset

from src.config.models import get_eval_llm, get_embed_model


def run_ragas_evaluation(
    eval_data: list[dict],
    eval_llm=None,
    eval_embeddings=None,
) -> dict:
    """Run RAGAS evaluation on a dataset.

    eval_data format:
        [{"question": "...", "ground_truth": "...", "answer": "...", "contexts": [...]}]
    """
    if eval_llm is None:
        eval_llm = get_eval_llm()
    if eval_embeddings is None:
        eval_embeddings = get_embed_model()

    dataset = Dataset.from_list(eval_data)

    results = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=eval_llm,
        embeddings=eval_embeddings,
    )

    def _safe_float(key):
        try:
            return float(results[key])
        except (KeyError, TypeError, ValueError):
            return 0.0

    return {
        "faithfulness": _safe_float("faithfulness"),
        "answer_relevancy": _safe_float("answer_relevancy"),
        "context_precision": _safe_float("context_precision"),
        "context_recall": _safe_float("context_recall"),
    }


def load_golden_dataset(path: str) -> list[dict]:
    """Load golden Q&A pairs from a JSON file."""
    import json

    with open(path, "r") as f:
        return json.load(f)
