"""Tests for the policy text cleaner component."""

import pytest

from rag.preprocessing.cleaner import clean_policy_document, clean_policy_text


def test_clean_policy_text_normalizes_whitespace_and_blank_lines() -> None:
    raw_text = "\r\n## Purpose\r\n\r\nThis   is   a   policy.\r\n\r\r\n\n- First item\n- Second item\n"

    cleaned = clean_policy_text(raw_text)

    assert cleaned == "## Purpose\n\nThis is a policy.\n\n- First item\n- Second item"
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned


def test_clean_policy_document_keeps_metadata_separate_from_text() -> None:
    raw_text = (
        "- Policy ID: POL-001\n"
        "- Policy name: Password Reset\n"
        "- Category: Access\n"
        "- Version: 2.0\n"
        "- Effective date: 2026-01-01\n"
        "- Department: Support\n"
        "- Status: Approved\n"
        "- Source: Internal policy\n\n"
        "## Purpose\n\n"
        "This policy explains how password resets are handled.\n"
    )

    cleaned_document = clean_policy_document(raw_text)

    assert cleaned_document.metadata["policy_id"] == "POL-001"
    assert cleaned_document.metadata["policy_name"] == "Password Reset"
    assert "Policy ID" not in cleaned_document.text
    assert "## Purpose" in cleaned_document.text
    assert "This policy explains how password resets are handled." in cleaned_document.text


def test_clean_policy_document_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="empty"):
        clean_policy_text("   \n\n\r\n   ")

    with pytest.raises(ValueError, match="empty"):
        clean_policy_document("  \n\n  ")
