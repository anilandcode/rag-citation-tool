"""Integration smoke test — validates the RAG pipeline end-to-end with no external APIs.

Run with: python tests/integration/test_smoke.py
"""

import os
import sys

# Set dummy API keys so imports don't fail
os.environ["OPENAI_API_KEY"] = "sk-test"
os.environ["COHERE_API_KEY"] = "test-cohere-key"
os.environ["PINECONE_API_KEY"] = "test-pinecone-key"
os.environ["LANGFUSE_HOST"] = "http://localhost:3000"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def test_all_modules_import():
    """Every core module must import without NameError."""
    from src.config.settings import settings
    from src.config.models import get_llm, get_eval_llm, get_embed_model
    from src.ingestion.pipeline import run_ingestion, load_documents, chunk_documents
    from src.retrieval.pipeline import build_full_retrieval_pipeline, build_reranker
    from src.generation.pipeline import (
        build_query_engine,
        extract_citations,
        verify_citations,
        Citation,
        CitationVerificationReport,
        _extract_claim_before_marker,
        find_node_by_metadata,
        source_name_in_text,
        _detect_refusal,
    )
    from src.evaluation.ragas_harness import run_ragas_evaluation, load_golden_dataset
    from src.evaluation.deepeval_harness import evaluate_single_response
    from src.evaluation.audit_report import generate_audit_report, run_audit
    from src.api.schemas import (
        QueryRequest, QueryResponse, IngestResponse,
        CitationDetail, VerificationDetail, VerificationReport,
    )
    from src.api.auth import verify_api_key, rate_limit
    from src.utils.logging import get_logger, StructuredLogger
    from src.utils.langfuse_tracer import get_langfuse, init_langfuse_llama_index
    from src.api.main import app
    from src.cli import main as cli_main

    log = get_logger("smoke_test")
    log.info("all_modules_imported", module_count=17)


def test_citation_extraction():
    """Citation extraction must parse all supported formats."""
    from src.generation.pipeline import extract_citations

    # Standard format
    c = extract_citations("Claim. [Source: doc.pdf, Page 2]")
    assert len(c) == 1
    assert c[0].source == "doc.pdf"
    assert c[0].page == "2"

    # p. variant
    c = extract_citations("Claim. [Source: doc.pdf, p. 5]")
    assert len(c) == 1
    assert c[0].page == "5"

    # pg variant
    c = extract_citations("Claim. [Source: doc.pdf, pg 8]")
    assert len(c) == 1

    # Section variant
    c = extract_citations("Claim. [Source: doc.pdf, Section 3.1]")
    assert len(c) == 1
    assert c[0].page == "3.1"

    # Page-optional (no page)
    c = extract_citations("Claim. [Source: doc.pdf]")
    assert len(c) == 1
    assert c[0].page == "N/A"

    # Case insensitive
    c = extract_citations("Claim. [source: doc.pdf, page 1]")
    assert len(c) == 1

    print("Passed: citation_extraction")


def test_refusal_detection():
    """Refusal detection must recognize common refusal phrases."""
    from src.generation.pipeline import _detect_refusal

    assert _detect_refusal("I don't have enough information to answer this.")
    assert _detect_refusal("I cannot answer that question.")
    assert _detect_refusal("I'm unable to answer based on the provided documents.")
    assert _detect_refusal("This information is not found in the provided context.")
    assert _detect_refusal("The document does not contain this information.")
    assert not _detect_refusal("The answer is 42.")
    assert not _detect_refusal("Refunds are available within 30 days.")

    print("Passed: refusal_detection")


def test_exact_source_matching():
    """find_node_by_metadata must prefer exact matches over substring."""
    from src.generation.pipeline import find_node_by_metadata

    # Create mock nodes
    class MockNode:
        def __init__(self, source, file_name):
            self.metadata = {"source": source, "file_name": file_name}

    nodes = [
        MockNode("policy.pdf", "policy.pdf"),
        MockNode("old_policy.pdf", "old_policy.pdf"),
        MockNode("terms.pdf", "terms.pdf"),
    ]

    # Exact match should return policy.pdf, not old_policy.pdf
    result = find_node_by_metadata(nodes, "policy.pdf")
    assert result is not None
    assert result.metadata["source"] == "policy.pdf"

    # Non-existent source returns None
    result = find_node_by_metadata(nodes, "nonexistent.pdf")
    assert result is None

    print("Passed: exact_source_matching")


def test_audit_report_generation():
    """Audit report must generate correct structure and summary."""
    from src.evaluation.audit_report import generate_audit_report

    report = generate_audit_report(
        collection_name="test",
        baseline_metrics={"faithfulness": 0.72},
        optimized_metrics={"faithfulness": 0.94},
        improvements=["Hybrid search", "Reranking"],
        sample_questions=[{"question": "Q1"}],
    )

    assert report["collection"] == "test"
    assert report["baseline_metrics"]["faithfulness"] == 0.72
    assert report["optimized_metrics"]["faithfulness"] == 0.94
    assert len(report["improvements"]) == 2
    assert len(report["sample_questions"]) == 1
    assert "faithfulness" in report["summary"]
    assert "0.72" in report["summary"]
    assert "0.94" in report["summary"]

    print("Passed: audit_report_generation")


def test_logger_output():
    """Structured logger must emit text and JSON without error."""
    from src.utils.logging import get_logger

    log = get_logger("test")
    log.info("test_event", key="value")
    log.warning("test_warning", reason="testing")
    log.error("test_error", error="intentional")

    print("Passed: logger_output")


if __name__ == "__main__":
    test_all_modules_import()
    test_citation_extraction()
    test_refusal_detection()
    test_exact_source_matching()
    test_audit_report_generation()
    test_logger_output()
    print("\n✅ All integration smoke tests passed.")
