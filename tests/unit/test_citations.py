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
