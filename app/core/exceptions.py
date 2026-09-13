"""Application exceptions and their HTTP error responses."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class CaseNotFoundError(LookupError):
    """Raised when a requested case does not exist."""


class DuplicateCaseNumberError(ValueError):
    """Raised when a case number is already in use."""


logger = logging.getLogger(__name__)


def _error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


async def case_not_found_handler(
    request: Request, exc: CaseNotFoundError
) -> JSONResponse:
    return _error_response("CASE_NOT_FOUND", "Case not found", 404)


async def duplicate_case_number_handler(
    request: Request, exc: DuplicateCaseNumberError
) -> JSONResponse:
    return _error_response(
        "DUPLICATE_CASE_NUMBER", "Case number already exists", 409
    )


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unexpected application error")
    return _error_response("INTERNAL_SERVER_ERROR", "Internal server error", 500)


def register_exception_handlers(app: FastAPI) -> None:
    """Register the application's consistent error responses."""

    app.add_exception_handler(CaseNotFoundError, case_not_found_handler)
    app.add_exception_handler(DuplicateCaseNumberError, duplicate_case_number_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)