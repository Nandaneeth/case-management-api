I’ll assemble this from the current workspace rather than relying on earlier conversation summaries. I’ll inspect README, app/ETL/RAG implementations, policy metadata, tests and manifests; for Git metadata I’ll read the repository metadata files directly, without invoking Git or changing the worktree.

Read 

Read 

Read 

Read 

Read , lines 1 to 240

Read , lines 241 to 421

The README documents Week 1 and Week 2 architecture, including which ETL pieces are intentionally not wired into the executable pipeline. I’m now checking the current tree against that documentation and locating the exact Week 3/RAG files, test counts, policy metadata, and non-secret Git/environment metadata so the handoff reflects code rather than README claims alone.

Read , lines 421 to 421

Read 

Read 

Read 

Read 

Read 

Read 

Read 

The current repository has added `app/dependencies.py`, assistant schemas/routes/service, RAG evaluation assets, and RAG-index startup wiring beyond the README’s documented sections. I’ll map those implementations and test names now; Git branch/remote/push status will be reported only to the extent that the checked-in metadata files directly establish it.

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Searched for regex `^\s*(async\s+)?def\s+test_` (`**/case-management-api/tests/**/*.py`), 104 results

Read 

Read 

Read 

Read 

Read 

Read 

Read 

The test tree contains 104 test functions; visible parametrization expands that count, so I’m checking all parameterized cases before reporting a collected-item count. I’m also reading current app/database/ETL/RAG configs and `.git` metadata directly; a true working-tree dirty check normally requires `git status`, which I will not run under your no-Git-operations constraint.

Read 

Read 

Searched for regex `pytest\.mark\.parametrize` (`**/case-management-api/tests/**/*.py`), 2 results

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Git metadata shows the current branch is `feature/week3-rag-assistant`; the reflog’s latest commit is the Week 2 final-changes commit followed by checkout to this branch. I won’t inspect secrets or invoke Git to determine working-tree status/push freshness. Next I’m verifying the exact RAG/provider/refusal mechanics and policy metadata for the brief.

Read 

Read 

Read 

Read 

Read 

Read 

Read 

The code confirms important Week 3 caveats: production generation is deterministic mock output, the grounded prompt template is not wired into `RAGService`, and there are two parallel generation interfaces (`base.py` and legacy `provider.py`). The vector store supports explicit JSON save/load but production builds an in-memory store on every startup. I’m verifying ETL entrypoint behavior, corpus headers, eval artifacts, and Git refs next.

Read , lines 1 to 320

Read 

Read 

Read 

Read 

Read 

Read 

Read 

The current test tree has 104 test functions and two parametrized tests; accounting for those parameter cases gives 108 collected items. There is no fresh full-suite result after the Spark predicate edit; the most recent full run recorded 105 passed and the Spark datatype failure before that edit. I’m finishing the ETL audit and checking local/remote-tracking ref metadata for the Git section.

Read 

Read , lines 1 to 16

Read , lines 1 to 16

Read , lines 1 to 16

Read , lines 1 to 16

Read , lines 1 to 16

Read 

Read 

The corpus contains five approved policies with stable IDs and metadata, and local branch `feature/week3-rag-assistant` points to the same hash as the latest Week 2 commit visible in its reflog. I’m checking whether a corresponding `origin` tracking ref exists; even if it matches, that only shows local tracking metadata, not live push status.

Read 

Read 

Read 

Read , lines 1 to 200

Read 

Read 

Read 

Read 

The local `origin/feature/week3-rag-assistant` tracking ref matches the current branch ref, but that only reflects the last fetched metadata; it cannot prove whether newer remote commits exist or whether current work was pushed. I’m doing the final code pass across retrieval scoring, ETL auxiliary layers, evaluation artifacts, and configuration to state pending work accurately.

Read 

Read , lines 115 to 271

Read 

Read 

Read 

Read 

Read 

Read 

