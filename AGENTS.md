# AGENTS.md — Long-Term Memory for Claude Code

> Read this file at the start of every session. IDs are stable references for this project.
> This file is your long term memory, use it for everything what you think that is necesary to remeber.

---

## META

- **ID:** PROJ-001
- **Project:** OpenRAG
- **Purpose:** Proof-of-Concept self-hosted RAG chatbot for internal document Q&A
- **License:** GNU GPL v3
- **Status:** PoC / MVP — OpenAI-only runtime
- **Working dir:** `/Users/mnebehay/Documents/Code/OpenRAG`

---

## TECH STACK

| ID | Layer | Technology |
|----|-------|-----------|
| STACK-001 | Frontend | React 18.3, TypeScript 5.6, Vite 5.4, React Router v6, Zustand 5, TanStack Query v5, Tailwind CSS 3.4, Zod 3.23, React Hook Form 7.53 |
| STACK-002 | Backend | Python 3.12+, FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.x, Alembic, Uvicorn |
| STACK-003 | Database | PostgreSQL 16 (relational metadata), Qdrant v1.13.4 (vector index), Redis 7 (Celery broker + result cache) |
| STACK-004 | AI Runtime | OpenAI API only — gpt-4o-mini (default chat), text-embedding-3-small (default embeddings) |
| STACK-005 | Workers | Celery (ingestion, evals, reindexing queues), Celery Beat (scheduler) |
| STACK-006 | Auth | JWT (memory-side) + HttpOnly cookie refresh token, argon2 password hashing, Fernet encryption for secrets |
| STACK-007 | Observability | OpenTelemetry (traces → Jaeger), Prometheus (metrics), Grafana (dashboards), Loki + Promtail (logs) |
| STACK-008 | Testing | pytest + pytest-asyncio (backend), vitest (frontend), ruff (linting) |
| STACK-009 | Infra | Docker + Docker Compose, PowerShell helper scripts |

---

## DIRECTORY STRUCTURE

| ID | Path | Description |
|----|------|-------------|
| DIR-001 | `apps/backend/` | FastAPI application (Python, 107+ files) |
| DIR-002 | `apps/backend/app/api/` | REST route controllers |
| DIR-003 | `apps/backend/app/core/` | Config, security, JWT, crypto, logging, telemetry, rate limiting |
| DIR-004 | `apps/backend/app/db/` | SQLAlchemy models, Alembic migrations, session factory |
| DIR-005 | `apps/backend/app/providers/` | AI provider abstraction (interfaces + OpenAI impls) |
| DIR-006 | `apps/backend/app/rag/` | Parsers, chunker, prompt builder, citations |
| DIR-007 | `apps/backend/app/schemas/` | Pydantic request/response models |
| DIR-008 | `apps/backend/app/services/` | Business logic (22 service modules) |
| DIR-009 | `apps/backend/app/telemetry/` | OTel metric helpers, span context |
| DIR-010 | `apps/backend/app/workers/` | Celery task definitions |
| DIR-011 | `apps/backend/app/tests/` | Unit + integration tests |
| DIR-012 | `apps/frontend/src/` | React SPA source (43+ TypeScript files) |
| DIR-013 | `apps/frontend/src/api/` | API client wrapper |
| DIR-014 | `apps/frontend/src/components/` | Shared React components |
| DIR-015 | `apps/frontend/src/features/` | Feature-scoped logic (auth, chat, admin, evals, etc.) |
| DIR-016 | `apps/frontend/src/pages/` | Page-level components |
| DIR-017 | `apps/frontend/src/store/` | Zustand state stores |
| DIR-018 | `infra/compose/` | Docker Compose files (dev + prod-like) |
| DIR-019 | `infra/grafana/` | Grafana dashboard provisioning |
| DIR-020 | `infra/otel/` | OTel collector config |
| DIR-021 | `infra/prometheus/` | Prometheus config |
| DIR-022 | `docs/` | Architecture, RAG pipeline, RBAC, secrets, telemetry, evals docs |
| DIR-023 | `scripts/` | PowerShell dev helper scripts |
| DIR-024 | `data/uploads/` | Volume-mounted user-uploaded files |
| DIR-025 | `samples/` | Example documents + eval datasets |

---

## KEY FILES

