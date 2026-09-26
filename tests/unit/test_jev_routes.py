"""Route selection for the Jev decision layer.

These lock the two properties that matter operationally:
  1. Fail-open — no usable route means available() is False, never an exception.
  2. Key isolation — the first-party TypeSafe key must never be sent to a
     third-party gateway host (and vice versa), whatever env is configured.
"""

import pytest

from src.config.settings import Settings
import src.decisions.jev as jev


def _routes_for(monkeypatch, env):
    """Build a route plan from env without touching the network."""
    for k in list(env_defaults):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    jev.settings = Settings()
    return jev.available(), jev._routes()


env_defaults = (
    "JEV_ENABLED", "JEV_API_KEY", "JEV_BASE_URL", "JEV_DECISIONS_URL",
    "JEV_MODEL", "JEV_MODEL_DIRECT", "TYPESAFE_API_KEY", "TYPESAFE_BASE_URL",
    "OPENAI_API_KEY", "OPENAI_BASE_URL",
)

TS_KEY = "ts-" + "K" * 20
OR_KEY = "sk-or-v1-" + "R" * 20
CC_KEY = "user_" + "C" * 20


def test_direct_and_gateway_both_present_direct_first(monkeypatch):
    available, routes = _routes_for(monkeypatch, {
        "TYPESAFE_API_KEY": TS_KEY,
        "OPENAI_API_KEY": CC_KEY,
        "OPENAI_BASE_URL": "https://api.commandcode.ai/provider/v1",
        "JEV_API_KEY": OR_KEY,
        "JEV_BASE_URL": "https://openrouter.ai/api/v1",
    })
    assert available is True
    names = [r[0] for r in routes]
    assert names == ["typesafe", "gateway"]
    assert routes[0][1] == "https://api.typesafe.ai/v1/systemone"
    assert routes[0][2] == "jev-latest"
    assert routes[1][1] == "https://openrouter.ai/api/alpha/decisions"


def test_typesafe_key_never_leaks_to_gateway_override(monkeypatch):
    """JEV_DECISIONS_URL must not redirect the first-party route."""
    available, routes = _routes_for(monkeypatch, {
        "TYPESAFE_API_KEY": TS_KEY,
        "OPENAI_API_KEY": CC_KEY,
        "JEV_API_KEY": OR_KEY,
        "JEV_BASE_URL": "https://openrouter.ai/api/v1",
        "JEV_DECISIONS_URL": "https://openrouter.ai/api/alpha/decisions",
    })
    assert available is True
    direct = [r for r in routes if r[0] == "typesafe"]
    assert direct, "direct route should still be registered"
    # The direct route keeps the TypeSafe host even with an explicit override.
    assert direct[0][1] == "https://api.typesafe.ai/v1/systemone"
    # And its Authorization header carries the TypeSafe key, sent nowhere else.
    assert direct[0][3]["Authorization"].endswith(TS_KEY)
    for name, url, _model, headers in routes:
        if name != "typesafe":
            assert not headers["Authorization"].endswith(TS_KEY)


def test_no_duplicate_urls(monkeypatch):
    available, routes = _routes_for(monkeypatch, {
        "TYPESAFE_API_KEY": TS_KEY,
        "OPENAI_API_KEY": CC_KEY,
        "JEV_API_KEY": OR_KEY,
        "JEV_BASE_URL": "https://openrouter.ai/api/v1",
        "JEV_DECISIONS_URL": "https://api.typesafe.ai/v1/systemone",
    })
    urls = [r[1] for r in routes]
    assert len(urls) == len(set(urls)), urls


def test_gateway_only_when_no_typesafe_key(monkeypatch):
    available, routes = _routes_for(monkeypatch, {
        "OPENAI_API_KEY": CC_KEY,
        "OPENAI_BASE_URL": "https://api.commandcode.ai/provider/v1",
        "JEV_API_KEY": OR_KEY,
        "JEV_BASE_URL": "https://openrouter.ai/api/v1",
    })
    assert available is True
    assert [r[0] for r in routes] == ["gateway"]


def test_fail_open_when_nothing_configured(monkeypatch):
    available, routes = _routes_for(monkeypatch, {"OPENAI_API_KEY": CC_KEY})
    assert available is False
    assert routes == []


def test_disabled_flag_wins_over_keys(monkeypatch):
    available, routes = _routes_for(monkeypatch, {
        "JEV_ENABLED": "false",
        "TYPESAFE_API_KEY": TS_KEY,
        "JEV_API_KEY": OR_KEY,
        "JEV_BASE_URL": "https://openrouter.ai/api/v1",
    })
    assert available is False
    assert routes == []


def test_ask_returns_not_ok_without_raising_when_unavailable(monkeypatch):
    """A decision layer must never raise into the query path."""
    _routes_for(monkeypatch, {"OPENAI_API_KEY": CC_KEY})
    result = jev.ask({"q": 1}, {"a": jev.noul("a", "proposition")})
    assert result.ok is False
    assert result.error == "jev_unavailable"


def test_ask_returns_not_ok_on_empty_questions(monkeypatch):
    _routes_for(monkeypatch, {"TYPESAFE_API_KEY": TS_KEY})
    result = jev.ask({"q": 1}, {})
    assert result.ok is False
    assert result.error == "no_questions"
