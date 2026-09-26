from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    # Optional OpenAI-compatible gateway (e.g. https://openrouter.ai/api/v1)
    openai_base_url: str = ""
    cohere_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "rag-citation"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    llm_model: str = "gpt-4o-mini"
    llm_eval_model: str = "gpt-4o-mini"
    # Reasoning models (muse-spark, nemotron) burn budget on hidden reasoning
    # before emitting content — keep this generous or replies come back empty.
    llm_max_tokens: int = 4096
    embedding_model: str = "text-embedding-3-small"
    # Embedding provider: "http" (OpenAI-compatible gateway) or "local"
    # (fastembed ONNX in-process — no network, no rate limits, deterministic).
    embed_provider: str = "http"
    embed_local_model: str = "BAAI/bge-small-en-v1.5"
    rerank_model: str = "rerank-english-v3.0"

    rerank_top_n: int = 5
    retrieval_top_k: int = 20

    # --- Decision layer (TypeSafe Jev: typed decisions, not chat) ---------- #
    # When enabled, claim verification / answerability gating use Jev
    # (~1e-5 USD per decision) instead of a frontier-model "reply yes/no" call.
    # Fail-open: without a key/gateway the pipeline falls back to the LLM path.
    jev_enabled: bool = True
    jev_model: str = "typesafe/jev-1.13-20260917"
    # Optional dedicated key/base/endpoint; defaults reuse the OpenAI gateway.
    jev_api_key: str = ""
    jev_base_url: str = ""
    jev_decisions_url: str = ""
    # Direct TypeSafe API (api.typesafe.ai/v1/systemone) is the stable,
    # first-party route; OpenRouter's /api/alpha/decisions is a fallback.
    typesafe_api_key: str = ""
    typesafe_base_url: str = "https://api.typesafe.ai"
    # Model ids differ per gateway: OpenRouter needs the vendor-prefixed slug,
    # TypeSafe direct wants a bare id like "jev-latest".
    jev_model_direct: str = "jev-latest"
    jev_timeout: float = 45.0
    # Confidence floor: below this a claim is treated as unsupported and the
    # answer is flagged for human review rather than silently trusted.
    jev_support_threshold: float = 0.5
    # Route verification through Jev when available (else LLM/heuristic).
    jev_verify_citations: bool = True
    # Query-time gate: one Jev call decides answerability + retrieval route +
    # complexity before the frontier model is invoked.
    jev_gate_enabled: bool = True
    # Precision-first tripwire. Skip generation ONLY when Jev's probability that
    # the context can answer is at or below this. A false refusal costs far more
    # trust than a wasted LLM call, so keep this extreme and calibrate on your
    # own labelled set before raising it.
    jev_gate_unanswerable_floor: float = 0.02

    cors_origins: str = (
        "http://localhost:8080,http://localhost:5173,"
        "https://rag-citation-tool.vercel.app"
    )
    api_key: str = ""
    demo_api_key: str = "demo-public-key"

    # When true, seed data/demo into the index on process start
    demo_auto_seed: bool = True
    # Skip Cohere rerank if no key (vector+BM25 only) — keeps demo bootable
    allow_no_rerank: bool = True


settings = Settings()
