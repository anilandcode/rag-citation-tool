from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    cohere_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "rag-citation"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    llm_model: str = "gpt-4o-mini"
    llm_eval_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    rerank_model: str = "rerank-english-v3.0"

    rerank_top_n: int = 5
    retrieval_top_k: int = 20

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
