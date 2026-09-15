# Customer Support Case Management Backend

A beginner-friendly FastAPI backend for creating, viewing, listing, and updating customer support cases. A case represents a customer issue raised with a support team, such as a password reset problem, failed payment, account access issue, or service outage. It uses SQLAlchemy for database access, Pydantic for request and response validation, and SQLite for local development. The database URL is configurable so PostgreSQL can be introduced later without changing the service and route architecture.

## Architecture

Requests follow this path:

```text
FastAPI routes -> service functions -> SQLAlchemy session -> database
```

- Routes handle HTTP input, output, and request-specific logging.
- Services contain customer support case-management business logic.
- Pydantic schemas validate API input and shape API responses.
- SQLAlchemy models describe the database tables.
- Central exception handlers provide consistent JSON errors.
- Application logs are written as JSON to standard output.

## Project Structure

```text
app/
	api/routes/cases.py       Case HTTP endpoints
	core/config.py            Environment-backed settings
	core/exceptions.py        Application exceptions and handlers
	core/logging.py           JSON logging configuration
	db/database.py            SQLAlchemy engine, sessions, and startup setup
	db/models.py              SQLAlchemy Case model
	schemas/case.py           Pydantic request and response schemas
	services/case_service.py  Case business logic
sql/
	schema.sql                Reference SQL schema
	queries.sql               Educational SQL examples
tests/
	conftest.py               Isolated in-memory database fixture
	test_cases.py             API tests
```

## Prerequisites

- Windows PowerShell
- Python 3.10 or newer
- Git, if you are working with branches

Python 3.11 is used in the current development environment. PostgreSQL is not required for local development.

## Windows Setup

From the repository root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current session, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Environment Configuration

The application reads settings from a `.env` file in the repository root. Copy the example file when you want to provide explicit settings:

```powershell
Copy-Item .env.example .env
```

The default configuration is:

```dotenv
DATABASE_URL=sqlite:///./sql/cases.db
```

SQLite remains the default. The path is relative to the directory where the server is started, so start the server from the repository root. Do not commit `.env`.

## SQLite Database

On application startup, SQLAlchemy creates missing tables in the configured database. With the default settings, the database file is `sql/cases.db`.

The reference schema is in `sql/schema.sql`. The application uses SQLAlchemy metadata at startup rather than executing that file directly.

## Start the Server

Run this command from the repository root with the virtual environment activated:

```powershell
python -m uvicorn app.main:app --reload
```

The server is available at `http://127.0.0.1:8000`.

Interactive API documentation:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## API Endpoints

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| GET | `/health` | Check that the API is running | `200` |
| POST | `/cases` | Create a customer support case | `201` |
| GET | `/cases` | List customer support cases with optional `skip` and `limit` query parameters | `200` |
| GET | `/cases/{case_id}` | Get one customer support case by ID | `200` |
| PATCH | `/cases/{case_id}` | Partially update a customer support case | `200` |

There is currently no delete endpoint.

### Example Request

With the server running, create a case from PowerShell:

```powershell
$body = @{
		case_number = "CASE-001"
		title = "Unable to reset password"
		description = "Customer receives an error after submitting the password reset form."
		status = "open"
		priority = "medium"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
		-Uri http://127.0.0.1:8000/cases `
		-ContentType "application/json" `
		-Body $body
```

List cases with pagination:

```text
GET http://127.0.0.1:8000/cases?skip=0&limit=100
```

## Validation and Errors

Request validation is handled by Pydantic. Invalid enum values, missing required fields, extra fields, invalid lengths, or invalid pagination values return HTTP `422` with FastAPI's standard `detail` error list.

Application errors use this structure:

```json
{
	"error": {
		"code": "CASE_NOT_FOUND",
		"message": "Case not found"
	}
}
```

The current application errors are:

- Missing case: HTTP `404`, code `CASE_NOT_FOUND`
- Duplicate case number: HTTP `409`, code `DUPLICATE_CASE_NUMBER`
- Unexpected server error: HTTP `500`, code `INTERNAL_SERVER_ERROR`, with a generic client message

Unexpected exception details, database information, and stack traces are logged on the server but are not returned to API clients.

## Logging

The application writes structured JSON logs to standard output. Successful customer support case operations include event names and relevant IDs. Unexpected exceptions are logged with exception details for server-side diagnosis while the API returns only the generic 500 response.

## Tests and Coverage

Run the test suite from the repository root:

```powershell
python -m pytest
```

Tests use a fresh in-memory SQLite database for each test, so they do not depend on the local `sql/cases.db` file.

Coverage is an optional development tool and is not required by the application. Install it once in the active virtual environment:

```powershell
python -m pip install coverage
```

Run pytest under coverage and view the report:

```powershell
python -m coverage run -m pytest
python -m coverage report -m
```

To create an HTML report:

```powershell
python -m coverage html
```

Open `htmlcov/index.html` in a browser to view the HTML report.

## Troubleshooting

### `python` is not recognized

Install Python 3.10 or newer and enable the option to add Python to `PATH`. You can also try the Python launcher:

```powershell
py -3 -m venv .venv
```

### `pytest` is not recognized

Activate `.venv`, or run it through the environment explicitly:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

### PowerShell will not activate the environment

Use the process-scoped execution policy command from the setup section, then run `.\.venv\Scripts\Activate.ps1` again.

### Port 8000 is already in use

Start the server on another port:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Use the same port in the documentation URLs.

### The database cannot be found or has no tables

Run the server from the repository root and check `DATABASE_URL` in `.env`. The default startup process creates the SQLite tables automatically.

## Git Workflow

Keep `main` stable and create a feature branch for each focused change:

```powershell
git switch main
git pull
git switch -c feature/case-endpoint-change
```

Run the tests before committing and opening a pull request:

```powershell
python -m pytest
```

Use focused branch names such as `feature/database-model`, `feature/case-endpoints`, or `feature/error-handling`.