| ID | File | Role |
|----|------|------|
| FILE-001 | `apps/backend/app/main.py` | FastAPI app entry point |
| FILE-002 | `apps/backend/app/core/config.py` | Pydantic Settings — all env var loading |
| FILE-003 | `apps/backend/app/core/security.py` | Password hashing, token generation, secret masking |
| FILE-004 | `apps/backend/app/core/jwt.py` | JWT encode/decode |
| FILE-005 | `apps/backend/app/core/crypto.py` | Fernet encryption for secrets at rest |
| FILE-006 | `apps/backend/app/services/chat_service.py` | Core RAG ask logic |
| FILE-007 | `apps/backend/app/services/ingestion_service.py` | Document parsing → chunking → embedding → Qdrant |
| FILE-008 | `apps/backend/app/services/retrieval_service.py` | Qdrant vector search |
| FILE-009 | `apps/backend/app/services/embedding_provider_service.py` | Embedding profile + provider management |
| FILE-010 | `apps/backend/app/services/evaluation_service.py` | Eval dataset/run management |
| FILE-011 | `apps/backend/app/services/secrets_service.py` | Encrypted key storage/retrieval |
| FILE-012 | `apps/backend/app/providers/inference/openai_provider.py` | OpenAI chat completions |
| FILE-013 | `apps/backend/app/providers/embeddings/openai_embedding_provider.py` | OpenAI embeddings |
| FILE-014 | `apps/backend/app/rag/parsers/document_parser.py` | Parse PDF, DOCX, TXT, MD |
| FILE-015 | `apps/backend/app/rag/chunking/recursive_chunker.py` | Recursive separator-aware chunker |
| FILE-016 | `apps/backend/app/rag/prompts/prompt_builder.py` | RAG context + system prompt assembly |
| FILE-017 | `apps/backend/app/rag/citations/citation_utils.py` | Citation extraction from retrieval results |
| FILE-018 | `apps/backend/app/workers/celery_app.py` | Celery app init |
| FILE-019 | `apps/backend/app/workers/tasks_ingestion.py` | Celery ingestion task |
| FILE-020 | `apps/backend/app/workers/tasks_evals.py` | Celery eval run task |
| FILE-021 | `apps/backend/app/db/migrations/versions/` | Alembic migrations (4 versions) |
| FILE-022 | `apps/backend/pyproject.toml` | Python dependencies |
| FILE-023 | `apps/frontend/package.json` | npm dependencies |
| FILE-024 | `apps/frontend/src/api/client.ts` | API client with JWT + base URL handling |
| FILE-025 | `infra/compose/compose.yaml` | Dev Docker Compose (6–11 services) |
| FILE-026 | `.env.example` | Root environment template |
| FILE-027 | `apps/backend/.env.example.backend` | Backend-only env template |
| FILE-028 | `docs/architecture.md` | System topology and layering |
| FILE-029 | `docs/rag-pipeline.md` | Ingestion, chunking, retrieval flow |
| FILE-030 | `docs/rbac.md` | Role-based access control docs |
| FILE-031 | `docs/secrets-management.md` | Encryption & key rotation docs |
| FILE-032 | `docs/evaluation-framework.md` | Eval datasets, runs, metrics |

---

## DATABASE MODELS

| ID | Model | Table | Key Fields |
|----|-------|-------|-----------|
| DB-001 | User | `user` | id, username, email, hashed_password, role (user/contributor/admin), is_active |
| DB-002 | RefreshToken | `refresh_token` | id, user_id, token_hash, expires_at |
| DB-003 | Document | `document` | id, owner_id, project_id, filename, file_size, status (uploaded/processing/indexed/failed) |
| DB-004 | DocumentProcessingJob | `document_processing_job` | id, document_id, status (queued/processing/completed/failed), progress_json |
| DB-005 | DocumentProcessingJobEvent | `document_processing_job_event` | id, job_id, level (info/warning/error), stage, message |
| DB-006 | ChatSession | `chat_session` | id, user_id, project_id, title, is_archived, last_message_at |
| DB-007 | ChatMessage | `chat_message` | id, session_id, role (user/assistant), content, provider, model_id, answer_mode, citations_json, retrieval_metadata_json, token_usage_json, latency_ms |
| DB-008 | Project | `project` | id, name, owner_id, is_active |
| DB-009 | ProjectMembership | `project_membership` | id, project_id, user_id, role (viewer/editor/admin) |
| DB-010 | EmbeddingProfile | `embedding_profile` | id, name, provider, model_id, dimension, is_active |
| DB-011 | EmbeddingReindexRun | `embedding_reindex_run` | id, source_profile_id, target_profile_id, collection_name, status |
| DB-012 | SystemSetting | `system_setting` | id, namespace, key, value_json, description |
| DB-013 | ProviderSetting | `provider_setting` | id, provider_name, config_json |
| DB-014 | SecretStore | `secret_store` | id, secret_type (openai_api_key), ciphertext, masked_preview, rotation_metadata_json |
| DB-015 | AuditLog | `audit_log` | id, user_id, action, resource_type, resource_id, status, detail_json, timestamp |
| DB-016 | EvaluationDataset | `evaluation_dataset` | id, name, owner_id, item_count |
| DB-017 | EvaluationDatasetItem | `evaluation_dataset_item` | id, dataset_id, question, expected_answer, expected_sources_json, refusal_expected, tags_json |
| DB-018 | EvaluationRun | `evaluation_run` | id, dataset_id, provider, model_id, config_json, status, started_at, completed_at |
| DB-019 | EvaluationRunItem | `evaluation_run_item` | id, run_id, dataset_item_id, answer, citations_json, metrics_json, latency_ms |
| DB-020 | EvaluationMetricsSummary | `evaluation_metrics_summary` | id, run_id, metric_name, value, aggregation |
| DB-021 | ModelUsageLog | `model_usage_log` | id, session_id, message_id, provider, model_id, input_tokens, output_tokens |

