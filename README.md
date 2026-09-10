# Case Management API

A beginner-friendly FastAPI backend for managing cases. The project will use SQLAlchemy for database access, Pydantic for validation, and SQLite for local development. The database configuration will be kept portable so PostgreSQL can be added later.

## Project Status

This repository currently contains the initial project foundation only. The case model, API endpoints, database session, error handling, logging, and tests will be added in later steps.

## Planned Structure

- `app/api/`: HTTP routers and route handlers.
- `app/core/`: Application settings and shared infrastructure.
- `app/db/`: Database engine, sessions, and SQLAlchemy models.
- `app/schemas/`: Pydantic request and response schemas.
- `app/services/`: Business logic separate from HTTP concerns.
- `tests/`: Unit and API tests.
- `sql/`: Local database files and SQL-related development artifacts.

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
pip install -r requirements.txt
```

Copy `.env.example` to `.env` when application settings are introduced. Do not commit `.env` because it may contain local or sensitive configuration.

## Running Tests

Run the test suite with:

```powershell
pytest
```

Tests will be added as the application features are implemented.

## Git Workflow

Keep `main` stable and create a feature branch for each focused change:

```text
feature/project-foundation
feature/database-model
feature/case-endpoints
feature/error-handling
feature/tests
```

Run the relevant tests before merging a feature branch into `main`.