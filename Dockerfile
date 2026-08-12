FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DEMO_AUTO_SEED=true \
    ALLOW_NO_RERANK=true \
    DEMO_API_KEY=demo-public-key

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY src/ ./src/
COPY data/demo/ ./data/demo/
COPY pyproject.toml .

# non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}
