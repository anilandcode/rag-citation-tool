"""Minimal TypeSafe Jev client over plain HTTP.

Why not the `typesafe-ai` SDK: TypeSafe signups are paused (as of Sept 2026) and
the SDK binds us to one vendor. Jev is reachable through any OpenAI-style gateway
that lists it, so we speak the decisions endpoint directly with httpx and keep the
transport swappable via env. Verified working contract (OpenRouter):

    POST https://openrouter.ai/api/alpha/decisions
    {
      "model": "typesafe/jev-1.13-20260917",
      "state": {...},
      "questions": {
        "q_id": {"type": "noul",   "instructions": "..."},
        "q_id": {"type": "choice", "instructions": "...",
                 "criteria": {"opt": "description", ...}},
        "q_id": {"type": "score",  "instructions": "...",
                 "criteria": ["lowest", ..., "highest"]}
      }
    }
    -> {"answers": {"q_id": {"type": "noul", "noul": 0.99}, ...},
        "usage": {"input_tokens": n, "output_tokens": n, "cost": f}}

Answers are probabilities, not correctness guarantees. Callers must apply their
own threshold and never auto-execute an irreversible action on confidence alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config.settings import settings
from src.utils.logging import get_logger

log = get_logger("decisions")

# --------------------------------------------------------------------------- #
# Answers
# --------------------------------------------------------------------------- #


@dataclass
class NoulAnswer:
    """Yes/no with calibrated probability that the proposition holds."""

    question_id: str
    probability: float

    @property
    def value(self) -> bool:
        return self.probability >= self.threshold

    threshold: float = 0.5


@dataclass
class ChoiceAnswer:
    """One picked option, with the full probability distribution kept."""

    question_id: str
    choice: str
    confidence: float
    probabilities: dict[str, float] = field(default_factory=dict)


@dataclass
class ScoreAnswer:
    """Ordinal rating as a float index into the ordered criteria levels."""

    question_id: str
    score: float
    confidence: float
    legend: dict[str, str] = field(default_factory=dict)
    probabilities: dict[str, float] = field(default_factory=dict)


@dataclass
class DecisionResult:
    """Everything one Jev call returned, parsed into typed answers."""

    ok: bool
    noul: dict[str, NoulAnswer] = field(default_factory=dict)
    choice: dict[str, ChoiceAnswer] = field(default_factory=dict)
    score: dict[str, ScoreAnswer] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    request_id: str = ""
    # Which transport served this: "typesafe" (first-party) or "gateway".
    route: str = ""
    error: str = ""

    def get_bool(self, question_id: str, default: bool | None = None) -> bool | None:
        a = self.noul.get(question_id)
        return a.value if a else default

    def get_probability(
        self, question_id: str, default: float | None = None
    ) -> float | None:
        a = self.noul.get(question_id)
        return a.probability if a else default

    def get_choice(self, question_id: str, default: str | None = None) -> str | None:
        a = self.choice.get(question_id)
        return a.choice if a else default

    def get_score(self, question_id: str, default: float | None = None) -> float | None:
        a = self.score.get(question_id)
        return a.score if a else default


# --------------------------------------------------------------------------- #
# Config / availability
# --------------------------------------------------------------------------- #

_last_usage: dict[str, Any] = {}


def last_usage() -> dict[str, Any]:
    """Usage from the most recent successful Jev call (cost tracking)."""
    return dict(_last_usage)


def _direct_key() -> str:
    """First-party TypeSafe key, if configured."""
    return (settings.typesafe_api_key or "").strip()


def _router_key() -> str:
    """Key for the gateway route (explicit Jev key, else the LLM gateway key)."""
    return (settings.jev_api_key or settings.openai_api_key or "").strip()


def available() -> bool:
    """True when at least one Jev route (direct TypeSafe or gateway) is usable.

    Fail-open by design: without this, callers use the LLM/heuristic path.
    """
    if not settings.jev_enabled:
        return False
    return bool(_direct_key()) or bool(_router_key() and _decisions_url())


def _routes() -> list[tuple[str, str, str, dict[str, str]]]:
    """Ordered candidate routes: (name, url, model, headers).

    Direct TypeSafe first — it is first-party and stable; the OpenRouter
    `/api/alpha/decisions` path is explicitly alpha and may change or vanish.
    Both return the same {answers, usage} shape, so parsing is shared.
    """
    out: list[tuple[str, str, str, dict[str, str]]] = []

    direct = _direct_key()
    if direct:
        base = (settings.typesafe_base_url or "https://api.typesafe.ai").rstrip("/")
        url = settings.jev_decisions_url or (base + "/v1/systemone")
        out.append((
            "typesafe",
            url,
            settings.jev_model_direct or "jev-latest",
            {
                "Authorization": "Bearer " + direct,
                "Content-Type": "application/json",
                "User-Agent": _UA,
            },
        ))

    key = _router_key()
    gateway_url = _decisions_url()
    if key and gateway_url:
        # Never register the same URL twice (e.g. JEV_DECISIONS_URL pointed at
        # TypeSafe while a direct key is also set).
        if not any(url == gateway_url for _, url, _, _ in out):
            out.append(("gateway", gateway_url, settings.jev_model, _headers(key)))

    return out


def _decisions_url() -> str:
    """Gateway decisions endpoint, derived from the configured base URL.

    OpenRouter exposes /api/alpha/decisions (sibling of /api/v1). A dedicated
    JEV_DECISIONS_URL always wins so other gateways need no code change.
    """
    explicit = (settings.jev_decisions_url or "").strip()
    if explicit:
        return explicit

    base = (settings.jev_base_url or settings.openai_base_url or "").strip()
    if not base:
        return ""
    if "openrouter.ai" in base:
        # https://openrouter.ai/api/v1 -> .../api/alpha/decisions
        return base.split("/api/")[0].rstrip("/") + "/api/alpha/decisions"
    # Generic OpenAI-compatible guess: <base>/decisions
    return base.rstrip("/") + "/decisions"


# Cloudflare-fronted gateways reject default python HTTP user agents.
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def _headers(api_key: str) -> dict[str, str]:
    h = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
        "User-Agent": _UA,
    }
    base = settings.jev_base_url or settings.openai_base_url or ""
    if "openrouter.ai" in base:
        h["HTTP-Referer"] = "https://rag-citation-tool.vercel.app"
        h["X-Title"] = "CiteRAG"
    return h


# --------------------------------------------------------------------------- #
# Call
# --------------------------------------------------------------------------- #


def ask(
    state: Any,
    questions: dict[str, dict[str, Any]],
    *,
    model: str | None = None,
    threshold: float = 0.5,
    timeout: float | None = None,
) -> DecisionResult:
    """Send one shared-state batch of typed questions to Jev.

    Parallel questions in a single call barely add latency versus separate
    calls, and they cost fractions of a cent — batch aggressively.

    Never raises: transport/parse failures return DecisionResult(ok=False) so a
    decision layer can never take down the query path.
    """
    global _last_usage

    if not questions:
        return DecisionResult(ok=False, error="no_questions")

    routes = _routes()
    if not routes:
        return DecisionResult(ok=False, error="jev_unavailable")

    import httpx

    state_payload = state if not isinstance(state, str) else {"text": state}
    tmo = timeout if timeout is not None else settings.jev_timeout

    data = None
    used_route = ""
    used_model = ""
    last_error = "no route attempted"

    # Try each route in order: a first-party TypeSafe key is preferred, and we
    # fall through to the gateway only if the direct call fails. Any HTTP/parse
    # error moves to the next route rather than killing the decision.
    for name, url, route_model, headers in routes:
        payload = {
            "model": model or route_model,
            "state": state_payload,
            "questions": questions,
        }
        try:
            with httpx.Client(timeout=tmo) as client:
                r = client.post(url, headers=headers, json=payload)
                if r.status_code != 200:
                    last_error = name + ":http_" + str(r.status_code)
                    log.warning(
                        "jev_route_http_error", route=name,
                        status=r.status_code, body=r.text[:200],
                    )
                    continue
                candidate = r.json()
        except httpx.TimeoutException as exc:
            # An unknown outcome may ALREADY be charged and the endpoint
            # documents no idempotency key — stop rather than fail over to a
            # second route and risk paying twice for one decision.
            last_error = name + ":timeout"
            log.warning("jev_route_timeout", route=name, error=str(exc)[:200])
            return DecisionResult(ok=False, error=last_error)
        except Exception as exc:  # noqa: BLE001 - safe to try the next route
            last_error = name + ":" + type(exc).__name__
            log.warning("jev_route_failed", route=name, error=str(exc)[:200])
            continue

        answers = candidate.get("answers") or {}
        if not answers:
            last_error = name + ":empty_answers"
            log.warning("jev_route_empty", route=name, raw=str(candidate)[:200])
            continue

        data = candidate
        used_route = name
        used_model = str(candidate.get("model") or payload["model"])
        break

    if data is None:
        return DecisionResult(ok=False, error=last_error)

    answers = data.get("answers") or {}
    result = DecisionResult(
        ok=True,
        usage=data.get("usage") or {},
        model=used_model,
        request_id=str(data.get("id") or ""),
        route=used_route,
    )

    for qid, raw in answers.items():
        if not isinstance(raw, dict):
            continue
        qtype = str(raw.get("type", "")).lower()
        try:
            if qtype == "noul":
                result.noul[qid] = NoulAnswer(
                    question_id=qid,
                    probability=float(raw.get("noul", 0.0)),
                    threshold=threshold,
                )
            elif qtype == "choice":
                result.choice[qid] = ChoiceAnswer(
                    question_id=qid,
                    choice=str(raw.get("choice", "")),
                    confidence=float(raw.get("confidence", 0.0)),
                    probabilities={
                        str(k): float(v)
                        for k, v in (raw.get("probabilities") or {}).items()
                    },
                )
            elif qtype == "score":
                result.score[qid] = ScoreAnswer(
                    question_id=qid,
                    score=float(raw.get("score", 0.0)),
                    confidence=float(raw.get("confidence", 0.0)),
                    legend={
                        str(k): str(v) for k, v in (raw.get("legend") or {}).items()
                    },
                    probabilities={
                        str(k): float(v)
                        for k, v in (raw.get("probabilities") or {}).items()
                    },
                )
        except (TypeError, ValueError) as exc:
            log.warning("jev_answer_parse_failed", qid=qid, error=str(exc)[:120])

    _last_usage = dict(result.usage)
    log.info(
        "jev_decided",
        questions=len(questions),
        answered=len(answers),
        noul=len(result.noul),
        choice=len(result.choice),
        score=len(result.score),
        cost=result.usage.get("cost"),
        model=result.model,
        route=result.route,
    )
    return result


# --------------------------------------------------------------------------- #
# Question builders — keep instructions evidence-rich, never vague
# --------------------------------------------------------------------------- #


def noul(question_id: str, instructions: str) -> dict[str, Any]:
    """Proposition -> probability it holds. Put the real policy in instructions."""
    return {"type": "noul", "instructions": instructions}


def choice(
    question_id: str, instructions: str, options: dict[str, str]
) -> dict[str, Any]:
    """Pick one labeled option. Jev reads option TEXT, not your variable names."""
    return {
        "type": "choice",
        "instructions": instructions,
        "criteria": options,
    }


def score(
    question_id: str, instructions: str, levels: list[str]
) -> dict[str, Any]:
    """Ordinal rating; score comes back as a float index into `levels`."""
    return {
        "type": "score",
        "instructions": instructions,
        "criteria": levels,
    }