The evaluator dataset has 12 records; the generated retrieval-results JSON is absent, and `failure_log.md` explicitly records no observed evaluation failures. I’m checking the auxiliary Spark/metadata/Bronze paths and current data/output files so the Week 2 section clearly separates executable pipeline behavior from standalone capabilities.

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

The main ETL entrypoint is confirmed as a Pandas pipeline; its Spark metadata reader/Bronze writer are standalone and `etl/layers/pipeline_layers.py` plus `etl/transform/transformer.py` are empty. I’m taking one last inventory of generated data and the pipeline’s output/checkpoint code, then I’ll provide the brief in the exact 20-section structure without changing anything.

Read 

Read 

Read 

Read 

Read 

Read 

Read , lines 300 to 398

Read 

Read 

I have enough evidence for the status and limitations; before writing, I’m verifying the remaining data-source filenames and mock policy API contract so the repository tree and ETL flow aren’t relying on assumptions. No tests or Git commands will be run.

Read 

Read 

Read 

Read 

Read 

Read 

# CASE-MANAGEMENT-API — AI HANDOFF BRIEF

## 1. Project Overview

- **Purpose:** A FastAPI customer-support case-management backend, with a separate Pandas/PySpark ETL foundation and a local-policy RAG assistant.
- **Current domain:** Customer support case management, including password resets, account access, payment failures, refunds, and service outages.
- **Architecture:** The FastAPI case endpoints follow `route → service → schema/model/database`. ETL is a separate batch pipeline. RAG has separate ingestion, preprocessing, chunking, embedding, retrieval, context, and generation modules, with an assistant API adapter in `app/`.
- **Technologies:** Python 3.11, FastAPI, Pydantic v2 and pydantic-settings, SQLAlchemy, SQLite by default, Pandas, PySpark, Sentence Transformers, pytest, Uvicorn, and Docker.

## 2. Development Progress

### Week 1 — FastAPI Backend

- **Objectives/features:** Customer-support case CRUD endpoints, validation, SQLAlchemy persistence, structured errors, and JSON logging are implemented.
- **Technical decisions:** SQLite is the default local database; routes and services are separate; request/response contracts use Pydantic.
- **Status:** Implemented and covered by `tests/test_cases.py`.
- **Pending:** README’s Week 1 API table does not document the later-added `/assistant/query` endpoint.

### Week 2 — ETL/Data Engineering

- **Objectives/features:** A Pandas pipeline reads case/reference/policy sources, profiles and validates data, rejects invalid rows, joins data, reconciles counts, writes standardized/curated outputs, and maintains an incremental checkpoint. Separate PySpark metadata extraction and transformation components exist.
- **Technical decisions:** The current executable batch path is Pandas. The separate metadata-driven Spark/Bronze components are not integrated into that path.
- **Status:** Core ETL path and tests are implemented.
- **Pending:** README identifies structured audit logging integration, wiring the metadata-driven Spark Bronze/Silver/Gold flow into the main pipeline, and making the policy API URL configurable.

### Week 3 — RAG Policy Assistant

- **Objectives/features:** Policy corpus, retrieval components, refusal behavior, evaluator assets, and `/assistant/query` are implemented.
- **Technical decisions:** Local vector retrieval uses Sentence Transformers and an in-memory vector store; generation currently uses deterministic mock output.
- **Status:** Partially complete. Production retriever construction is wired to FastAPI startup, but the active environment reports that `sentence_transformers` is missing. There is no real LLM provider, and the prompt template is not connected to production generation.
- **Pending:** Install/use the declared embedding dependency in the active environment, verify a successful production startup and end-to-end query, and decide whether to implement a real generation provider.

## 3. Repository Structure

