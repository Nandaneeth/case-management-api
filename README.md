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

## Week 3 – Policy Knowledge RAG Assistant

### 1. Week 3 Objective

Build a local policy retrieval and answering path for customer-support questions, preserve policy metadata through retrieval, refuse when retrieval evidence is insufficient, expose the capability through FastAPI, and evaluate retrieval configurations against a fixed policy-question dataset.

This section describes implemented code and existing tests/results. It does not imply that a real LLM provider or a successful production-model startup has been verified.

### 2. RAG Architecture

```text
data/policies/*.md
	-> rag/ingestion/document_loader.py
	-> rag/preprocessing/cleaner.py
	-> rag/chunking/fixed_chunker.py or recursive_chunker.py
	-> rag/embeddings/embedding_service.py
	-> rag/retrieval/vector_store.py
	-> vector, keyword, or hybrid retrieval
	-> rag/retrieval/reranker.py
	-> rag/generation/context_builder.py
	-> rag/service.py
	-> configured generation provider
	-> POST /assistant/query
```

Production startup currently indexes the policy corpus with fixed chunking and vector retrieval. Keyword/hybrid retrieval, recursive chunking, and evaluation configurations are implemented and tested separately; the FastAPI assistant does not currently select the hybrid path.

### 3. Policy Document Corpus

The current corpus contains five Markdown files in `data/policies/`:

| File | Policy ID | Policy name | Category | Version | Effective date | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `account_access_policy.md` | `POL-ACC-002` | Customer Account Access and Authorization Standard | Identity and Access Management | 4.2 | 2026-03-01 | Approved |
| `password_reset_policy.md` | `POL-ACC-001` | Customer Password Reset Standard | Authentication and Access | 2.4 | 2026-01-15 | Approved |
| `payment_failure_policy.md` | `POL-BILL-014` | Payment Failure Resolution and Retry Guidance | Billing and Collections | 3.1 | 2026-02-10 | Approved |
| `refund_policy.md` | `POL-CUST-027` | Customer Refund Eligibility and Processing Policy | Customer Resolution and Billing | 1.8 | 2026-05-05 | Approved |
| `service_outage_policy.md` | `POL-OPS-009` | Service Outage Communication and Recovery Standard | Service Reliability | 5.0 | 2026-04-20 | Approved |

Each file also declares department and source metadata. These metadata fields are parsed by the document loader; the table above omits those two fields for readability.

### 4. Document Ingestion

`rag/ingestion/document_loader.py` defines `PolicyDocument`, `PolicyMetadata`, `parse_policy_document()`, and `load_policy_documents()`. The loader finds `.md` files in sorted path order, reads UTF-8 Markdown, and requires policy ID, policy name, category, version, effective date, department, status, and source.

### 5. Preprocessing

`rag/preprocessing/cleaner.py` normalizes line endings, trims lines, collapses repeated whitespace, and reduces excess blank lines while preserving headings and policy content. `clean_policy_document()` returns cleaned text with structured metadata separated. The production index builder calls this function before chunking.

### 6. Chunking Strategies

- `rag/chunking/fixed_chunker.py`: `chunk_policy_document()` splits content into fixed-size overlapping chunks, preserves metadata, and creates deterministic IDs. Production startup uses `ChunkerConfig(chunk_size=500, overlap=50)`.
- `rag/chunking/recursive_chunker.py`: `chunk_policy_document()` prefers policy section boundaries such as Purpose, Scope, Procedure, Exceptions, and Escalation, then uses fixed-size splitting with overlap. Its behavior and metadata preservation have unit tests. Production startup currently uses the fixed chunker, not this strategy.

### 7. Embeddings

`rag/embeddings/embedding_service.py` defines `EmbeddingService`. Its default Sentence Transformers model is `sentence-transformers/all-MiniLM-L6-v2`; the service normalizes vectors, supports individual query/document embeddings and batches, and checks returned dimensions. The dimension is read from the loaded model rather than configured as a constant.

The production builder calls `EmbeddingService()` without an injected model. The package is declared as `sentence-transformers==6.1.0` in `requirements.txt`, but the active runtime has reported `ModuleNotFoundError: sentence_transformers`. Tests inject deterministic fake models and therefore do not verify installation or model loading. The pretrained model may need to be downloaded/cached before the API can start successfully.

### 8. Vector Index

`rag/retrieval/vector_store.py` implements `VectorStore`, which stores embeddings and metadata in a Python dictionary and searches by cosine similarity. `save()` and `load()` can persist the index as JSON when explicitly called; the production API does not call them. Production currently builds an in-memory index at startup, so each app worker has its own index and the index is rebuilt after restart.

### 9. Vector Retrieval

