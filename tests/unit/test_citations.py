"""Unit tests for citation extraction and verification."""

from src.generation.pipeline import (
    extract_citations,
    Citation,
    source_name_in_text,
)


def test_extract_citations_single():
    text = "Refunds are available. [Source: policy.pdf, Page 2]"
    citations = extract_citations(text)
    assert len(citations) == 1
    assert citations[0].source == "policy.pdf"
    assert citations[0].page == "2"
    assert citations[0].claim == "Refunds are available"


def test_extract_citations_multiple():
    text = (
        "First point is important. [Source: doc1.pdf, Page 1] "
        "Second point needs evidence. [Source: doc2.pdf, Page 5]"
    )
    citations = extract_citations(text)
    assert len(citations) == 2
    assert citations[0].source == "doc1.pdf"
    assert citations[0].claim == "First point is important"
    assert citations[1].source == "doc2.pdf"
    assert citations[1].claim == "Second point needs evidence"


def test_extract_citations_none():
    text = "No citations here at all."
    citations = extract_citations(text)
    assert len(citations) == 0


def test_extract_citations_leading_citation():
    text = "[Source: foo.pdf, Page 1] This has a citation before the claim."
    citations = extract_citations(text)
    assert len(citations) == 1
    assert citations[0].claim == ""


def test_extract_citations_claim_across_newlines():
    text = (
        "The system processes requests asynchronously.\n"
        "This ensures non-blocking behavior. [Source: arch.pdf, Page 3]"
    )
    citations = extract_citations(text)
    assert len(citations) == 1
    assert "non-blocking behavior" in citations[0].claim


def test_extract_citations_multiple_with_periods_in_filenames():
    text = (
        "Refunds are available. [Source: policy.pdf, Page 2] "
        "Terms apply for annual plans. [Source: terms.pdf, Page 5]"
    )
    citations = extract_citations(text)
    assert len(citations) == 2
    assert citations[0].claim == "Refunds are available"
    assert citations[1].claim == "Terms apply for annual plans"


def test_extract_citations_no_period_between():
    text = "Config uses port 8080 [Source: config.json, Page 1] and requires SSL."
    citations = extract_citations(text)
    assert len(citations) == 1
    assert citations[0].claim == "Config uses port 8080"


def test_source_name_in_text_match():
    assert source_name_in_text("policy.pdf", "The policy.pdf document outlines")


def test_source_name_in_text_no_match():
    assert not source_name_in_text("policy.pdf", "No mention here")


# --------------------------------------------------------------------------- #
# Regression: claims must never bleed a previous citation marker into their
# text. Verification (Jev or LLM) judges the claim against the cited source, so
# a claim carrying "[Source: policy.pdf, Page 2]" gets verified against the
# wrong text and its confidence is meaningless.
# --------------------------------------------------------------------------- #

_REAL_ANSWER = (
    "Annual subscriptions can be refunded within 30 days of the initial purchase "
    "date [Source: refund-policy.md, Page 1]. After 30 days, no refunds are "
    "available for the remaining months [Source: refund-policy.md, Page 1]. "
    "Refunds are processed to the original payment method within 5-10 business "
    "days [Source: refund-policy.md, Page 2]. To request one, email "
    "billing@example.com [Source: refund-policy.md, Page 3]."
)


def test_no_claim_contains_marker_text_four_citations():
    citations = extract_citations(_REAL_ANSWER)
    assert len(citations) == 4
    for c in citations:
        assert "[Source:" not in c.claim, c.claim
        assert "]" not in c.claim, c.claim


def test_claims_are_the_sentences_they_support():
    citations = extract_citations(_REAL_ANSWER)
    claims = [c.claim for c in citations]
    assert claims[0] == (
        "Annual subscriptions can be refunded within 30 days of the initial "
        "purchase date"
    )
    assert claims[1] == "After 30 days, no refunds are available for the remaining months"
    assert claims[2] == (
        "Refunds are processed to the original payment method within 5-10 "
        "business days"
    )
    assert claims[3] == "To request one, email billing@example.com"


def test_claims_carry_no_previous_source_name():
    """A later claim must not inherit an earlier citation's filename."""
    citations = extract_citations(_REAL_ANSWER)
    for c in citations:
        assert "refund-policy.md" not in c.claim, c.claim
        assert "Page" not in c.claim, c.claim


def test_extract_citations_mixed_sources_no_bleed():
    text = (
        "Starter costs $49 per month [Source: pricing.md, Page 1]. "
        "Refunds close after 30 days [Source: refund-policy.md, Page 2]. "
        "Uptime is committed at 99.9% [Source: terms-2026.md, Page 4]."
    )
    citations = extract_citations(text)
    assert [(c.source, c.claim) for c in citations] == [
        ("pricing.md", "Starter costs $49 per month"),
        ("refund-policy.md", "Refunds close after 30 days"),
        ("terms-2026.md", "Uptime is committed at 99.9%"),
    ]