```text
case-management-api/
├── app/
│   ├── api/routes/          cases.py, assistant.py
│   ├── core/                config.py, exceptions.py, logging.py
│   ├── db/                  database.py, models.py
│   ├── schemas/              case.py, assistant.py
│   ├── services/             case_service.py, assistant_service.py
│   ├── dependencies.py       Policy retriever/index builder
│   └── main.py              FastAPI app and lifespan
├── etl/
│   ├── audit/                audit_logger.py, checkpoint.py
│   ├── config/               case_schema.py, source_registry.py
│   ├── extract/              metadata-driven Spark reader
│   ├── ingestion/            Pandas CSV/JSON/Parquet/DB/API readers
│   ├── layers/               pipeline_layers.py (empty)
│   ├── load/                 Bronze writer
│   ├── metadata/             SQLite metadata reader
│   ├── profiling/            profiler.py
│   ├── transform/            transformer.py (empty)
│   ├── transformations/      Pandas and Spark operations
│   ├── validation/           schema, quality, reconciliation
│   └── pipeline.py           Executable Pandas ETL pipeline
├── rag/
│   ├── ingestion/            document_loader.py
│   ├── preprocessing/        cleaner.py
│   ├── chunking/             fixed_chunker.py, recursive_chunker.py
│   ├── embeddings/           embedding_service.py
│   ├── retrieval/            vector store/retrievers/reranker
│   ├── generation/           interfaces, mock providers, prompt/context
│   └── service.py            RAG orchestration/refusal
├── data/
│   ├── policies/             Five Markdown policies
│   ├── raw/                  cases.csv, policy_metadata.csv, reference_data.csv
│   ├── source/               customer_cases.csv
│   ├── standardized/         cases.parquet
│   ├── curated/              case_summary.parquet
│   ├── rejected/             cases_rejected.csv
│   ├── audit/                cases_checkpoint.json
│   ├── evaluation/           rag_evaluation_dataset.json
│   └── bronze/, silver/, gold/
├── evaluation/               evaluator and failure log
├── mock_api/                 mock policy-updates API
├── sql/                      schema.sql, metadata_schema.sql, queries.sql
├── tests/                    app, ETL, and RAG tests
├── .env.example
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md
```

Important references: README.md, requirements.txt, pytest.ini, Dockerfile, .env.example.

## 4. Week 1 — FastAPI Customer Support Backend

- **Endpoints:** `GET /health`; `POST /cases`; `GET /cases`; `GET /cases/{case_id}`; `PATCH /cases/{case_id}`. There is no delete endpoint. The additional `POST /assistant/query` endpoint is described in section 11.
- **Models:** case.py defines `CaseCreate`, `CaseUpdate`, and `CaseResponse`. Status values are `open`, `in_progress`, `resolved`, `closed`; priorities are `low`, `medium`, `high`, `critical`.
- **Database:** database.py creates a SQLAlchemy engine/session and `Base.metadata.create_all()` at startup. Default is `sqlite:///./sql/cases.db`, relative to the working directory. models.py defines the `cases` table with unique `case_number` and status/priority constraints.
- **Services:** case_service.py implements create/read/list/update, duplicate checks, and transaction rollback on integrity errors.
- **Validation:** Pydantic rejects extra fields, invalid enums, missing required fields, and invalid lengths. List pagination validates `skip >= 0`, `limit >= 1`.
- **Errors:** exceptions.py provides `CASE_NOT_FOUND`, `DUPLICATE_CASE_NUMBER`, assistant-specific codes, and a generic internal error envelope. FastAPI validation failures remain standard `422` responses.
- **Logging:** logging.py formats structured JSON to stdout. Case routes log operation events and relevant IDs/fields.
- **Tests:** `tests/test_cases.py` contains 10 test functions for health, CRUD, validation, and errors; tests use an in-memory SQLite database.
- **Configuration/current behavior:** config.py reads `DATABASE_URL` from environment/`.env`; SQLite is default. The app initializes database tables at startup.

## 5. Week 2 — ETL/Data Engineering

