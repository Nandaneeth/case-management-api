"""Application dependencies for policy retrieval."""

from __future__ import annotations

from pathlib import Path

from rag.chunking.fixed_chunker import ChunkerConfig, chunk_policy_document
from rag.embeddings.embedding_service import EmbeddingService
from rag.ingestion.document_loader import load_policy_documents
from rag.preprocessing.cleaner import clean_policy_document
from rag.retrieval.retriever import VectorRetriever
from rag.retrieval.vector_store import VectorStore


DEFAULT_TOP_K = 5
POLICY_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "policies"


def build_policy_retriever(
    policy_directory: str | Path = POLICY_DIRECTORY,
) -> VectorRetriever:
    """Load, clean, chunk, embed, and index the local policy corpus."""
    policy_documents = load_policy_documents(policy_directory)
    chunk_config = ChunkerConfig(chunk_size=500, overlap=50)
    chunks = []

    for document in policy_documents:
        cleaned_document = clean_policy_document(document.text)
        chunks.extend(
            chunk_policy_document(
                cleaned_document.text,
                policy_id=document.metadata.policy_id,
                source=document.metadata.source,
                metadata=document.metadata.to_dict(),
                config=chunk_config,
            )
        )

    vector_store = VectorStore(default_top_k=DEFAULT_TOP_K)
    retriever = VectorRetriever(
        embedding_service=EmbeddingService(),
        vector_store=vector_store,
        top_k=DEFAULT_TOP_K,
    )
    indexed_count = retriever.index_chunks(chunks)
    if indexed_count == 0:
        raise RuntimeError("No policy chunks were indexed from the policy directory")
    return retriever


__all__ = ["DEFAULT_TOP_K", "POLICY_DIRECTORY", "build_policy_retriever"]