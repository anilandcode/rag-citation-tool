"""Decision layer: typed decisions via a System One model (TypeSafe Jev).

CiteRAG splits the loop the way serious agent stacks do:

    create  -> LLM (muse-spark / any frontier model)   writes prose + citations
    decide  -> Jev  (typed, calibrated, ~1e-5 USD)      gates, scores, routes
    execute -> code (retrieval, verification math, API)

Jev is NOT a chat model. It takes `state` plus typed questions and returns
probabilities you can branch on. That makes it ideal for the two decisions a RAG
pipeline otherwise pays frontier prices for:

  1. "Is this claim actually supported by the cited passage?"  (noul per claim)
  2. "Can this question be answered from the retrieved context?" (noul)
  3. "How complex is this query / which retrieval route?"        (score, choice)

Everything here is optional and fail-open: if no key, no network, or the gateway
changes shape, `available()` is False and callers fall back to the existing LLM
or heuristic path. A decision layer must never become a new hard dependency.
"""

from .gates import QueryGate, gate_query
from .jev import (
    ChoiceAnswer,
    DecisionResult,
    NoulAnswer,
    ScoreAnswer,
    ask,
    available,
    choice,
    last_usage,
    noul,
    score,
)

__all__ = [
    "ChoiceAnswer",
    "DecisionResult",
    "NoulAnswer",
    "QueryGate",
    "ScoreAnswer",
    "ask",
    "available",
    "choice",
    "gate_query",
    "last_usage",
    "noul",
    "score",
]
