# Logging System

The RAG Citation Tool uses a custom structured logger that emits timestamped, module-tagged events to stderr. Built for both human debugging and machine parsing.

---

## Quick Start

```python
from src.utils.logging import get_logger

log = get_logger("my_module")
log.info("operation_complete", item_count=42, duration_ms=120)
# → [2026-08-06T14:22:00.000Z] INFO    [my_module] operation_complete  item_count=42 duration_ms=120
```

---

## Design

### Why Not `logging` Module?

Python's standard `logging` module is designed around linear log messages with format strings. Our system emits **structured events** — each log entry has a machine-readable event name and an arbitrary payload dict. This makes it trivial for monitoring systems, log aggregators, and AI agents to parse.

### Architecture

```
get_logger("module_name")
        │
        ▼
  StructuredLogger
        │
        ├── .info(event, **payload)
        ├── .warning(event, **payload)
        ├── .error(event, **payload)
        └── .debug(event, **payload)
                │
                ▼
        StructuredRecord
                │
        ┌───────┴───────┐
        ▼               ▼
    text format     JSON format
    (stderr)        (stderr)
```

Loggers are cached per module name via `@lru_cache` — calling `get_logger("ingestion")` twice returns the same instance.

### Format Modes

**Text** (default, `RAG_CITE_LOG_FORMAT=text` or unset):
```
[2026-08-06T14:22:00.123456Z] INFO    [ingestion] documents_loaded  count=5
[2026-08-06T14:22:02.456789Z] INFO    [ingestion] chunking_complete  chunk_count=42
[2026-08-06T14:22:05.000000Z] WARNING [generation] source_node_missing  source=unknown.pdf
[2026-08-06T14:22:05.000001Z] ERROR   [ingestion] ingestion_failed  reason=no_documents_found input_dir=./data
```

**JSON** (`RAG_CITE_LOG_FORMAT=json`):
```json
{"ts": "2026-08-06T14:22:00.123456Z", "lvl": "INFO", "mod": "ingestion", "evt": "documents_loaded", "count": 5}
{"ts": "2026-08-06T14:22:02.456789Z", "lvl": "INFO", "mod": "ingestion", "evt": "chunking_complete", "chunk_count": 42}
{"ts": "2026-08-06T14:22:05.000000Z", "lvl": "WARNING", "mod": "generation", "evt": "source_node_missing", "source": "unknown.pdf"}
{"ts": "2026-08-06T14:22:05.000001Z", "lvl": "ERROR", "mod": "ingestion", "evt": "ingestion_failed", "reason": "no_documents_found", "input_dir": "./data"}
```

---

## Event Naming Convention

Event names use `snake_case` and follow a consistent pattern:

| Pattern | Example | Meaning |
|---------|---------|---------|
| `{noun}_{past_verb}` | `documents_loaded` | A state transition completed |
| `{component}_{past_verb}` | `ingestion_complete` | A pipeline stage finished |
| `{component}_{noun}` | `index_ready` | A resource is available |
| `{component}_{failure_reason}` | `source_node_missing` | A known issue occurred |
| `{verb}_{reason}` | `verification_skip` | A decision was made |

Event names are the primary key for filtering/log aggregation. Avoid putting variable data in event names — use the payload for that.

---

## Module Names

Each module registers with a short, lowercase name:

| Module | Logger Name | Used In | Verified |
|--------|------------|---------|----------|
| `ingestion` | `rag_cite.ingestion` | `src/ingestion/pipeline.py` | ✅ |
| `retrieval` | `rag_cite.retrieval` | `src/retrieval/pipeline.py` | ✅ |
| `generation` | `rag_cite.generation` | `src/generation/pipeline.py` | ✅ |
| `api` | `rag_cite.api` | `src/api/main.py` | ✅ |
| `evaluation` | `rag_cite.evaluation` | (reserved) | — |

When adding a new module, follow the pattern: `log = get_logger("module_name")`.

> **Important**: The generation module originally used Python's stdlib `logging.getLogger(__name__)` with `logger.warning("msg %s", arg)` syntax. This was consolidated to the structured logger in v0.1.1. All modules now use the same `log = get_logger(...)` pattern. If you see `logger.` references in the codebase, they're stale — replace them with `log.` and use the structured keyword-argument API.

---

## Complete Event Catalog

### Ingestion

| Event | Level | Payload | When |
|-------|-------|---------|------|
| `loading_documents` | INFO | `input_dir`, `extensions` | Start loading files |
| `documents_loaded` | INFO | `count` | Files loaded into memory |
| `chunking_start` | INFO | `document_count` | Begin semantic splitting |
| `chunking_complete` | INFO | `chunk_count` | Splitting finished |
| `ingestion_start` | INFO | `input_dir` | Ingestion pipeline entry |
| `ingestion_failed` | ERROR | `reason`, `input_dir` | No documents found |
| `ingestion_complete` | INFO | `document_count`, `chunk_count` | Pipeline finished |

### Retrieval

| Event | Level | Payload | When |
|-------|-------|---------|------|
| `building_index` | INFO | `node_count`, `backend` | Index construction starts |
| `index_ready` | INFO | `top_k`, `rerank_top_n` | Index + retrievers built |

### Generation (Verification)

| Event | Level | Payload | When |
|-------|-------|---------|------|
| `verification_start` | INFO | `citation_count` | Begin verifying citations |
| `verification_skip` | INFO | `reason` | No citations to verify |
| `verification_network_fallback` | WARNING | `source`, `error` | LLM unreachable, used substring |
| `verification_llm_failed` | WARNING | `source`, `claim`, `error` | LLM call failed, used substring |
| `source_node_missing` | WARNING | `source` | Could not find source chunk |
| `verification_complete` | INFO | `total_citations`, `verified`, `accuracy` | Verification finished |

### API

| Event | Level | Payload | When |
|-------|-------|---------|------|
| `startup` | INFO | — | Server starting |
| `shutdown` | INFO | — | Server stopping |
| `ingest_complete` | INFO | `chunks` | `/ingest` finished |
| `query_rejected` | WARNING | `reason` | No index when querying |
| `query_complete` | INFO | `question`, `citations`, `accuracy` | `/query` finished |

---

## Environment Variables

| Variable | Values | Default | Effect |
|----------|--------|---------|--------|
| `RAG_CITE_LOG_FORMAT` | `text`, `json` | `text` | Output format |
| `RAG_CITE_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | Minimum severity (not yet enforced) |

---

## Adding Logging to a New Module

```python
from src.utils.logging import get_logger

log = get_logger("new_module")

def my_function():
    log.info("my_function_start", param1=value1)
    try:
        result = do_work()
        log.info("my_function_complete", result_count=len(result))
        return result
    except Exception as e:
        log.error("my_function_failed", error=str(e))
        raise
```

Follow these rules:
- **Event names are past-tense** for completion events (`loaded`, `complete`, `ready`)
- **Event names are present-tense** for start events (`start`, `begin`)
- **Always include relevant context** in the payload (counts, IDs, parameters)
- **Don't log secrets** — no API keys, tokens, or passwords in payload
- **Don't log full document text** — use character counts or truncated previews
