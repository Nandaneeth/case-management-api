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

## Start the ETL Mock Policy API

The Week 2 ETL source test API is separate from the Customer Support Case Management API. From the repository root, start it on port 8001:

```powershell
python -m uvicorn mock_api.policy_api:app --reload --port 8001
```

Fetch the mock policy updates from `http://127.0.0.1:8001/api/policy-updates`. The response is a small JSON array containing `policy_id`, `category_code`, and `policy_version` fields for joining with the local policy and reference datasets. Interactive API documentation is available at `http://127.0.0.1:8001/docs`.

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

## Week 2 – ETL and Data Engineering Foundation

The ETL package is separate from the FastAPI customer-support case-management API. It provides a reusable data-engineering foundation for ingesting, profiling, validating, transforming, and publishing customer-support case data.

### 1. ETL Architecture

The intended Week 2 flow is:

```text
Source -> Raw/Bronze -> Profiling & Schema Validation -> Standardized/Silver -> Data Quality -> Curated/Gold -> Audit & Reconciliation
```

The current executable local pipeline follows the Pandas path from raw sources through standardized, rejected, and curated outputs. The package also contains separate metadata-driven Spark extraction and Bronze-writing components; those components are tested independently and are not currently wired into `etl.pipeline`.

### 2. Source Ingestion

The ETL package provides readers for:

- CSV files
- JSON files
- Parquet files
- Relational database tables through SQLAlchemy
- REST APIs returning JSON arrays

The Pandas readers implement the common `SourceReader` abstraction where applicable. `etl.config.source_registry` selects a reader by source type. The executable pipeline currently reads the case, reference, and policy CSV files plus the policy-updates REST API.

### 3. Data Profiling

The profiling module reports:

- row and column counts
- null counts and completeness percentages
- distinct and duplicate counts
- value counts for string-like columns
- basic case validity checks for required columns, statuses, priorities, and case-number uniqueness

The implementation does not currently calculate general numeric descriptive statistics such as mean, median, or standard deviation. The local pipeline profiles the records selected for processing before schema and quality validation.

### 4. Schema Validation

Schemas are declared as `ColumnSpec` contracts in `etl/config/case_schema.py`. Validation supports:

- expected column names
- compatible data types
- required-value checks
- allowed-value checks for statuses and priorities
- missing-column detection

The separate `compare_schema` utility reports added, removed, and type-changed columns for schema-evolution checks. The current pipeline uses `validate_schema` and fails fast for missing required columns and incompatible data types; it does not reject extra columns as a pipeline error.

### 5. Data Quality and Rejected Records

The pipeline separates valid and invalid case records and writes rejected records with a `rejection_reason` column to `data/rejected/cases_rejected.csv`.

Implemented rejection checks include:

- missing or blank case numbers
- duplicate case numbers
- invalid statuses
- invalid priorities
- null values in required fields
- case records whose category is absent from reference data

### 6. Transformations

The Pandas ETL code implements:

- filtering through checkpoint selection, quality rules, and reference validation
- joins between cases, reference data, policy metadata, and policy updates
- status aggregation through `aggregate_cases_by_status`
- deduplication of standardized records by case number and update timestamp during output merging
- string trimming, status and priority normalization, and configured null handling
- reusable filtering, priority enrichment, and ranking helpers in `dataframe_operations.py`

The default enriched pipeline publishes selected curated columns rather than a status aggregation. The package also includes the verified PySpark transformation `summarize_standardized_cases`, which filters unusable records, keeps the latest record per case with a window function, and aggregates by status and priority. It is currently a separate transformation and is not called by `etl.pipeline`.

### 7. Layered Data Outputs

- `data/raw/` contains source CSV inputs such as cases, reference data, and policy metadata.
- `data/standardized/` contains the normalized and joined case dataset in Parquet format.
- `data/curated/` contains the consumer-oriented curated case output in Parquet format.
- `data/rejected/` contains invalid records and their rejection reasons in CSV format.
- `data/audit/` contains the incremental checkpoint written by the current pipeline.

The repository also contains `data/bronze/`, `data/silver/`, and `data/gold/` directories for the broader layered design. The current `etl.pipeline` entrypoint does not populate those directories.

### 8. Incremental and Idempotent Processing

`CheckpointStore` reads `data/audit/cases_checkpoint.json` and processes only records whose `updated_at` value is newer than `last_processed_timestamp`. After a successful run, it stores the newest processed timestamp.

Standardized output is merged with existing Parquet data and deduplicated using `case_number` plus `updated_at`. A second run with no newer records returns `completed_no_new_records`, supporting repeatable incremental execution.

### 9. Audit and Reconciliation

The package defines an `AuditRecord` model with fields for run ID, pipeline name, source, start and end times, row counts, status, and error information. `AuditLogger` can write these records as JSON Lines, but the current `etl.pipeline` entrypoint does not invoke it. Therefore, those structured audit fields are available in the package but are not currently captured in an `audit.jsonl` run log.

The current pipeline provides a JSON summary on standard output containing rows read, accepted, rejected, written, and pipeline status. It also writes the incremental checkpoint under `data/audit/`.

Reconciliation checks that source rows equal accepted plus rejected rows, and that accepted rows equal standardized rows. A failed reconciliation raises an error before outputs are written.

### 10. PySpark Environment

PySpark `4.2.0` is included in `requirements.txt` and has been verified locally with Java 17. The smoke test successfully:

- created a `SparkSession`
- reported Spark version `4.2.0`
- processed a simple Spark DataFrame containing five rows

On Windows, local Spark execution may display Hadoop or `winutils` warnings. Those warnings do not prevent the local smoke test from completing successfully when the Java environment is configured correctly.

### 11. Docker

The repository includes a Dockerfile based on Python 3.11, installs the project dependencies plus PyArrow, copies the application and ETL code, exposes `/app/data` as a volume, and starts the module with:

```text
python -m etl.pipeline
```

The image builds successfully. The default enriched pipeline also requires the mock policy API at port 8001; its current URL is hard-coded to `127.0.0.1`, so a complete container run requires the API to be colocated in the container network namespace or the URL configuration to be changed. The Dockerfile should not be treated as a standalone complete ETL deployment until that dependency is configured.

### 12. Testing

The ETL components have pytest coverage for:

- CSV, database, metadata, and source-reader behavior
- profiling and schema validation
- quality-rule rejection behavior
- Pandas pipeline idempotency and source joins
- reconciliation
- Bronze writing
- PySpark transformations, including filtering, latest-record windowing, aggregation, and required-column validation

Run the full test suite from the project root with:

```powershell
python -m pytest
```

### 13. Week 2 Progress

- [x] Common source-reader abstraction
- [x] CSV, JSON, Parquet, relational database, and REST API readers
- [x] Pandas profiling
- [x] Schema and type validation
- [x] Data-quality rules and rejected-record output
- [x] Pandas standardization, joins, null handling, and incremental output merging
- [x] Row-count reconciliation
- [x] Incremental checkpointing and idempotent reruns
- [x] PySpark transformation capability and local Spark smoke test
- [x] Pytest coverage for ETL components
- [x] Dockerfile and container build preparation
- [ ] Wire the structured `AuditLogger` into the executable pipeline
- [ ] Connect the metadata-driven Spark extraction and Bronze/Silver/Gold flow to the main pipeline
- [ ] Make the policy API URL configurable for standalone container execution