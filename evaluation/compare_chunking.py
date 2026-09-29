"""Compare fixed-size and structure-aware chunking for the policy corpus.

This script loads the Markdown policy corpus, cleans each document, and evaluates
both chunking strategies using a consistent set of summary metrics. It does not
add embeddings, retrieval, or any LLM-based processing.
"""

from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.chunking.fixed_chunker import ChunkerConfig, chunk_policy_document as fixed_chunk_policy_document
from rag.chunking.recursive_chunker import (
    RecursiveChunkerConfig,
    chunk_policy_document as recursive_chunk_policy_document,
)
from rag.ingestion.document_loader import load_policy_documents
from rag.preprocessing.cleaner import clean_policy_document


def _chunk_lengths(chunks: Sequence[object]) -> list[int]:
    """Return the length of each chunk based on its text payload."""
    return [len(getattr(chunk, "text", "")) for chunk in chunks]


def _summarize_chunks(chunks_by_document: Sequence[Sequence[object]]) -> dict[str, object]:
    """Compute aggregate chunking statistics for one strategy."""
    flattened_chunks: list[object] = [chunk for document_chunks in chunks_by_document for chunk in document_chunks]
    lengths = _chunk_lengths(flattened_chunks)

    if not lengths:
        raise ValueError("No chunks were produced for the supplied documents.")

    return {
        "documents": len(chunks_by_document),
        "total_chunks": len(flattened_chunks),
        "average_chunk_length": round(mean(lengths), 2),
        "min_chunk_length": min(lengths),
        "max_chunk_length": max(lengths),
        "chunks_per_document": [len(document_chunks) for document_chunks in chunks_by_document],
    }


def _chunk_documents_for_strategy(
    policy_documents: Sequence[object],
    chunker_name: str,
) -> list[list[object]]:
    """Chunk all policy documents using the selected strategy."""
    if chunker_name == "fixed":
        config = ChunkerConfig(chunk_size=500, overlap=50)
        strategy = fixed_chunk_policy_document
    elif chunker_name == "recursive":
        config = RecursiveChunkerConfig(max_chunk_size=800, overlap=80)
        strategy = recursive_chunk_policy_document
    else:
        raise ValueError(f"Unsupported chunker: {chunker_name}")

    chunked_documents: list[list[object]] = []
    for policy_document in policy_documents:
        cleaned = clean_policy_document(policy_document.text)
        chunks = strategy(
            cleaned.text,
            policy_id=policy_document.metadata.policy_id,
            source=str(policy_document.file_path),
            metadata={
                "policy_name": policy_document.metadata.policy_name,
                "category": policy_document.metadata.category,
                "version": policy_document.metadata.version,
                "department": policy_document.metadata.department,
                "status": policy_document.metadata.status,
                "source": policy_document.metadata.source,
            },
            config=config,
        )
        chunked_documents.append(chunks)

    return chunked_documents


def _print_report(name: str, summary: dict[str, object]) -> None:
    """Print a human-readable summary for one chunking strategy."""
    print(f"{name}\n{'=' * len(name)}")
    print(f"Number of documents: {summary['documents']}")
    print(f"Total chunks: {summary['total_chunks']}")
    print(f"Average chunk length: {summary['average_chunk_length']}")
    print(f"Minimum chunk length: {summary['min_chunk_length']}")
    print(f"Maximum chunk length: {summary['max_chunk_length']}")
    print(f"Chunks per document: {summary['chunks_per_document']}")
    print()


def main() -> None:
    """Load policies and compare the fixed and recursive chunking strategies."""
    policy_root = Path(__file__).resolve().parents[1] / "data" / "policies"
    policies = load_policy_documents(policy_root)

    fixed_chunks = _chunk_documents_for_strategy(policies, "fixed")
    recursive_chunks = _chunk_documents_for_strategy(policies, "recursive")

    print("Policy Chunking Comparison")
    print("=========================")
    print(f"Policy corpus directory: {policy_root}\n")

    _print_report("Fixed-size chunking", _summarize_chunks(fixed_chunks))
    _print_report("Recursive chunking", _summarize_chunks(recursive_chunks))


if __name__ == "__main__":
    main()