---

## API ROUTES

All routes prefixed `/api/v1`

| ID | Method | Path | Description |
|----|--------|------|-------------|
| API-001 | POST | `/auth/login` | Login (username + password) |
| API-002 | POST | `/auth/refresh` | Refresh access token via HttpOnly cookie |
| API-003 | POST | `/auth/logout` | Clear refresh token |
| API-004 | GET | `/users` | List users (admin) |
| API-005 | POST | `/users` | Create user (admin) |
| API-006 | PUT | `/users/{user_id}` | Update user role/active status |
| API-007 | POST | `/users/{user_id}/reset-password` | Reset password |
| API-008 | GET | `/projects` | List projects (filtered by membership) |
| API-009 | POST | `/projects` | Create project |
| API-010 | POST | `/projects/{project_id}/members` | Add member |
| API-011 | DELETE | `/projects/{project_id}/members/{user_id}` | Remove member |
| API-012 | POST | `/documents/upload` | Upload document → creates processing job |
| API-013 | GET | `/documents` | List documents |
| API-014 | DELETE | `/documents/{document_id}` | Delete document |
| API-015 | POST | `/documents/{document_id}/reprocess` | Requeue for ingestion |
| API-016 | GET | `/ingestion/jobs/{job_id}` | Get processing job status |
| API-017 | GET | `/ingestion/jobs/{job_id}/events` | Get job event log |
| API-018 | POST | `/chat/ask` | Ask question (RAG) |
| API-019 | GET | `/chat/sessions` | List chat sessions |
| API-020 | GET | `/chat/sessions/{session_id}` | Get session + messages |
| API-021 | PUT | `/chat/sessions/{session_id}` | Update session (archive/title) |
| API-022 | GET | `/settings/system` | Get system settings |
| API-023 | PUT | `/settings/system` | Update system settings |
| API-024 | GET | `/admin/providers` | Get provider config |
| API-025 | PUT | `/admin/providers/active` | Switch active provider |
| API-026 | POST | `/admin/openai/key` | Set OpenAI API key (encrypted storage) |
| API-027 | POST | `/admin/openai/key/test` | Test OpenAI connectivity |
| API-028 | POST | `/admin/openai/key/rotate` | Rotate key |
| API-029 | DELETE | `/admin/openai/key` | Remove key |
| API-030 | POST | `/admin/openai/models/set` | Set chat/embedding model IDs |
| API-031 | GET | `/admin/embeddings/profiles` | List embedding profiles |
| API-032 | POST | `/admin/embeddings/reindex` | Trigger bulk reindex job |
| API-033 | POST | `/evals/datasets` | Create evaluation dataset |
| API-034 | POST | `/evals/datasets/{dataset_id}/items` | Add dataset item |
| API-035 | POST | `/evals/runs` | Trigger evaluation run |
| API-036 | GET | `/evals/runs/{run_id}` | Get run + item results |
| API-037 | GET | `/evals/compare` | Compare two runs |
| API-038 | GET | `/health/ready` | Readiness check |
| API-039 | GET | `/health/live` | Liveness check |
| API-040 | GET | `/metrics` | Prometheus metrics |

---

## CORE WORKFLOWS