`rag/retrieval/retriever.py` defines `VectorRetriever` and `RetrievedChunk`. `index_chunks()` embeds chunk text in a batch and inserts vectors plus metadata into the store. `retrieve()` embeds the query and requests ranked cosine matches. Retrieval tests verify indexing, stable results, ordered scores, metadata preservation, and empty-index behavior using fake embedding models.

### 10. Metadata Filtering

Vector, keyword, hybrid, and vector-store searches support metadata filters for `category`, `policy_id`, `version`, `status`, and `department`. Matching is case-insensitive in the store and keyword/hybrid paths. The assistant request exposes optional `category`, `policy_id`, and `status` filters and passes non-null values through to retrieval.

### 11. Hybrid Retrieval

`rag/retrieval/keyword_retriever.py` provides local token/term-frequency retrieval. `rag/retrieval/hybrid_retriever.py` combines keyword and vector scores after min-max normalization; default weights are 0.5 keyword and 0.5 vector. Both components support `top_k` and metadata filters. Hybrid retrieval has unit tests but is not configured in the production `AssistantService` wiring, which constructs a vector-mode `RAGService`.

### 12. Reranking

`rag/retrieval/reranker.py` implements a local lexical reranker. It combines query/document token overlap, term frequency, and a contribution from the previous score, then orders deterministically with a chunk-ID tie-break. It preserves candidate objects and metadata. The production `RAGService` uses this reranker by default after retrieval.

### 13. Context Assembly

`rag/generation/context_builder.py` defines `ContextBuilder`. It de-duplicates by chunk ID, caps the selected chunks, and formats policy ID, chunk ID, source, other metadata, and text. It requires policy ID and source metadata. Production context is limited to five chunks by default.

### 14. Grounded Prompting

`rag/generation/prompts.py` provides configurable `PromptTemplate`, `GroundedPromptFactory`, and `build_grounded_prompt()`. Its instructions tell a downstream model to rely only on supplied context, avoid unsupported claims, state when context is insufficient, cite sources, and distinguish policy requirements from explanation. Prompt construction has unit tests.

The current `RAGService` does not call this prompt factory. It passes system instructions, retrieved chunk text, and the query to the provider interface. Therefore the prompt template is implemented but not integrated into production generation.

### 15. Structured Responses

`rag/service.py` returns `RAGResponse` with `answer`, `supported`, `explanation`, `sources`, `context`, and `retrieved_chunks`. The FastAPI contract in `app/schemas/assistant.py` exposes `answer`, `supported`, `sources`, and `retrieval_metadata`.

### 16. Citation and Source Tracking

Retrieved chunks carry `policy_id` and `source` metadata. `RAGService` derives a de-duplicated list of source references from accepted, reranked chunks, formatted as `source (policy_id)` when a policy ID exists. The API returns this list separately from answer text and returns no sources on refusal. There is no separate parser that extracts citations from generated answer text; the API provider is currently a mock.

### 17. Refusal / No-Answer Behavior

`RAGService` defaults to `min_similarity_score=0.5`. It refuses before generation if retrieval is empty, no result meets the threshold, context building fails, or context is empty. It also refuses if the provider returns empty text. A refusal has `supported=false`, empty answer, and empty sources. Unit tests cover supported, partial, unsupported, empty-result, and below-threshold cases; the threshold is not adjusted by those tests.

### 18. `/assistant/query` API

`POST /assistant/query` is implemented by `app/api/routes/assistant.py` and registered in `app/main.py`. Request validation in `AssistantQueryRequest` requires a trimmed non-empty question of at most 2,000 characters; `top_k`, when supplied, must be between 1 and 20. Category, policy ID, and status are optional. The route is independent of the case database session and obtains `AssistantService` through FastAPI dependency injection.

The service logs question length, filters, top-k, support state, and source count as structured JSON; it does not log the full question or answer at info level. Existing exception handlers return the shared `{"error":{"code":...,"message":...}}` envelope for application errors.

### 19. Evaluation Dataset

`data/evaluation/rag_evaluation_dataset.json` contains 12 deterministic questions: 3 direct factual, 2 procedure, 2 metadata-filtered, 2 policy-specific, 2 unsupported, and 1 ambiguous. Each record includes a question ID, expected evidence, expected support state, category, optional filters, and expected policy ID when applicable.

### 20. Retrieval Configuration Comparison

`evaluation/evaluate_retrieval.py` compares:

| Configuration | Retrieval | Reranking | Default `top_k` |
| --- | --- | --- | --- |
| `vector` | Vector | No | 5 |
| `hybrid_reranked` | Keyword + vector | Yes | 5 |

