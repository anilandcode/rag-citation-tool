"""Citation-grounded generation with response verification."""

import re
from dataclasses import dataclass, field

from llama_index.core.llms import ChatMessage
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.prompts import PromptTemplate

from src.config.models import get_llm
from src.utils.logging import get_logger

log = get_logger("generation")

CITATION_PROMPT = PromptTemplate(
    """You are a precise research assistant. Answer the question using ONLY the provided context.

RULES:
1. Every factual claim MUST cite its source using [Source: filename, Page X]
2. If the context doesn't contain the answer, say "I don't have enough information to answer this."
3. Do NOT make up information or cite sources not provided.
4. Place each citation marker immediately after the factual statement it supports.

Context:
{context_str}

Question: {query_str}

Answer (with citations):"""
)


@dataclass
class Citation:
    source: str
    page: str
    claim: str = ""


@dataclass
class CitationVerification:
    citation: Citation
    supported: bool
    source_text: str = ""


@dataclass
class CitationVerificationReport:
    total_citations: int
    verified: int
    accuracy: float
    is_refusal: bool = False
    details: list[CitationVerification] = field(default_factory=list)


def build_query_engine(retriever, node_postprocessors=None, llm=None):
    if llm is None:
        llm = get_llm()

    return RetrieverQueryEngine.from_args(
        retriever=retriever,
        node_postprocessors=node_postprocessors or [],
        text_qa_template=CITATION_PROMPT,
        llm=llm,
    )


def _extract_claim_before_marker(text: str, match_start: int) -> str:
    before = text[:match_start].rstrip()
    while before and before[-1] in ".!?":
        before = before[:-1].rstrip()

    i = len(before) - 1
    while i >= 0:
        ch = before[i]
        if ch == "]":
            depth = 1
            i -= 1
            while i >= 0 and depth > 0:
                if before[i] == "]":
                    depth += 1
                elif before[i] == "[":
                    depth -= 1
                i -= 1
            continue
        if ch in ".!?\n":
            if i + 1 >= len(before) or before[i + 1] in " \t\n":
                break
        i -= 1
    start = i + 1 if i >= 0 else 0
    return before[start:].strip()


def extract_citations(response_text: str) -> list[Citation]:
    pattern = re.compile(
        r"\[Source:\s*([^,\]]+)"
        r"(?:,\s*(?:Page|p\.?|pg\.?|Section)\s*([^\]]+))?"
        r"\]",
        re.IGNORECASE,
    )
    citations = []
    for m in pattern.finditer(response_text):
        source = m.group(1).strip()
        page = m.group(2).strip() if m.group(2) else "N/A"
        claim = _extract_claim_before_marker(response_text, m.start())
        citations.append(Citation(source=source, page=page, claim=claim))
    return citations


def find_node_by_metadata(source_nodes, source_name):
    normalized = source_name.strip().lower().replace(" ", "_")

    for node in source_nodes:
        node_source = (node.metadata.get("source", "") or "").strip().lower()
        file_name = (node.metadata.get("file_name", "") or "").strip().lower()
        if normalized == node_source or normalized == file_name:
            return node

    for node in source_nodes:
        node_source = (node.metadata.get("source", "") or "").strip().lower()
        file_name = (node.metadata.get("file_name", "") or "").strip().lower()
        if normalized in node_source or normalized in file_name:
            return node

    return None


_REFUSAL_PATTERNS = [
    "I don't have enough information",
    "I do not have enough information",
    "I don't have sufficient information",
    "I cannot answer",
    "I'm unable to answer",
    "not enough context",
    "no information available",
    "does not contain",
    "not found in the provided",
    "not mentioned in the",
]


def _detect_refusal(response_text: str) -> bool:
    text_lower = response_text.strip().lower()
    return any(p.lower() in text_lower for p in _REFUSAL_PATTERNS)


def _leaf_text(response) -> str:
    if hasattr(response, "message") and hasattr(response.message, "content"):
        return str(response.message.content)
    if hasattr(response, "text"):
        return str(response.text)
    return str(response)


def verify_citations(
    response_text: str, source_nodes, llm=None
) -> CitationVerificationReport:
    if llm is None:
        llm = get_llm()

    citations = extract_citations(response_text)
    log.info("verification_start", citation_count=len(citations))
    if not citations:
        is_refusal = _detect_refusal(response_text)
        log.info(
            "verification_skip",
            reason="refusal" if is_refusal else "no_citations_found",
        )
        return CitationVerificationReport(
            total_citations=0,
            verified=0,
            accuracy=1.0 if is_refusal else 0.0,
            is_refusal=is_refusal,
            details=[],
        )

    details = []
    verified_count = 0

    for citation in citations:
        node = find_node_by_metadata(source_nodes, citation.source)
        is_supported = False
        source_text = ""

        if node:
            source_text = node.text[:500]
            try:
                messages = [
                    ChatMessage(
                        role="system",
                        content=(
                            "You verify whether a claim is supported by the source text. "
                            "Reply ONLY 'yes' or 'no'."
                        ),
                    ),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Claim: '{citation.claim}'\n\n"
                            f"Source text:\n{node.text[:2000]}\n\n"
                            "Is the claim supported? Reply 'yes' or 'no'."
                        ),
                    ),
                ]
                response = llm.chat(messages)
                is_supported = "yes" in _leaf_text(response).lower()
            except (ConnectionError, TimeoutError, OSError) as net_err:
                log.warning(
                    "verification_network_fallback",
                    source=citation.source,
                    error=str(net_err),
                )
                is_supported = source_name_in_text(citation.source, node.text)
            except Exception as exc:
                log.warning(
                    "verification_llm_failed",
                    source=citation.source,
                    claim=citation.claim[:100],
                    error=str(exc),
                )
                is_supported = source_name_in_text(citation.source, node.text)
        else:
            log.warning("source_node_missing", source=citation.source)

        if is_supported:
            verified_count += 1

        details.append(
            CitationVerification(
                citation=citation,
                supported=is_supported,
                source_text=source_text,
            )
        )

    total = len(citations)
    log.info(
        "verification_complete",
        total_citations=total,
        verified=verified_count,
        accuracy=verified_count / total if total > 0 else 0.0,
    )
    return CitationVerificationReport(
        total_citations=total,
        verified=verified_count,
        accuracy=verified_count / total if total > 0 else 0.0,
        details=details,
    )


def source_name_in_text(source: str, text: str) -> bool:
    return source.lower() in text.lower()
