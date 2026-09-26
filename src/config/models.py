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
    max_tokens: int = 1024,
) -> str:
    import httpx

    payload = {
        "model": model,
        "messages": list(messages),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    last_err = "no attempt ran"
    for attempt in range(4):
        try:
            with httpx.Client(timeout=180.0) as client:
                r = client.post(
                    f"{_base_url()}/chat/completions",
                    headers=_headers(),
                    json=payload,
                )
                if r.status_code == 429:
                    import time

                    last_err = f"429 rate limited (attempt {attempt})"
                    time.sleep(3 * (attempt + 1))
                    continue
                if r.status_code >= 400:
                    last_err = f"HTTP {r.status_code}: {r.text[:300]}"
                    r.raise_for_status()
                data = r.json()
            return data["choices"][0]["message"]["content"] or ""
        except Exception as exc:  # noqa: BLE001 - retry transient gateway errors
            last_err = f"{type(exc).__name__}: {exc}"
            import time

            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"chat completions failed: {last_err}")


def _embed_http(model: str, texts: List[str]) -> List[List[float]]:
    import httpx

    payload = {"model": model, "input": texts}
    with httpx.Client(timeout=180.0) as client:
        r = client.post(f"{_base_url()}/embeddings", headers=_headers(), json=payload)
        r.raise_for_status()
        data = sorted(r.json()["data"], key=lambda d: d.get("index", 0))
    return [row["embedding"] for row in data]


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
    from llama_index.core.llms.callbacks import llm_completion_callback
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

        @llm_completion_callback()
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

        @llm_completion_callback()
        def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any):
            yield self.chat(messages, **kwargs)

    return HttpChatLLM()


def get_llm():
    return _make_http_llm(settings.llm_model, temperature=0.1)


def get_eval_llm():
    return _make_http_llm(
        settings.llm_eval_model or settings.llm_model, temperature=0.0
    )


# --------------------------------------------------------------------------- #
# Embeddings over raw HTTP
# --------------------------------------------------------------------------- #
def get_embed_model():
    from llama_index.core.embeddings import BaseEmbedding

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