- **Source readers:** source_registry.py chooses a `SourceReader` for CSV, JSON, Parquet, relational database, and REST API. These readers return Pandas DataFrames. REST API reader expects a JSON array.
- **Executable pipeline:** pipeline.py defaults to `data/raw/cases.csv`, references `data/raw/reference_data.csv`, policy metadata `data/raw/policy_metadata.csv`, and `http://127.0.0.1:8001/api/policy-updates`. It writes standardized Parquet, curated Parquet, rejected CSV, and the checkpoint JSON.
- **Profiling:** profiler.py records row/column counts, dtypes, nulls, distinct/duplicate counts, string value counts, and case-domain checks. General numeric descriptive statistics are not implemented.
- **Schema validation:** case_schema.py defines column contracts. schema_validator.py validates columns/types/required values/allowed values and offers schema comparison. The pipeline fails fast on required-column/type failures; other row problems are handled as rejected records.
- **Transformations:** dataframe_operations.py implements trimming, normalization, null handling, deduplication, filtering, aggregation, priority enrichment, and ranking. The pipeline joins cases to reference and policy metadata, then policy updates.
- **Data quality/rejected records:** quality_rules.py rejects blank/missing and duplicate case numbers, invalid status/priority, missing required values, and invalid reference categories. Applicable rejection reasons are written to `data/rejected/cases_rejected.csv`.
- **Reconciliation/idempotency:** reconciliation.py verifies source rows equal accepted plus rejected and accepted equal standardized. checkpoint.py processes records newer than `last_processed_timestamp`; output merging deduplicates by `case_number` and `updated_at`.
- **Pandas/PySpark:** The main pipeline is Pandas. spark_operations.py independently summarizes latest case rows by status/priority. The blank-case-number predicate has been parenthesized as a Boolean expression after a reported Spark datatype mismatch; it has not been rerun successfully after that edit.
- **Layered design:** Raw, standardized, curated, and rejected data paths are used by the Pandas pipeline. `data/bronze/`, `data/silver/`, and `data/gold/` exist, but the main pipeline does not populate them. BronzeWriter and metadata-driven Spark extraction are standalone. `etl/layers/pipeline_layers.py` and `etl/transform/transformer.py` are empty.
- **Audit:** audit_logger.py defines JSONL audit records, but `etl.pipeline` does not call it. The active pipeline writes a timestamp checkpoint and prints a JSON `PipelineSummary`.
- **Docker:** Dockerfile uses Python 3.11.11, installs `requirements.txt` plus PyArrow, mounts `/app/data`, and runs `python -m etl.pipeline` (not Uvicorn). README says the image builds, but that was not independently tested in this inspection. The pipeline’s policy API URL is hard-coded to loopback, which complicates standalone container use.
- **Tests:** ETL coverage is in `tests/etl/` plus `tests/test_bronze_writer.py`, `tests/test_extract_reader.py`, and `tests/test_metadata_reader.py`.

## 6. Week 3 — RAG Policy Assistant

Implemented pipeline:

`data/policies/*.md → document loader → cleaner → fixed/recursive chunking → embeddings → vector store → vector/keyword/hybrid retrieval → reranking → context builder → RAGService → MockLLMProvider → POST /assistant/query`

- **Policy ingestion:** document_loader.py: `load_policy_documents()` parses sorted Markdown files and requires policy ID/name, category, version, effective date, department, status, and source.
- **Cleaning:** cleaner.py: whitespace/line-ending normalization; optional metadata extraction. Startup builder calls `clean_policy_document()`.
- **Chunking:** fixed_chunker.py: deterministic IDs, metadata, configurable chunk size/overlap. Startup uses `500` characters and `50` overlap. recursive_chunker.py is section-aware with max size/overlap; it is covered by tests but not used by production startup.
- **Embeddings:** embedding_service.py: SentenceTransformer loading, normalized single/batch embeddings, model-reported dimension validation.
- **Vector store/retriever:** vector_store.py, retriever.py: cosine search, metadata retention/filtering, explicit indexing. Details are in section 9.
- **Keyword/hybrid/reranking:** keyword_retriever.py, hybrid_retriever.py, reranker.py: local lexical retrieval, score fusion, and lexical reranking.
- **Context:** context_builder.py: de-duplicates, limits chunks, requires policy ID/source metadata, and formats source-aware text.
- **RAG orchestration:** service.py: validates queries/filters, retrieves, checks evidence scores, reranks, builds context, calls provider, and refuses when evidence is insufficient.
- **Generation prompt:** prompts.py contains a provider-neutral grounded prompt template and factory. Current production `RAGService` does not call it.
- **FastAPI integration:** dependencies.py builds the local vector index; assistant_service.py adapts it; assistant.py exposes the route.

