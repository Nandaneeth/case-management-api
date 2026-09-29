"""Pydantic schemas for policy assistant queries."""

from pydantic import BaseModel, ConfigDict, Field


class AssistantQueryRequest(BaseModel):
    """Validated input for a grounded policy query."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language policy question.",
    )
    category: str | None = Field(
        default=None,
        max_length=100,
        description="Optional policy category filter.",
    )
    policy_id: str | None = Field(
        default=None,
        max_length=100,
        description="Optional policy identifier filter.",
    )
    status: str | None = Field(
        default=None,
        max_length=50,
        description="Optional policy status filter.",
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Maximum number of retrieved chunks to use.",
    )


class AssistantQueryResponse(BaseModel):
    """Grounded answer and retrieval details returned to the caller."""

    answer: str = Field(..., description="Generated grounded answer or empty refusal answer.")
    supported: bool = Field(..., description="Whether the answer has sufficient policy grounding.")
    sources: list[str] = Field(..., description="Policy sources used for the answer.")
    retrieval_metadata: dict = Field(
        ...,
        description="Retrieval strategy, filters, top_k, and evidence metadata.",
    )


__all__ = ["AssistantQueryRequest", "AssistantQueryResponse"]