"""Hybrid search with vector + BM25 retrieval and optional Cohere reranking."""

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.retrievers import QueryFusionRetriever, VectorIndexRetriever

from src.config.models import get_embed_model
from src.config.settings import settings
from src.utils.logging import get_logger

log = get_logger("retrieval")


def _create_pinecone_store():
    from llama_index.vector_stores.pinecone import PineconeVectorStore
    from pinecone import Pinecone

    pc = Pinecone(api_key=settings.pinecone_api_key)
    pinecone_index = pc.Index(settings.pinecone_index_name)
    return PineconeVectorStore(pinecone_index=pinecone_index)


def build_vector_index(nodes, embed_model=None, use_pinecone: bool = False):
    if embed_model is None:
        embed_model = get_embed_model()

    if use_pinecone and settings.pinecone_api_key:
        vector_store = _create_pinecone_store()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            embed_model=embed_model,
            show_progress=True,
        )
    else:
        index = VectorStoreIndex(
            nodes,
            embed_model=embed_model,
            show_progress=True,
        )

    return index


def build_vector_retriever(index) -> VectorIndexRetriever:
    return VectorIndexRetriever(
        index=index,
        similarity_top_k=settings.retrieval_top_k,
    )


def build_bm25_retriever(nodes):
    from llama_index.retrievers.bm25 import BM25Retriever

    return BM25Retriever.from_defaults(
        nodes=nodes,
        similarity_top_k=settings.retrieval_top_k,
    )


def build_hybrid_retriever(vector_retriever, bm25_retriever) -> QueryFusionRetriever:
    return QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        similarity_top_k=settings.retrieval_top_k,
        num_queries=1,
        mode="reciprocal_rerank",
        use_async=False,
    )


def build_reranker():
    if not settings.cohere_api_key:
        if settings.allow_no_rerank:
            log.info("rerank_skipped", reason="no_cohere_api_key")
            return None
        raise RuntimeError("COHERE_API_KEY required when allow_no_rerank=false")

    from llama_index.postprocessor.cohere_rerank import CohereRerank

    return CohereRerank(
        api_key=settings.cohere_api_key,
        top_n=settings.rerank_top_n,
        model=settings.rerank_model,
    )


def build_full_retrieval_pipeline(nodes, use_pinecone: bool = False):
    """End-to-end: build index + hybrid retriever + optional reranker."""
    log.info(
        "building_index",
        node_count=len(nodes),
        backend="pinecone" if use_pinecone else "memory",
    )
    index = build_vector_index(nodes, use_pinecone=use_pinecone)
    vector_retriever = build_vector_retriever(index)
    bm25_retriever = build_bm25_retriever(nodes)
    hybrid_retriever = build_hybrid_retriever(vector_retriever, bm25_retriever)
    reranker = build_reranker()
    log.info(
        "index_ready",
        top_k=settings.retrieval_top_k,
        rerank_top_n=settings.rerank_top_n if reranker else 0,
    )
    return index, hybrid_retriever, reranker