## 7. Policy Corpus

All five Markdown policies currently present under `data/policies/` have the listed metadata fields: policy ID, policy name, category, version, effective date, department, status, and source.

| File | Policy name | ID | Category | Version | Effective date | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `account_access_policy.md` | Customer Account Access and Authorization Standard | `POL-ACC-002` | Identity and Access Management | 4.2 | 2026-03-01 | Approved |
| `password_reset_policy.md` | Customer Password Reset Standard | `POL-ACC-001` | Authentication and Access | 2.4 | 2026-01-15 | Approved |
| `payment_failure_policy.md` | Payment Failure Resolution and Retry Guidance | `POL-BILL-014` | Billing and Collections | 3.1 | 2026-02-10 | Approved |
| `refund_policy.md` | Customer Refund Eligibility and Processing Policy | `POL-CUST-027` | Customer Resolution and Billing | 1.8 | 2026-05-05 | Approved |
| `service_outage_policy.md` | Service Outage Communication and Recovery Standard | `POL-OPS-009` | Service Reliability | 5.0 | 2026-04-20 | Approved |

## 8. Embedding System

- **Implementation/package:** EmbeddingService lazily imports `SentenceTransformer` from the `sentence-transformers` package.
- **Configured model:** `sentence-transformers/all-MiniLM-L6-v2`.
- **Dimension:** Not hard-coded; queried from the loaded model using `get_sentence_embedding_dimension()`. Test doubles use dimension 4; the evaluator’s synthetic model uses dimension 128. No production dimension has been recorded by this repository.
- **Determinism/batching:** EmbeddingService normalizes vectors and supports document, query, and batch calls. Deterministic behavior is tested with fake models; the real model’s output has not been verified in the current environment.
- **Production loading:** build_policy_retriever() calls `EmbeddingService()` during FastAPI startup. After download/cache, inference runs locally; obtaining the named pretrained model may require external model-repository access.
- **Dependency:** `sentence-transformers==6.1.0` is declared in requirements.txt, but the active environment has reported `ModuleNotFoundError: sentence_transformers`. Tests inject fake models and avoid this import.

## 9. Retrieval System

- **VectorStore:** In-memory Python dictionary of chunk IDs, embedding tuples, and metadata. `save()`/`load()` support JSON persistence, but production does not call them.
- **VectorRetriever:** Calls `EmbeddingService.embed_query()` and cosine search; `index_chunks()` embeds batches and inserts into VectorStore.
- **KeywordRetriever:** Local tokenization and term-frequency/inverse-document-frequency-style scores with deterministic tie-breaking.
- **HybridRetriever:** Min-max normalizes keyword/vector scores and combines them with configurable weights; defaults are `0.5` each.
- **Reranker:** Lexical overlap/frequency score with a prior score contribution; deterministic chunk-ID tie-break; supports `top_k`.
- **Top-k:** Production default is 5; API requests can set 1–20. RAG orchestration defaults to 5.
- **Metadata filters:** Retriever/store support category, policy ID, version, status, and department. The API schema currently exposes category, policy ID, and status.
- **Threshold/refusal:** `RAGService` default minimum score is `0.5`. It refuses if there are no candidates, no candidate reaches threshold, context cannot be built, context is empty, or generation returns empty text. No RAG retrieval/refusal behavior was changed for startup wiring.
- **Persistence:** Production index is rebuilt in memory on every app-worker startup; it is not persisted or shared across workers.

