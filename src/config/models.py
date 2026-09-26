"""LLM + embedding factories.

Chat uses a raw-HTTP CustomLLM against any OpenAI-compatible gateway (OpenAI,
OpenRouter, Command Code Provider, ...). We deliberately do NOT depend on
`llama-index-llms-openai`: its pinned releases import
`openai.types.responses.ResponseTextAnnotationDeltaEvent`, a symbol removed in
current `openai` SDKs, so every version combo breaks. Raw HTTP is stable.
"""
from typing import Any, List, Sequence

from src.config.settings import settings


def _base_url() -> str:
    return (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")


def _headers() -> dict:
    h = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
        # Some gateways (e.g. api.commandcode.ai behind Cloudflare) reject
        # default python HTTP user agents with 403/1010 — send a browser UA.
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
    }
    base = settings.openai_base_url or ""
    if "openrouter.ai" in base:
        h["HTTP-Referer"] = "https://rag-citation-tool.vercel.app"
        h["X-Title"] = "CiteRAG"
    return h


def _chat_http(
    model: str,
    messages: Sequence[dict],
    temperature: float = 0.1,
    max_tokens: int | None = None,
) -> str:
    """POST /chat/completions with retries.

    Reasoning models (muse-spark, nemotron) can burn the whole token budget on
    hidden reasoning and return empty content — start from a generous budget
    (settings.llm_max_tokens) and escalate further on empty replies.
    """
    import httpx

    resolved = max_tokens if max_tokens is not None else getattr(settings, "llm_max_tokens", 4096)
    base_budget = int(resolved)

    payload = {
        "model": model,
        "messages": list(messages),
        "temperature": temperature,
        "max_tokens": base_budget,
    }
    last_err = "no attempt ran"
    budgets = [base_budget, base_budget * 2, base_budget * 4]
    for attempt, budget in enumerate(budgets + [base_budget * 4] * 3):
        payload["max_tokens"] = budget
        try:
            with httpx.Client(timeout=240.0) as client:
                r = client.post(
                    f"{_base_url()}/chat/completions",
                    headers=_headers(),
                    json=payload,
                )
                if r.status_code == 429:
                    import time

                    last_err = f"429 rate limited (attempt {attempt}, budget {budget})"
                    time.sleep(3 * (attempt + 1))
                    continue
                if r.status_code >= 400:
                    last_err = f"HTTP {r.status_code}: {r.text[:300]}"
                    r.raise_for_status()
                data = r.json()
            choice = data["choices"][0]
            content = (choice.get("message") or {}).get("content") or ""
            if not content.strip():
                # empty content — likely reasoning-only completion; retry bigger
                last_err = f"empty content (finish={choice.get('finish_reason')}, budget={budget})"
                import time

                time.sleep(1)
                continue
            return content
        except Exception as exc:  # noqa: BLE001 - retry transient gateway errors
            last_err = f"{type(exc).__name__}: {exc}"
            import time

            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"chat completions failed: {last_err}")


def _embed_http(model: str, texts: List[str]) -> List[List[float]]:
    """POST /embeddings with 429/5xx retry + backoff (free gateway tiers)."""
    import time

    import httpx

    payload = {"model": model, "input": texts}
    last_err = "no attempt ran"
    import random

    for attempt in range(9):
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(f"{_base_url()}/embeddings", headers=_headers(), json=payload)
                if r.status_code == 429 or r.status_code >= 500:
                    last_err = f"HTTP {r.status_code} (attempt {attempt})"
                    time.sleep(min(4 * (attempt + 1), 25) + random.uniform(0, 2))
                    continue
                r.raise_for_status()
                data = sorted(r.json()["data"], key=lambda d: d.get("index", 0))
            return [row["embedding"] for row in data]
        except Exception as exc:  # noqa: BLE001 - retry transient gateway errors
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(min(4 * (attempt + 1), 25) + random.uniform(0, 2))
    raise RuntimeError(f"embeddings failed: {last_err}")


