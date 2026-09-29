"""Tests for building a safe, controlled retrieval context."""

from dataclasses import dataclass
from typing import Any

from rag.generation.context_builder import ContextBuilder


@dataclass(frozen=True)
class Candidate:
    chunk_id: str
    text: str
    metadata: dict[str, Any]


def test_context_builder_preserves_ordering() -> None:
    chunks = [
        Candidate(
            chunk_id="chunk-b",
            text="Second chunk about password resets.",
            metadata={"policy_id": "POL-002", "source": "policy-b.md"},
        ),
        Candidate(
            chunk_id="chunk-a",
            text="First chunk about account access.",
            metadata={"policy_id": "POL-001", "source": "policy-a.md"},
        ),
    ]

    context = ContextBuilder().build(chunks)

    assert context.index("POL-002") < context.index("POL-001")
    assert context.index("chunk-b") < context.index("chunk-a")


def test_context_builder_removes_duplicate_chunks() -> None:
    chunks = [
        Candidate(
            chunk_id="dup-1",
            text="Password reset verification rules.",
            metadata={"policy_id": "POL-001", "source": "policy-a.md"},
        ),
        Candidate(
            chunk_id="dup-1",
            text="Password reset verification rules.",
            metadata={"policy_id": "POL-001", "source": "policy-a.md"},
        ),
    ]

    context = ContextBuilder().build(chunks)

    assert context.count("dup-1") == 1
    assert context.count("Policy ID: POL-001") == 1


def test_context_builder_enforces_maximum_chunk_count() -> None:
    chunks = [
        Candidate(
            chunk_id=f"chunk-{index}",
            text=f"Password reset guidance {index}.",
            metadata={"policy_id": f"POL-{index}", "source": f"policy-{index}.md"},
        )
        for index in range(1, 5)
    ]

    context = ContextBuilder(max_chunks=2).build(chunks)

    assert context.count("Policy ID:") == 2
    assert "POL-4" not in context


def test_context_builder_preserves_metadata() -> None:
    chunks = [
        Candidate(
            chunk_id="chunk-1",
            text="Password reset verification should use MFA and a secure callback.",
            metadata={
                "policy_id": "POL-ACC-001",
                "source": "Internal Policy Library / Identity & Access Management",
                "category": "Authentication and Access",
                "status": "Approved",
            },
        )
    ]

    context = ContextBuilder().build(chunks)

    assert "Policy ID: POL-ACC-001" in context
    assert "Chunk ID: chunk-1" in context
    assert "Source: Internal Policy Library / Identity & Access Management" in context
    assert "Category: Authentication and Access" in context
    assert "Status: Approved" in context


def test_context_builder_returns_empty_string_for_no_candidates() -> None:
    assert ContextBuilder().build([]) == ""
