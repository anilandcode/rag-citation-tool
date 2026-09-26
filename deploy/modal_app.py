"""Modal.com host for CiteRAG FastAPI — free tier friendly, no credit card.

Deploy:
  modal secret create citerag-secrets OPENAI_API_KEY=sk-...
  modal deploy deploy/modal_app.py

Public URL prints after deploy (*.modal.run). Point vercel.json rewrite there.
"""
from __future__ import annotations

import modal

APP_NAME = "citerag-api"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("build-essential")
    .pip_install_from_requirements("requirements-modal.txt")
    .env(
        {
            "DEMO_AUTO_SEED": "true",
            "ALLOW_NO_RERANK": "true",
            "DEMO_API_KEY": "demo-public-key",
            "CORS_ORIGINS": (
                "https://rag-citation-tool.vercel.app,"
                "http://localhost:8080,"
                "http://127.0.0.1:8080"
            ),
            "LLM_MODEL": "meta/muse-spark-1.3-contributor",
            "LLM_EVAL_MODEL": "meta/muse-spark-1.3-contributor",
            # Reasoning model: hidden reasoning burns budget before content.
            "LLM_MAX_TOKENS": "4096",
            # Local ONNX embeddings in-container: no gateway, no 429 rate limits.
            "EMBED_PROVIDER": "local",
            "EMBED_LOCAL_MODEL": "BAAI/bge-small-en-v1.5",
            "OPENAI_BASE_URL": "https://api.commandcode.ai/provider/v1",
            # Decision layer (Jev) runs on a DIFFERENT gateway than the LLM:
            # Command Code has no decision model, OpenRouter exposes
            # typesafe/jev-1.13. JEV_API_KEY comes from the secret.
            "JEV_ENABLED": "true",
            "JEV_MODEL": "typesafe/jev-1.13-20260917",
            "JEV_BASE_URL": "https://openrouter.ai/api/v1",
            "PYTHONPATH": "/root",
        }
    )
    .add_local_dir("src", remote_path="/root/src")
    .add_local_dir("data/demo", remote_path="/root/data/demo")
    .add_local_file("pyproject.toml", remote_path="/root/pyproject.toml")
)

app = modal.App(APP_NAME, image=image)


@app.function(
    secrets=[modal.Secret.from_name("citerag-secrets")],
    timeout=600,
    memory=2048,
    cpu=0.25,
    # Single warm container: the index is in-memory, so all requests must hit
    # the same process. 0.25 CPU + 2GB stays inside Modal's free credit.
    min_containers=1,
    scaledown_window=300,
)
@modal.asgi_app()
def api():
    """Serve the existing FastAPI app (lifespan seeds demo corpus)."""
    import os
    import sys

    os.chdir("/root")
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")

    from src.api.main import app as fastapi_app

    return fastapi_app
