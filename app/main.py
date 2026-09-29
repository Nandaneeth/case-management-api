from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.assistant import router as assistant_router
from app.api.routes.cases import router as cases_router
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.database import initialize_database
from app.dependencies import build_policy_retriever
from app.services.assistant_service import AssistantService

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    app.state.assistant_service = AssistantService(
        retriever=build_policy_retriever()
    )
    yield


app = FastAPI(
    title="Customer Support Case Management API",
    description=(
        "A beginner-friendly API for managing customer support cases raised by customers "
        "and handled by a support team."
    ),
    lifespan=lifespan,
)

app.include_router(cases_router)
app.include_router(assistant_router)
register_exception_handlers(app)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}