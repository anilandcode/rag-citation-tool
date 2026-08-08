# RAG Citation Tool

Production-ready, citation-grounded RAG pipeline with built-in evaluation harness.
Built on LlamaIndex + hybrid search + cross-encoder reranking + RAGAS/DeepEval.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Start the API
python -m src.cli ingest --input-dir ./data
uvicorn src.api.main:app --reload --port 8000
```

## CLI Commands

```bash
python -m src.cli ingest --input-dir ./data
python -m src.cli query "What is the refund policy?"
python -m src.cli eval tests/eval_datasets/sample_golden.json
python -m src.cli verify "What are supported file formats?"
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ingest` | Upload and index documents |
| `POST` | `/query` | Query with citation-grounded answer |
| `POST` | `/evaluate` | Run RAGAS evaluation on dataset |
| `POST` | `/evaluate-single` | DeepEval metrics for one query |
| `GET` | `/audit-report/{collection}` | Before/after comparison report |
| `GET` | `/health` | Health check |

## Docker

```bash
docker compose up -d
```

## Architecture

```
ingestion/  → Document loaders, semantic chunking, metadata enrichment
retrieval/  → Hybrid vector+BM25 search, Cohere cross-encoder reranking
generation/ → Citation-grounded prompts, citation extraction + verification
evaluation/ → RAGAS metrics, DeepEval CI/CD gates, audit reports
api/        → FastAPI service with Pydantic schemas, module state
```
