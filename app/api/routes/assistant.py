"""HTTP routes for the policy assistant."""

from fastapi import APIRouter, Depends, status

from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.services.assistant_service import AssistantService, get_assistant_service


router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post(
    "/query",
    response_model=AssistantQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a grounded policy question",
    description="Retrieve policy context and return an answer only when it is sufficiently grounded.",
)
def query_assistant(
    request: AssistantQueryRequest,
    service: AssistantService = Depends(get_assistant_service),
) -> AssistantQueryResponse:
    """Answer a policy question through the RAG service."""
    return service.query(request)