## 10. Generation System

- **Current abstraction:** base.py defines frozen `GenerationRequest` with immutable `tuple[str, ...]` context, `GenerationResult`, and abstract `LLMProvider`.
- **Current API provider:** MockLLMProvider, selected by assistant_service.py when `GenerationSettings.provider == "mock"`.
- **Mock behavior:** Returns a deterministic template containing the query and context-chunk count, or a configured test response. It makes no network calls.
- **Prompt:** prompts.py instructs a provider to use only supplied policy context, cite sources, distinguish requirements from explanatory text, and refuse unsupported questions. It is tested but not wired into current API generation.
- **Grounding/refusal:** `RAGService` gates generation on retrieval scores and passes only reranked context; it cannot verify whether generated claims are semantically grounded. The API’s current mock answer is not an LLM-generated policy answer.
- **Response:** AssistantQueryResponse returns `answer`, `supported`, `sources`, and `retrieval_metadata`.
- **Legacy interface:** provider.py and mock_provider.py define a second older `TextGenerator` contract. Production uses `base.py`/`mock.py`; both interface families currently coexist.
- **Real provider:** No OpenAI, Anthropic, or other real LLM provider is implemented. Generation settings include provider/model/key/token/temperature fields, but the API builder currently supports only `mock`.

## 11. Production API Wiring

`POST /assistant/query` path:

1. AssistantQueryRequest validates a non-empty question up to 2,000 characters, optional category/policy ID/status filters, and optional `top_k` from 1 to 20.
2. assistant.py injects the request-scoped dependency, which reads the shared `AssistantService` from `request.app.state`.
3. `AssistantService.query()` builds the supplied metadata filters and calls `RAGService.answer()`.
4. `RAGService` calls the configured vector retriever, filters candidates below its threshold, reranks, builds context, then invokes `MockLLMProvider`.
5. The service returns the four-field API contract and sources formatted as `source (policy_id)` when supported; refusal responses have empty answer/sources.

At FastAPI lifespan startup, main.py initializes the SQL database, calls `build_policy_retriever()`, and stores an `AssistantService` on app state. The builder loads `data/policies/`, cleans each document, fixed-chunks it, creates `EmbeddingService`, `VectorStore`, and `VectorRetriever`, then calls `index_chunks()`. This occurs once per worker startup, not per request.

**Current blocker:** In the active environment, startup has been reported to fail because `sentence_transformers` is not installed. The dependency is listed in requirements, but a successful production startup/real-model POST has not been verified.

## 12. Testing Status

- **Current static count:** 104 test functions across 22 files; two parametrized tests expand the expected collected count to 108 items. No fresh collection/full-suite run was performed for this handoff.
- **Latest known broad run:** 105 passed and 1 failed before the Spark predicate was parenthesized. The failing test was `tests/etl/test_spark_transformations.py::test_spark_summary_filters_nulls_deduplicates_and_aggregates`, reporting a PySpark `DATATYPE_MISMATCH.BINARY_OP_DIFF_TYPES`.
- **After that run:** The length comparison was parenthesized to make it Boolean, but the Spark test was not successfully rerun. Current pass/fail status for that test is unverified.
- **Latest selected regression run:** 84 passed, 2 warnings across `tests/test_cases.py`, `tests/test_assistant.py`, `tests/test_assistant_indexing.py`, and `tests/rag/`. This did not include the Spark tests or all ETL tests.
- **Known warnings:** Starlette’s `httpx` TestClient deprecation, AnyIO `BlockingPortal` deprecation, and Pandas `is_categorical_dtype` deprecation in `etl/profiling/profiler.py` were present in earlier test output.
- **Week 1:** `tests/test_cases.py` (10 functions).
- **Week 2:** `tests/etl/` and root ETL tests (`test_bronze_writer.py`, `test_extract_reader.py`, `test_metadata_reader.py`); 25 expanded test items by source count.
- **Week 3:** `tests/rag/`, `tests/test_assistant.py`, and `tests/test_assistant_indexing.py`; 73 expanded test items by source count.
- Test configuration: pytest.ini sets `testpaths = tests`, `pythonpath = .`, and `addopts = -ra`.

