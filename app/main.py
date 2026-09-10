from fastapi import FastAPI


app = FastAPI(
    title="Case Management API",
    description="A beginner-friendly API for managing cases.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}