| ID | Workflow | Summary |
|----|----------|---------|
| FLOW-001 | **Chat (RAG Ask)** | `POST /chat/ask` → ChatService.ask() → RetrievalService (Qdrant vector search) → citations → prompt builder → OpenAI completion → infer answer_mode → persist ChatMessage → return answer + citations |
| FLOW-002 | **Document Ingestion** | Upload → save file to volume → create ProcessingJob (queued) → Celery task → parse (pdf/docx/txt/md) → chunk (recursive separator) → embed (OpenAI) → upsert to Qdrant → mark indexed/failed |
| FLOW-003 | **Evaluation** | Create dataset + items → trigger run → Celery worker → per-item: RAG ask → compute metrics (hit@k, recall, citation presence, refusal correctness) → aggregate → EvaluationMetricsSummary |
| FLOW-004 | **Auth** | Login → JWT (in memory) + refresh token (HttpOnly cookie) → refresh via cookie → backend validates at every protected endpoint → RBAC enforced via `require_roles` dependency |
| FLOW-005 | **Secrets** | Admin submits key → backend encrypts with Fernet (APP_SECRETS_MASTER_KEY) → stored as ciphertext in secret_store → decrypted at runtime for API calls → frontend only sees masked preview |
| FLOW-006 | **Embedding Reindex** | Admin changes model → trigger reindex → Celery worker re-embeds all documents → upserts to target Qdrant collection → updates document pointers |

---

## ENVIRONMENT VARIABLES

| ID | Variable | Description |
|----|----------|-------------|
| ENV-001 | `APP_JWT_SECRET` | JWT signing secret |
| ENV-002 | `APP_SECRETS_MASTER_KEY` | Fernet key for encrypting OpenAI API key at rest |
| ENV-003 | `DATABASE_URL` | PostgreSQL connection string |
| ENV-004 | `REDIS_URL` | Redis connection string |
| ENV-005 | `QDRANT_HOST` / `QDRANT_PORT` | Qdrant vector DB connection |
| ENV-006 | `QDRANT_COLLECTION` | Vector collection name |
| ENV-007 | `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | Chunking config |
| ENV-008 | `RAG_TOP_K` / `RAG_MIN_SCORE` | Retrieval config |
| ENV-009 | `RAG_ANSWER_BEHAVIOR_MODE` | `strict_rag_only` or `hybrid_with_disclaimer` |
| ENV-010 | `OPENAI_CHAT_MODEL` | Default: `gpt-4o-mini` |
| ENV-011 | `OPENAI_EMBEDDING_MODEL` | Default: `text-embedding-3-small` |
| ENV-012 | `APP_BOOTSTRAP_ADMIN_USERNAME` | Initial admin user credentials |
| ENV-013 | `VITE_API_BASE_URL` | Frontend → backend API URL |
| ENV-014 | `OTEL_ENABLED` | Enable OTel observability stack |

---

## ROLES & RBAC

| ID | Role | Permissions |
|----|------|------------|
| RBAC-001 | `user` | Chat, view own sessions and documents |
| RBAC-002 | `contributor` | Upload documents, manage own projects |
| RBAC-003 | `admin` | Full access — user management, provider settings, eval runs, reindexing, key management |

---

## LOCAL DEVELOPMENT

| ID | Action | Command |
|----|--------|---------|
| DEV-001 | Build | `./scripts/dev-build.ps1` |
| DEV-002 | Start | `./scripts/dev-start.ps1` |
| DEV-003 | Stop | `./scripts/dev-stop.ps1` |
| DEV-004 | Health check | `./scripts/dev-health.ps1` |
| DEV-005 | Logs | `./scripts/dev-logs.ps1` |
| DEV-006 | Trigger eval run | `./scripts/dev-eval-run.ps1` |
| DEV-007 | Frontend | `http://localhost:5173` |
| DEV-008 | Backend API | `http://localhost:8000` |
| DEV-009 | OpenAPI Docs | `http://localhost:8000/docs` |
| DEV-010 | Grafana | `http://localhost:3000` |
| DEV-011 | Jaeger | `http://localhost:16686` |
| DEV-012 | Prometheus | `http://localhost:9090` |
| DEV-013 | Generate Fernet key | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

---

## PATTERNS & CONVENTIONS