## 13. Known Issues / Technical Debt

- **Missing runtime embedding package:** The active environment reports `ModuleNotFoundError` for `sentence_transformers`; affected files are embedding_service.py and startup dependencies.py. FastAPI startup fails before serving requests. `requirements.txt` already declares the package.
- **Spark fix unverified:** The pre-fix datatype mismatch was in spark_operations.py. The Boolean expression is now parenthesized, but its test was not rerun successfully; this is a verification gap, not a confirmed remaining failure.
- **Mock-only API generation:** mock.py is the only provider used by the API. Answers are deterministic placeholders, not policy answers from an LLM. This blocks a real assistant experience but not retrieval tests.
- **Prompt unused by production:** prompts.py is not called in the API generation path.
- **In-memory production index:** The vector store is rebuilt at startup and not shared/persisted. This is the implemented behavior, not an external database failure.
- **ETL gaps:** Structured `AuditLogger`, the integrated metadata-driven Spark layer flow, and configurable API URL are README-listed pending work. `etl/layers/pipeline_layers.py` and `etl/transform/transformer.py` are empty.
- **Documentation gap:** README’s endpoint list documents `/health` and `/cases` but not `/assistant/query` or the RAG startup/model requirements.
- **Evaluation results absent:** `data/evaluation/rag_evaluation_dataset.json` exists, but `data/evaluation/retrieval_results.json` does not. The failure log has no question-level observations.

## 14. Git Status

- **Branch:** `feature/week3-rag-assistant`, confirmed from `.git/HEAD`.
- **Current local ref:** `e475530e2061f64191ce4bdef448417cde52a3f0` (`week 2 final changes`).
- **Recent relevant commits in the HEAD reflog:** `fb22c27` initial FastAPI project; `8fdecb2` case-management backend; `0098358` customer-support domain; `407f9df` Week 2 ETL foundation; `f46466e` Week 2 README update; `e475530` Week 2 final changes.
- **Remote:** `origin` is configured as `https://github.com/Nandaneeth/case-management-api`; current branch tracks `origin/feature/week3-rag-assistant`.
- **Tracking ref:** The local `origin/feature/week3-rag-assistant` ref equals the current local branch ref. This is only locally stored tracking metadata and may be stale.
- **Uncommitted changes / pushed status:** Not established. You asked for Git inspection but prohibited Git operations; I read `.git` metadata only and did not run status/log/fetch/push commands. The local metadata cannot establish current worktree cleanliness or live remote state.

## 15. Environment

- **OS:** Windows.
- **Python/venv:** Python 3.11.9 and pytest 9.1.1 appear in the provided `.venv` test output; `.venv/` exists.
- **Declared key package versions:** FastAPI 0.141.1, Pydantic 2.13.5, pydantic-settings 2.15.0, SQLAlchemy 2.0.52, Pandas 3.0.5, PySpark 4.2.0, pytest 9.1.1, Uvicorn 0.52.4, and sentence-transformers 6.1.0 are in requirements.txt. These are manifest versions, not a fresh inventory of installed packages.
- **Embedding package state:** The active runtime reported `sentence_transformers` missing despite its requirements entry.
- **Java:** Java 17 was reported/located at `C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot\bin\java.exe`. Earlier environment inspection found `JAVA_HOME` pointing to a downloaded `.msi`, not the JDK directory.
- **Environment variables:** `DATABASE_URL` is the app setting documented in `.env.example`; generation settings read `PROVIDER`, `MODEL_NAME`, `API_KEY`, `MAX_TOKENS`, and `TEMPERATURE`. No secret values are included here.
- **Start API:** README command is `python -m uvicorn app.main:app --reload` from the repository root. Current startup additionally initializes and embeds the policy corpus.

## 16. Manual Verification Already Performed

