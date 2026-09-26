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
            "LLM_MODEL": "qwen/qwen3.8-27b:free",
            "LLM_EVAL_MODEL": "qwen/qwen3.8-27b:free",
            "EMBEDDING_MODEL": "liquid/lfm-2.5-embedding-350m:free",
            "OPENAI_BASE_URL": "https://openrouter.ai/api/v1",
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
    cpu=1.0,
    min_containers=0,
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