| ID | Pattern | Description |
|----|---------|-------------|
| PAT-001 | **Backend layering** | Routes (thin) → Services (business logic) → Providers (AI abstraction) → DB/Vector store |
| PAT-002 | **Dependency injection** | FastAPI: `get_db()`, `get_current_user()`, `require_roles()`, `enforce_rate_limit()` |
| PAT-003 | **Provider abstraction** | `InferenceProvider`, `EmbeddingProvider`, `EvaluationProvider` interfaces in `providers/interfaces.py` |
| PAT-004 | **Celery queues** | Named queues: `ingestion`, `evals`, `default` |
| PAT-005 | **Audit logging** | All admin actions logged to `audit_log` table with JSON detail |
| PAT-006 | **Structured logging** | JSON format, contextual extras, redaction for secrets |
| PAT-007 | **Error handling** | `HTTPException` for API; handlers in `api/errors/handlers.py` |
| PAT-008 | **Frontend state** | JWT in memory (not localStorage), Zustand for UI, TanStack Query for server state |
| PAT-009 | **Migrations** | Alembic auto-run on backend startup; files in `db/migrations/versions/` |
| PAT-010 | **Security** | Never expose raw secrets; frontend never calls OpenAI directly |

---

## SCOPE & KNOWN LIMITATIONS

| ID | Item | Note |
|----|------|------|
| SCOPE-001 | **AI Provider** | OpenAI-only at runtime; multi-provider designed but not active |
| SCOPE-002 | **Local embeddings** | Architecture supports local models (design present, not default) |
| SCOPE-003 | **OCR** | `PDF_OCR_ENABLED` env var exists; not fully implemented |
| SCOPE-004 | **Deployment** | Dev compose + prod-like compose overlay available |
| SCOPE-005 | **Document types** | Supported: PDF, DOCX, TXT, MD |

---

## CHANGELOG

| ID | Date | Phase | Change |
|----|------|-------|--------|
| CHG-001 | 2026-03-19 | Phase 1 | **F5/U10:** Added `validate_fernet_key()` in `app/core/crypto.py` — validates APP_SECRETS_MASTER_KEY format (base64, 32 bytes, Fernet-compatible) at startup in `get_settings()` and in `SecretsCipher.__init__()` |
| CHG-002 | 2026-03-19 | Phase 1 | **F2/U1:** Created `apps/backend/entrypoint.sh` — unified entrypoint that validates env, runs Alembic migrations (api mode), then starts uvicorn/celery worker/celery beat based on mode arg |
| CHG-003 | 2026-03-19 | Phase 1 | **F2/U1:** Rewrote `apps/backend/Dockerfile` — separate `dev` (with dev deps) and `runtime` (prod deps only) stages, both using `entrypoint.sh` as ENTRYPOINT |
| CHG-004 | 2026-03-19 | Phase 1 | **F1/U2:** Created `apps/frontend/nginx.conf` — SPA fallback (`try_files $uri /index.html`), gzip, security headers, long cache for Vite hashed assets |
| CHG-005 | 2026-03-19 | Phase 1 | **F1/U2:** Updated `apps/frontend/Dockerfile` — runtime stage copies nginx.conf, also copies `package-lock.json*` for deterministic installs |
| CHG-006 | 2026-03-19 | Phase 1 | **U3:** Created `.dockerignore` for both `apps/backend/` and `apps/frontend/` |
| CHG-007 | 2026-03-19 | Phase 1 | **F3/U7:** Rewrote `migrations/20260225_000001_initial.py` — replaced `Base.metadata.create_all()` with explicit idempotent `op.create_table()` for all 16 initial tables; downgrade now drops tables individually in correct FK order |
| CHG-008 | 2026-03-19 | Phase 1 | **F3/U7:** Rewrote `migrations/20260225_000002_embeddings_profiles_reindex.py` — same pattern, explicit `op.create_table()` for 3 embedding tables |
| CHG-009 | 2026-03-19 | Phase 1 | **F4/U8:** Rewrote `infra/compose/compose.prod-like.yaml` — now a proper override file (use with `-f compose.yaml -f compose.prod-like.yaml`), inherits all services from base, overrides build targets to `runtime`, removes source mounts, uses entrypoint commands |
| CHG-010 | 2026-03-19 | Phase 1 | Updated `infra/compose/compose.yaml` — backend/worker/scheduler now use entrypoint commands (`api-dev`, `worker`, `beat`); removed hard dependency on `otel-collector` (optional profile) |

---

## USER PREFERENCES

| ID | Preference | Note |
|----|-----------|------|
| PREF-001 | **AGENTS.md** | User requested this file be read before every interaction for long-term memory |
