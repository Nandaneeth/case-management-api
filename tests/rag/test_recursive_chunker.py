"""Tests for the recursive policy chunker."""

from rag.chunking.fixed_chunker import chunk_policy_document as fixed_chunk_policy_document
from rag.chunking.fixed_chunker import ChunkerConfig
from rag.chunking.recursive_chunker import RecursiveChunkerConfig, chunk_policy_document


def test_recursive_chunker_prefers_section_boundaries() -> None:
    text = (
        "# Password Reset Policy\n\n"
        "## Purpose\n\n"
        "This policy explains how password resets are handled.\n\n"
        "## Procedure\n\n"
        "1. Verify identity.\n2. Send reset link.\n3. Confirm login.\n\n"
        "## Exceptions\n\n"
        "Exceptions apply when account takeover is suspected.\n\n"
        "## Escalation guidance\n\n"
        "Escalate to security if there are signs of compromise.\n"
    )

    chunks = chunk_policy_document(text, policy_id="POL-001", source="policy.md")

    assert len(chunks) >= 3
    assert all(
        chunk.section in {"overview", "purpose", "procedure", "exceptions", "escalation guidance"}
        for chunk in chunks
    )
    assert all(chunk.policy_id == "POL-001" for chunk in chunks)
    assert all(chunk.source == "policy.md" for chunk in chunks)
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


def test_recursive_chunker_respects_max_chunk_size_and_overlap() -> None:
    text = "A" * 1800

    chunks = chunk_policy_document(
        text,
        policy_id="POL-002",
        source="large.md",
        config=RecursiveChunkerConfig(max_chunk_size=400, overlap=50),
    )

    assert len(chunks) == 5
    assert chunks[0].start_index == 0
    assert chunks[0].end_index == 400
    assert chunks[1].start_index == 350
    assert chunks[1].end_index == 750
    assert chunks[2].start_index == 700
    assert chunks[2].end_index == 1100
    assert chunks[3].start_index == 1050
    assert chunks[3].end_index == 1450
    assert chunks[4].start_index == 1400
    assert chunks[4].end_index == 1800


def test_recursive_chunker_preserves_metadata() -> None:
    text = "# Policy\n\nThis is a sample policy with multiple paragraphs.\n\n## Procedure\n\nStep one.\nStep two.\n"
    metadata = {"category": "Access", "department": "Support"}

    chunks = chunk_policy_document(text, policy_id="POL-003", source="meta.md", metadata=metadata)

    assert all(chunk.metadata["category"] == "Access" for chunk in chunks)
    assert all(chunk.metadata["department"] == "Support" for chunk in chunks)
    assert all(chunk.policy_id == "POL-003" for chunk in chunks)
    assert all(chunk.source == "meta.md" for chunk in chunks)


def test_recursive_chunker_behavior_differs_from_fixed_chunker() -> None:
    text = (
        "# Service Outage Policy\n\n"
        "## Purpose\n\n"
        "The service may be unavailable while engineering fixes the issue.\n\n"
        "## Procedure\n\n"
        "1. Confirm the outage.\n2. Communicate to customers.\n3. Restore the service.\n\n"
        "## Escalation guidance\n\n"
        "Escalate to engineering when outages affect multiple regions.\n"
    )

    fixed_chunks = fixed_chunk_policy_document(
        text,
        policy_id="POL-004",
        source="compare.md",
        config=ChunkerConfig(chunk_size=250, overlap=25),
    )
    recursive_chunks = chunk_policy_document(
        text,
        policy_id="POL-004",
        source="compare.md",
        config=RecursiveChunkerConfig(max_chunk_size=250, overlap=25),
    )

    assert len(fixed_chunks) != len(recursive_chunks)
    assert fixed_chunks[0].text != recursive_chunks[0].text
    assert recursive_chunks[0].section in {"overview", "purpose", "procedure", "escalation guidance"}
