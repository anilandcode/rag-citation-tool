from src.config.settings import settings


def get_llm():
    from llama_index.llms.openai import OpenAI
    return OpenAI(model=settings.llm_model, api_key=settings.openai_api_key)


def get_eval_llm():
    from llama_index.llms.openai import OpenAI
    return OpenAI(model=settings.llm_eval_model, api_key=settings.openai_api_key)


def get_embed_model():
    from llama_index.embeddings.openai import OpenAIEmbedding
    return OpenAIEmbedding(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
