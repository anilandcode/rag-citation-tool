"""Structured logging for the RAG Citation Tool.

Every log entry includes a module/component tag, can be output as JSON for
machine consumption or human-readable text for local dev.

Usage:
    from src.utils.logging import get_logger
    log = get_logger("ingestion")
    log.info("chunk_complete", document_count=5, chunk_count=42)
    log.warning("empty_index", reason="no_documents_in_dir")
"""

import inspect
import json
import logging
import os
import sys
import time
from functools import lru_cache
from typing import Optional

LOG_FORMAT = os.environ.get("RAG_CITE_LOG_FORMAT", "text")
LOG_LEVEL = os.environ.get("RAG_CITE_LOG_LEVEL", "INFO").upper()


class StructuredRecord:
    """A single log event with key-value payload."""

    def __init__(self, module: str, level: str, event: str, **kwargs):
        self.timestamp = time.time()
        self.iso = _iso_utc(self.timestamp)
        self.module = module
        self.level = level
        self.event = event
        self.payload = kwargs


def _iso_utc(ts: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


class StructuredLogger:
    """Module-scoped logger that emits structured records.

    Each module gets its own instance via get_logger("module_name").
    """

    def __init__(self, module: str):
        self.module = module
        self._py_logger = logging.getLogger(f"rag_cite.{module}")
        if not self._py_logger.handlers:
            self._py_logger.setLevel(LOG_LEVEL)

    def debug(self, event: str, **kwargs):
        self._emit("DEBUG", event, **kwargs)

    def info(self, event: str, **kwargs):
        self._emit("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self._emit("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs):
        self._emit("ERROR", event, **kwargs)

    def _emit(self, level: str, event: str, **kwargs):
        record = StructuredRecord(self.module, level, event, **kwargs)
        if LOG_FORMAT == "json":
            print(json.dumps({
                "ts": record.iso,
                "lvl": record.level,
                "mod": record.module,
                "evt": record.event,
                **record.payload,
            }, default=str), file=sys.stderr)
        else:
            payload_str = " ".join(f"{k}={v}" for k, v in record.payload.items())
            msg = f"[{record.iso}] {record.level:7s} [{record.module}] {record.event}"
            if payload_str:
                msg += f"  {payload_str}"
            print(msg, file=sys.stderr)


@lru_cache(maxsize=64)
def get_logger(module: str) -> StructuredLogger:
    return StructuredLogger(module)
