"""Module-level state — holds the ingestion nodes and query engine for the lifetime of the API."""

from typing import Optional

_nodes: Optional[list] = None
_query_engine = None
_hybrid_retriever = None
_reranker = None


def get_nodes():
    return _nodes


def set_nodes(nodes):
    global _nodes
    _nodes = nodes


def get_query_engine():
    return _query_engine


def set_query_engine(qe):
    global _query_engine
    _query_engine = qe


def get_hybrid_retriever():
    return _hybrid_retriever


def set_hybrid_retriever(hr):
    global _hybrid_retriever
    _hybrid_retriever = hr


def get_reranker():
    return _reranker


def set_reranker(r):
    global _reranker
    _reranker = r
