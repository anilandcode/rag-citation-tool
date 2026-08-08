"""Document ingestion pipeline with structure-aware chunking and metadata enrichment."""

from datetime import datetime, timezone
from typing import Optional

from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.schema import Document

from src.config.models import get_embed_model
from src.utils.logging import get_logger

log = get_logger("ingestion")


def extract_section_header(text: str) -> str:
    """Extract the most recent section header from chunk text."""
    lines = text.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped and (stripped.startswith("#") or stripped.isupper()):
            return stripped[:120]
    return ""


def classify_document_type(metadata: dict) -> str:
    """Classify document type from filename or metadata."""
    filename = metadata.get("file_name", "")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext or "unknown"


def load_documents(
    input_dir: str = "./data",
    required_exts: Optional[list[str]] = None,
) -> list[Document]:
    if required_exts is None:
        required_exts = [".pdf", ".md", ".txt", ".docx"]

    log.info("loading_documents", input_dir=input_dir, extensions=required_exts)
    reader = SimpleDirectoryReader(
        input_dir=input_dir,
        required_exts=required_exts,
        filename_as_id=True,
    )
    documents = reader.load_data()
    log.info("documents_loaded", count=len(documents))
    return documents


def chunk_documents(
    documents: list[Document],
    embed_model=None,
) -> list:
    if embed_model is None:
        embed_model = get_embed_model()

    log.info("chunking_start", document_count=len(documents))
    splitter = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
        embed_model=embed_model,
    )

    nodes = splitter.get_nodes_from_documents(documents)

    for node in nodes:
        node.metadata.update({
            "source": node.metadata.get("file_name", "unknown"),
            "page": node.metadata.get("page_label", "N/A"),
            "section": extract_section_header(node.text),
            "doc_type": classify_document_type(node.metadata),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        })

    log.info("chunking_complete", chunk_count=len(nodes))
    return nodes


def run_ingestion(input_dir: str = "./data") -> list:
    """Full ingestion pipeline: load -> chunk -> enrich metadata."""
    log.info("ingestion_start", input_dir=input_dir)
    documents = load_documents(input_dir=input_dir)
    if not documents:
        log.error("ingestion_failed", reason="no_documents_found", input_dir=input_dir)
        raise ValueError(f"No documents found in {input_dir}")

    nodes = chunk_documents(documents)
    log.info("ingestion_complete", document_count=len(documents), chunk_count=len(nodes))
    return nodes
