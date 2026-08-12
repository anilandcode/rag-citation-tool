"""Langfuse observability — optional; never blocks the API if keys missing."""

from contextlib import contextmanager
from typing import Any, Optional

from src.config.settings import settings
from src.utils.logging import get_logger

log = get_logger("langfuse")

_langfuse_client: Any = None


class _NoopTrace:
    def update(self, *args, **kwargs):
        return self

    def span(self, *args, **kwargs):
        return _NoopTrace()

    def end(self, *args, **kwargs):
        return None


def get_langfuse():
    global _langfuse_client
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return _NoopTrace()
    if _langfuse_client is None:
        try:
            from langfuse import Langfuse

            _langfuse_client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
        except Exception as exc:
            log.warning("langfuse_init_failed", error=str(exc)[:120])
            return _NoopTrace()
    return _langfuse_client


def init_langfuse_llama_index():
    if not settings.langfuse_public_key:
        return
    try:
        from langfuse.llama_index import LlamaIndexCallbackHandler
        import llama_index.core

        llama_index.core.global_handler = LlamaIndexCallbackHandler()
    except Exception:
        pass


@contextmanager
def trace_generation(name: str = "rag-query", metadata: Optional[dict] = None):
    langfuse = get_langfuse()
    try:
        trace = langfuse.trace(name=name, metadata=metadata or {})
    except Exception:
        trace = _NoopTrace()
    try:
        yield trace
    finally:
        try:
            trace.update(status="completed")
        except Exception:
            pass
