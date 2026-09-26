"""Query-time decision gates (System One) for the RAG pipeline.

The pattern from production agent stacks: put a cheap, typed decision model in
front of the frontier model. Most queries a support/knowledge bot receives do
not need generation at all — they need a verdict.

One Jev call per query returns three decisions in parallel:

  answerable  (noul)  can the retrieved context support an answer?
  route       (choice) which retrieval strategy fits this query shape?
  complexity  (score)  how much synthesis does this query need?

Only `answerable` short-circuits the expensive LLM today, and only when Jev is
*confident the context cannot answer* — a precision-first tripwire. The other two
are recorded as telemetry so retrieval strategy can be tuned against real
queries instead of guesses.

Every gate is optional and fail-open: if Jev is unavailable, `gate_query`
returns None and the pipeline behaves exactly as before.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.config.settings import settings
from src.decisions import jev
from src.utils.logging import get_logger

log = get_logger("gates")

RETRIEVAL_ROUTES = {
    "hybrid": (
        "Multi-hop or comparison query, or wording that spans several documents "
        "(pricing plus refunds, policy plus terms). Needs dense + keyword fusion."
    ),
    "vector_only": (
        "Single semantic concept where the user's wording likely differs from the "
        "document wording (paraphrase, synonyms, conceptual questions)."
    ),
    "keyword_only": (
        "Exact identifiers, numbers, codes, dates, file names or proper nouns "
        "where literal matching matters more than meaning."
    ),
}

COMPLEXITY_LEVELS = [
    "single fact lookup - one sentence in one document answers it",
    "needs one document - a few related facts from the same source",
    "needs synthesis across documents - combines facts from separate sources",
    "needs multi-hop reasoning - answer requires chaining facts and inference",
]


@dataclass
class QueryGate:
    """The typed decisions made about one query, before generation."""

    answerable_prob: float | None = None
    route: str | None = None
    route_confidence: float | None = None
    complexity: float | None = None
    complexity_confidence: float | None = None
    # True when Jev is confident enough that the context cannot answer the
    # question that the frontier LLM call should be skipped.
    should_short_circuit: bool = False
    model: str = ""
    cost: float | None = None
    request_id: str = ""
    ok: bool = False

    def as_dict(self) -> dict:
        return {
            "answerable_probability": self.answerable_prob,
            "retrieval_route": self.route,
            "route_confidence": self.route_confidence,
            "complexity_score": self.complexity,
            "complexity_confidence": self.complexity_confidence,
            "short_circuit": self.should_short_circuit,
            "model": self.model,
            "cost": self.cost,
            "request_id": self.request_id,
        }


def gate_query(
    question: str,
    retrieved_passages: list[dict] | None = None,
) -> QueryGate | None:
    """Ask Jev for the query-time decisions. Returns None if Jev is off/down.

    `retrieved_passages` should be [{"source": str, "text": str, "score": float}]
    — evidence, not vibes. Jev judges only what you put in state.
    """
    if not (settings.jev_enabled and settings.jev_gate_enabled):
        return None
    if not jev.available():
        return None

    passages = [
        {
            "source": str(p.get("source") or p.get("file") or "unknown"),
            "score": p.get("score"),
            # Keep state tight: decisions share a ~32K token budget.
            "text": str(p.get("text") or "")[:1200],
        }
        for p in (retrieved_passages or [])
    ]

    questions = {
        "answerable": jev.noul(
            "answerable",
            "Proposition: the retrieved passages contain enough information to "
            "answer the question factually, without outside knowledge or "
            "guessing. Judge ONLY the passages given in state. If no passages "
            "were retrieved, the proposition is false.",
        ),
        "route": jev.choice(
            "route",
            "Pick the retrieval strategy that best fits the shape of this query.",
            RETRIEVAL_ROUTES,
        ),
        "complexity": jev.score(
            "complexity",
            "How much synthesis does answering this query require?",
            COMPLEXITY_LEVELS,
        ),
    }

    state = {
        "question": question,
        "retrieved_passages": passages,
        "passage_count": len(passages),
    }

    result = jev.ask(state, questions)
    if not result.ok:
        log.warning("query_gate_unavailable", error=result.error)
        return None

    answerable = result.get_probability("answerable")
    route_ans = result.choice.get("route")
    score_ans = result.score.get("complexity")

    gate = QueryGate(
        answerable_prob=answerable,
        route=route_ans.choice if route_ans else None,
        route_confidence=route_ans.confidence if route_ans else None,
        complexity=score_ans.score if score_ans else None,
        complexity_confidence=score_ans.confidence if score_ans else None,
        model=result.model,
        cost=result.usage.get("cost"),
        request_id=result.request_id,
        ok=True,
    )

    # Precision-first tripwire: only skip generation when Jev is confident the
    # context cannot answer. A false refusal is far worse than a wasted call,
    # so the floor is deliberately extreme and configurable.
    if answerable is not None and answerable <= settings.jev_gate_unanswerable_floor:
        gate.should_short_circuit = True

    log.info(
        "query_gated",
        answerable=answerable,
        route=gate.route,
        complexity=gate.complexity,
        short_circuit=gate.should_short_circuit,
        passages=len(passages),
        cost=gate.cost,
    )
    return gate
