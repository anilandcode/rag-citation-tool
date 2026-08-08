"""Langfuse observability — trace ingestion, retrieval, and generation calls."""

from contextlib import contextmanager
from typing import Optional

from langfuse import Langfuse

from src.config.settings import settings


_langfuse_client: Optional[Langfuse] = None


def get_langfuse() -> Langfuse:
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    return _langfuse_client


def init_langfuse_llama_index():
    """Register Langfuse as a LlamaIndex callback handler for observability."""
    try:
        from langfuse.llama_index import LlamaIndexCallbackHandler
        import llama_index.core

        callback_handler = LlamaIndexCallbackHandler()
        llama_index.core.global_handler = callback_handler
    except ImportError:
        try:
            import llama_index.core
            llama_index.core.set_global_handler("langfuse")
        except Exception:
            pass
    except Exception:
        pass


@contextmanager
def trace_generation(name: str = "rag-query", metadata: Optional[dict] = None):
    """Context manager for tracing a RAG query end-to-end."""
    langfuse = get_langfuse()
    trace = langfuse.trace(name=name, metadata=metadata or {})
    try:
        yield trace
    finally:
        trace.update(status="completed")


@contextmanager
def span(span_name: str, trace=None, metadata: Optional[dict] = None):
    """Create a span within a trace for a specific operation."""
    langfuse = get_langfuse()
    if trace:
        s = trace.span(name=span_name, metadata=metadata or {})
    else:
        s = langfuse.span(name=span_name)
    try:
        yield s
    finally:
        s.end()