# --------------------------------------------------------------------------- #
# Chat LLM over raw HTTP
# --------------------------------------------------------------------------- #
def _make_http_llm(model: str, temperature: float):
    from llama_index.core.base.llms.types import (
        ChatMessage,
        ChatResponse,
        CompletionResponse,
        LLMMetadata,
        MessageRole,
    )
    from llama_index.core.llms.callbacks import (
        llm_chat_callback,
        llm_completion_callback,
    )
    from llama_index.core.llms.custom import CustomLLM

    _model_name = model
    _temperature = temperature

    class HttpChatLLM(CustomLLM):
        model_name: str = _model_name
        temperature: float = _temperature

        @property
        def metadata(self) -> LLMMetadata:
            return LLMMetadata(model_name=self.model_name, is_chat_model=True)

        @llm_completion_callback()
        def complete(self, prompt: str, formatted: bool = False, **kwargs: Any):
            text = _chat_http(
                self.model_name,
                [{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            return CompletionResponse(text=text)

        @llm_chat_callback()
        def chat(self, messages: Sequence[ChatMessage], **kwargs: Any):
            raw = []
            for m in messages:
                role = m.role.value if hasattr(m.role, "value") else str(m.role)
                raw.append({"role": role, "content": m.content or ""})
            text = _chat_http(self.model_name, raw, temperature=self.temperature)
            return ChatResponse(
                message=ChatMessage(role=MessageRole.ASSISTANT, content=text)
            )

        @llm_completion_callback()
        def stream_complete(self, prompt: str, formatted: bool = False, **kwargs: Any):
            yield self.complete(prompt, formatted=formatted, **kwargs)

        @llm_chat_callback()
        def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any):
            yield self.chat(messages, **kwargs)

    return HttpChatLLM()


def get_llm():
    return _make_http_llm(settings.llm_model, temperature=0.1)


def get_eval_llm():
    return _make_http_llm(
        settings.llm_eval_model or settings.llm_model, temperature=0.0
    )


def configure_llama_index_defaults() -> None:
    """Set llama-index global Settings so components that implicitly resolve
    `Settings.llm` / `Settings.embed_model` (QueryFusionRetriever,
    RetrieverQueryEngine, VectorStoreIndex) use our raw-HTTP gateway clients
    instead of trying to import `llama-index-llms-openai` (not installed;
    its pinned releases are broken against current openai SDKs).
    """
    from llama_index.core import Settings as LISettings

    LISettings.llm = get_llm()
    LISettings.embed_model = get_embed_model()


# --------------------------------------------------------------------------- #
# Embeddings: local fastembed (default for demo) OR raw HTTP gateway
# --------------------------------------------------------------------------- #
_fastembed_model = None


def _get_fastembed():
    """Process-wide fastembed singleton (ONNX, in-memory, no network)."""
    global _fastembed_model
    if _fastembed_model is None:
        from fastembed import TextEmbedding

        _fastembed_model = TextEmbedding(
            model_name=settings.embed_local_model or "BAAI/bge-small-en-v1.5",
            cache_dir="/tmp/fecache",
        )
    return _fastembed_model


def get_embed_model():
    from llama_index.core.embeddings import BaseEmbedding

    provider = (settings.embed_provider or "http").strip().lower()

    if provider == "local":

        class LocalFastEmbedEmbedding(BaseEmbedding):
            model_name: str = settings.embed_local_model or "BAAI/bge-small-en-v1.5"

            def _get_query_embedding(self, query: str) -> List[float]:
                return [float(x) for x in next(iter(_get_fastembed().query_embed([query])))]

            def _get_text_embedding(self, text: str) -> List[float]:
                return [float(x) for x in next(iter(_get_fastembed().embed([text])))]

            def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
                return [[float(x) for x in v] for v in _get_fastembed().embed(texts)]

            async def _aget_query_embedding(self, query: str) -> List[float]:
                return self._get_query_embedding(query)

            async def _aget_text_embedding(self, text: str) -> List[float]:
                return self._get_text_embedding(text)

        return LocalFastEmbedEmbedding()

    model = settings.embedding_model or "text-embedding-3-small"

    class HttpOpenAICompatibleEmbedding(BaseEmbedding):
        model_name: str = model

        def _get_query_embedding(self, query: str) -> List[float]:
            return _embed_http(self.model_name, [query])[0]

        def _get_text_embedding(self, text: str) -> List[float]:
            return _embed_http(self.model_name, [text])[0]

        def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
            out: List[List[float]] = []
            for i in range(0, len(texts), 16):
                out.extend(_embed_http(self.model_name, texts[i : i + 16]))
            return out

        async def _aget_query_embedding(self, query: str) -> List[float]:
            return self._get_query_embedding(query)

        async def _aget_text_embedding(self, text: str) -> List[float]:
            return self._get_text_embedding(text)

    return HttpOpenAICompatibleEmbedding()