- **Mocked endpoint test:** `tests/test_assistant.py::test_valid_query_without_filters_returns_expected_shape` asserts HTTP `200`, `supported=true`, `chunk_count=1`, and source `identity-policy.md (POL-001)`. Its answer is the configured mock string `Grounded password reset answer`; its retriever is a `StubRetriever`, so this does not prove production model startup or real retrieval over HTTP.
- **Unsupported endpoint test:** The mocked API test asserts empty answer/sources and `supported=false` when the stub returns no chunks.
- **Index-builder test:** `tests/test_assistant_indexing.py` uses the real loader/cleaner/chunker/VectorStore/VectorRetriever with a fake embedding model and confirms that a payment-failure query retrieves `POL-BILL-014`.
- **User-reported request before production index wiring:** A no-filter `POST /assistant/query` returned `supported=false`, empty answer/sources, and `chunk_count=0`; HTTP status was not included in that report.
- **Production POST:** No successful real-model production POST has been verified. Current startup is blocked by the reported missing `sentence_transformers` package.

## 17. Week 3 Completion Status

### DONE

- Five local policy documents with required metadata.
- Document loading, cleaning, fixed and recursive chunking.
- Embedding service interface and deterministic fake-model tests.
- In-memory vector store, vector retrieval, metadata filtering, keyword/hybrid retrieval, and local reranking.
- Controlled context builder and refusal logic.
- Grounded prompt template exists and has unit tests.
- RAG evaluator script and 12-question dataset exist.
- FastAPI assistant endpoint and startup index-building/injection code exist.
- Focused selected API/RAG tests passed (84 in the latest reported run).

### PARTIALLY DONE

- Production index construction is wired, but active environment lacks the embedding package and real-model startup has not been verified.
- Retrieval is connected to the API, but provider output is mock text.
- Prompt instructions exist but are not used by the current production generation path.
- Evaluation framework exists, but no results file has been generated.
- Spark predicate fix exists, but the formerly failing test was not rerun.

### NOT YET DONE

- Real LLM provider implementation and provider-backed policy answers.
- End-to-end HTTP verification with the real embedding model and populated production retriever.
- Persistent/shared production vector index.
- Full-suite verification after the Spark predicate edit.

## 18. Recommended Starting Point for Week 4

- Start from the current interfaces and clarify Week 4’s requested deliverable and acceptance criteria before changing code.
- The nearest unresolved production boundary is a verified startup and real-model retrieval/HTTP smoke test; the repository already has the builder and a fake-model indexing test.
- Preserve `EmbeddingService`, `VectorStore`, `VectorRetriever`, `RAGService`, `GenerationRequest`/`GenerationResult`/`LLMProvider`, and the assistant schema/route contract.
- Do not rewrite the case backend, ETL pipeline, or existing RAG retrieval components without a concrete requirement.

## 19. Important Constraints for Future AI Assistants

- Do not rewrite working components unnecessarily.
- Preserve the customer-support case-management domain.
- Prefer incremental changes and maintain tests.
- Use free/local tools where practical; avoid paid APIs unless explicitly requested.
- Do not skip tests; clearly disclose tests not run.
- Do not modify unrelated Week 1/2/3 functionality.
- Continue implementation through manual copy/paste rather than Copilot.
- Do not expose credentials from `.env` or environment variables.

## 20. Quick Start for a New AI Assistant

Before Week 4 changes, ask me to provide:

1. The exact Week 4 objective and expected deliverable.
2. Acceptance criteria, including required endpoints, data flow, or UI if applicable.
3. Whether Week 4 may alter the API contract, persistence model, or generation provider.
4. Runtime constraints: offline/local-only, model download policy, Java/Spark availability, and target deployment environment.
5. Which tests/commands I expect to pass and whether installing dependencies is permitted.
6. Any relevant current runtime output or evaluation results not already present in the repository.
7. Confirmation of scope: files/components that must remain untouched and whether Git commands are permitted.