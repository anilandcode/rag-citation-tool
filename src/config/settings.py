from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    cohere_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "rag-citation"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    llm_model: str = "gpt-4o"
    llm_eval_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-large"
    rerank_model: str = "rerank-english-v3.0"

    rerank_top_n: int = 5
    retrieval_top_k: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