The evaluator builds a deterministic 128-dimensional hash embedding model locally for the comparison; this is separate from the production Sentence Transformers model. It writes machine-readable results to `data/evaluation/retrieval_results.json`. The existing results file describes 44 chunks and 12 questions per configuration. This is evaluator output, not proof of production API behavior.

### 21. Quality Metrics

The evaluator records evidence hit rate, retrieval relevance, expected-policy retrieval rate, answer relevance, groundedness, citation/source coverage, refusal correctness, and latency. In the current evaluator, answer/refusal text is built deterministically from lexical query overlap with retrieved chunks; it is not produced by the API’s LLM provider or an external model. Latency covers retrieval and optional reranking, not corpus loading/index construction.

The existing `retrieval_results.json` records these averages:

| Configuration | Evidence hit | Retrieval relevance | Expected policy retrieval | Answer relevance | Groundedness | Citation coverage | Refusal correctness | Average latency (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vector` | 0.1597 | 0.5333 | 0.7500 | 0.5650 | 0.9762 | 0.7500 | 0.7500 | 1.3089 |
| `hybrid_reranked` | 0.4236 | 0.6167 | 0.7500 | 0.6455 | 0.9860 | 0.7500 | 0.7500 | 6.1423 |

These numbers are reported as stored, with no winner declared. They are deterministic evaluator measurements, not LLM answer-quality measurements.

### 22. Failure Analysis

`evaluation/failure_log.md` defines eight failure categories and a template for recording observed issues. It currently says no evaluation failure records are available, so it contains no question-specific root causes or post-improvement results. The evaluator output exists separately; it includes examples where expected evidence hit rate is zero while the evaluator marks an answer supported. This is a measured evaluator outcome, not a confirmed production API failure. The failure log has not yet been reconciled with the present results file.

### 23. Testing

RAG tests are in `tests/rag/` and cover document cleaning, fixed/recursive chunking, embedding wrapper behavior with fake models, vector-store persistence, vector/keyword/hybrid retrieval, reranking, context assembly, prompt construction, and refusal behavior. `tests/test_assistant.py` covers request validation, response shape, filters, and supported/unsupported requests with stub retrieval and mock generation. `tests/test_assistant_indexing.py` covers policy-index construction with a fake embedding model and lifespan injection.

The most recent reported selected run covering cases, assistant, indexing, and RAG tests passed 84 tests. A prior full run reported 105 passed and one Spark failure before its predicate was edited; that Spark test has not been successfully rerun after the edit. Tests do not load the real Sentence Transformers model.

### 24. How to Run the RAG Pipeline

Run the evaluator without network/model downloads:

```powershell
python evaluation/evaluate_retrieval.py --top-k 5
```

It reads the local policy corpus and dataset, uses its deterministic test embedding model, and writes `data/evaluation/retrieval_results.json`.

To start the FastAPI application, use the repository’s normal command:

```powershell
python -m uvicorn app.main:app --reload
```

FastAPI lifespan loads and indexes the corpus before serving requests. Production startup requires the `sentence-transformers` dependency and availability of the configured model. The active environment has reported `ModuleNotFoundError: sentence_transformers`; successful production startup has not been verified.

### 25. Example API Request / Response

Request:

```http
POST /assistant/query
Content-Type: application/json

{
	"question": "How do I reset a password?"
}
```

The following response shape and values are asserted by `tests/test_assistant.py` using a stub retriever and mock provider; it is not an observed production-model response:

```json
{
	"answer": "Grounded password reset answer",
	"supported": true,
	"sources": ["identity-policy.md (POL-001)"],
	"retrieval_metadata": {
		"top_k_used": 5,
		"filters": {},
		"chunk_count": 1,
		"supported": true
	}
}
```

### Week 3 Completion Checklist

- [x] Local policy Markdown corpus with parsed metadata
- [x] Policy document loading and cleaning
- [x] Fixed and recursive deterministic chunkers
- [x] EmbeddingService wrapper with fake-model tests and batch support
- [x] In-memory vector store with explicit JSON save/load methods
- [x] Vector retrieval and metadata filtering
- [x] Keyword/hybrid retrieval and reranking components
- [x] Controlled source-aware context builder
- [x] Grounded prompt template and tests
- [x] RAG refusal behavior and unit tests
- [x] `/assistant/query` schema, route, service, and startup index wiring
- [x] Evaluation dataset, comparison script, results file, and failure-log framework
- [ ] Install/verify the embedding dependency and configured model in the API runtime
- [ ] Verify a successful production startup and real-model HTTP query
- [ ] Integrate a real generation provider and connect the grounded prompt to it
- [ ] Reconcile observed evaluator failures with `evaluation/failure_log.md`
- [ ] Rerun the Spark transformation test after its predicate fix