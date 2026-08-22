"""Unit tests for refusal detection and golden dataset shape."""

import json
from pathlib import Path

from src.generation.pipeline import _detect_refusal, extract_citations

ROOT = Path(__file__).resolve().parents[2]


def test_detect_refusal_positive():
    assert _detect_refusal("I don't have enough information to answer this.")
    assert _detect_refusal("I cannot answer that from the documents.")
    assert _detect_refusal("I'm unable to answer based on the provided context.")
    assert _detect_refusal("This is not found in the provided sources.")
    assert _detect_refusal("The corpus does not contain a phone number.")


def test_detect_refusal_negative():
    assert not _detect_refusal(
        "Annual subscriptions can be refunded within 30 days. "
        "[Source: refund-policy.md, Page 1]"
    )
    assert not _detect_refusal("The answer is 42.")


def test_extract_demo_style_source():
    text = (
        "Annual subscriptions can be refunded within 30 days of purchase. "
        "[Source: refund-policy.md, Page 1]"
    )
    cites = extract_citations(text)
    assert len(cites) == 1
    assert cites[0].source == "refund-policy.md"
    assert "30 days" in cites[0].claim


def test_demo_corpus_golden_shape():
    path = ROOT / "tests" / "eval_datasets" / "demo_corpus_golden.json"
    data = json.loads(path.read_text())
    assert len(data) >= 12
    ids = set()
    n_refuse = 0
    for item in data:
        assert "id" in item and item["id"] not in ids
        ids.add(item["id"])
        assert item["question"].strip()
        assert "ground_truth" in item
        assert "expect_refusal" in item
        assert isinstance(item.get("expected_sources"), list)
        if item["expect_refusal"]:
            n_refuse += 1
            assert item["expected_sources"] == []
    assert n_refuse >= 2
