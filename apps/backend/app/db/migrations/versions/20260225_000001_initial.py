"""initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260225_000001"
down_revision = None
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return _inspector().has_table(name)


def upgrade() -> None:
    # -- Enums -------------------------------------------------------
    role_enum = postgresql.ENUM("user", "contributor", "admin", name="roleenum", create_type=False)
    role_enum.create(op.get_bind(), checkfirst=True)

    doc_status_enum = postgresql.ENUM(
        "uploaded", "parsing", "chunking", "embedding", "indexed", "failed", "archived",
        name="documentstatusenum", create_type=False,
    )
    doc_status_enum.create(op.get_bind(), checkfirst=True)

    # -- users -------------------------------------------------------
    if not _has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("username", sa.String(100), nullable=False),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("display_name", sa.String(255), nullable=False),
            sa.Column("role", role_enum, nullable=False, server_default="user"),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # -- refresh_tokens ----------------------------------------------
    if not _has_table("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("user_id", sa.String(36), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("jti", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rotated_from_token_id", sa.String(36), nullable=True),
            sa.Column("user_agent", sa.String(512), nullable=True),
            sa.Column("ip_address", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["rotated_from_token_id"], ["refresh_tokens.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"])
        op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)
        op.create_index(op.f("ix_refresh_tokens_jti"), "refresh_tokens", ["jti"], unique=True)

    # -- documents ---------------------------------------------------
    if not _has_table("documents"):
        op.create_table(
            "documents",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("owner_user_id", sa.String(36), nullable=False),
            sa.Column("filename_original", sa.String(255), nullable=False),
            sa.Column("filename_stored", sa.String(255), nullable=False),
            sa.Column("file_ext", sa.String(16), nullable=False),
            sa.Column("mime_type", sa.String(255), nullable=False),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
            sa.Column("storage_path", sa.String(1024), nullable=False),
            sa.Column("status", doc_status_enum, nullable=False, server_default="uploaded"),
            sa.Column("status_message", sa.String(512), nullable=True),
            sa.Column("error_details_json", sa.JSON(), nullable=True),
            sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("indexed_chunk_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("content_hash", sa.String(128), nullable=True),
            sa.Column("visibility_scope", sa.String(64), nullable=False, server_default="workspace"),
            sa.Column("min_role", role_enum, nullable=False, server_default="user"),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("filename_stored"),
        )
        op.create_index(op.f("ix_documents_owner_user_id"), "documents", ["owner_user_id"])

    # -- document_processing_jobs ------------------------------------
    if not _has_table("document_processing_jobs"):
        op.create_table(
            "document_processing_jobs",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("document_id", sa.String(36), nullable=False),
            sa.Column("requested_by_user_id", sa.String(36), nullable=True),
            sa.Column("celery_task_id", sa.String(255), nullable=True),
            sa.Column("job_type", sa.String(64), nullable=False, server_default="ingest"),
            sa.Column("status", sa.String(64), nullable=False, server_default="queued"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_summary", sa.String(1024), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("trace_id", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_document_processing_jobs_document_id"), "document_processing_jobs", ["document_id"])
        op.create_index(op.f("ix_document_processing_jobs_requested_by_user_id"), "document_processing_jobs", ["requested_by_user_id"])
        op.create_index(op.f("ix_document_processing_jobs_celery_task_id"), "document_processing_jobs", ["celery_task_id"])

    # -- document_processing_job_events ------------------------------
    if not _has_table("document_processing_job_events"):
        op.create_table(
            "document_processing_job_events",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("job_id", sa.String(36), nullable=False),
            sa.Column("level", sa.String(32), nullable=False, server_default="info"),
            sa.Column("stage", sa.String(64), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("details_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["job_id"], ["document_processing_jobs.id"], ondelete="CASCADE"),
        )
        op.create_index(op.f("ix_document_processing_job_events_job_id"), "document_processing_job_events", ["job_id"])

    # -- chat_sessions -----------------------------------------------
    if not _has_table("chat_sessions"):
        op.create_table(
            "chat_sessions",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("user_id", sa.String(36), nullable=False),
            sa.Column("title", sa.String(255), nullable=False, server_default="New Chat"),
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index(op.f("ix_chat_sessions_user_id"), "chat_sessions", ["user_id"])

    # -- chat_messages -----------------------------------------------
    if not _has_table("chat_messages"):
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("session_id", sa.String(36), nullable=False),
            sa.Column("user_id", sa.String(36), nullable=True),
            sa.Column("role", sa.String(32), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("message_index", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(64), nullable=True),
            sa.Column("provider_model_id", sa.String(255), nullable=True),
            sa.Column("model_category", sa.String(16), nullable=True),
            sa.Column("answer_mode", sa.String(64), nullable=True),
            sa.Column("citations_json", sa.JSON(), nullable=True),
            sa.Column("retrieval_metadata_json", sa.JSON(), nullable=True),
            sa.Column("token_usage_json", sa.JSON(), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="ok"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"])
        op.create_index(op.f("ix_chat_messages_user_id"), "chat_messages", ["user_id"])

    # -- evaluation_datasets -----------------------------------------
    if not _has_table("evaluation_datasets"):
        op.create_table(
            "evaluation_datasets",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source_format", sa.String(32), nullable=False, server_default="json"),
            sa.Column("content_hash", sa.String(128), nullable=True),
            sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("tags_json", sa.JSON(), nullable=True),
            sa.Column("created_by_user_id", sa.String(36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_evaluation_datasets_name"), "evaluation_datasets", ["name"])

    # -- evaluation_dataset_items ------------------------------------
    if not _has_table("evaluation_dataset_items"):
        op.create_table(
            "evaluation_dataset_items",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=False),
            sa.Column("case_key", sa.String(255), nullable=False),
            sa.Column("question", sa.Text(), nullable=False),
            sa.Column("expected_answer", sa.Text(), nullable=True),
            sa.Column("expected_sources_json", sa.JSON(), nullable=True),
            sa.Column("expects_refusal", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("tags_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["dataset_id"], ["evaluation_datasets.id"], ondelete="CASCADE"),
        )
        op.create_index(op.f("ix_evaluation_dataset_items_dataset_id"), "evaluation_dataset_items", ["dataset_id"])
        op.create_index(op.f("ix_evaluation_dataset_items_case_key"), "evaluation_dataset_items", ["case_key"])

    # -- evaluation_runs ---------------------------------------------
    if not _has_table("evaluation_runs"):
        op.create_table(
            "evaluation_runs",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("dataset_version", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
            sa.Column("provider", sa.String(64), nullable=False),
            sa.Column("model_category", sa.String(16), nullable=False),
            sa.Column("resolved_model_id", sa.String(255), nullable=True),
            sa.Column("config_snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("llama_stack_eval_used", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("started_by_user_id", sa.String(36), nullable=True),
            sa.Column("started_at", sa.String(64), nullable=True),
            sa.Column("finished_at", sa.String(64), nullable=True),
            sa.Column("error_summary", sa.String(1024), nullable=True),
            sa.Column("trace_id", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["dataset_id"], ["evaluation_datasets.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["started_by_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_evaluation_runs_dataset_id"), "evaluation_runs", ["dataset_id"])

    # -- evaluation_run_items ----------------------------------------
    if not _has_table("evaluation_run_items"):
        op.create_table(
            "evaluation_run_items",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("run_id", sa.String(36), nullable=False),
            sa.Column("dataset_item_id", sa.String(36), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
            sa.Column("question", sa.Text(), nullable=False),
            sa.Column("expected_answer_snapshot", sa.Text(), nullable=True),
            sa.Column("retrieved_chunks_json", sa.JSON(), nullable=True),
            sa.Column("answer_text", sa.Text(), nullable=True),
            sa.Column("citations_json", sa.JSON(), nullable=True),
            sa.Column("metrics_json", sa.JSON(), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column("token_usage_json", sa.JSON(), nullable=True),
            sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
            sa.Column("error_details_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["dataset_item_id"], ["evaluation_dataset_items.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_evaluation_run_items_run_id"), "evaluation_run_items", ["run_id"])

    # -- evaluation_metrics_summary ----------------------------------
    if not _has_table("evaluation_metrics_summary"):
        op.create_table(
            "evaluation_metrics_summary",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("run_id", sa.String(36), nullable=False),
            sa.Column("metrics_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("comparison_baseline_run_id", sa.String(36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        )
        op.create_index(op.f("ix_evaluation_metrics_summary_run_id"), "evaluation_metrics_summary", ["run_id"])

    # -- model_usage_logs --------------------------------------------
    if not _has_table("model_usage_logs"):
        op.create_table(
            "model_usage_logs",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("user_id", sa.String(36), nullable=True),
            sa.Column("context_type", sa.String(32), nullable=False),
            sa.Column("context_id", sa.String(36), nullable=True),
            sa.Column("provider", sa.String(64), nullable=False),
            sa.Column("model_id", sa.String(255), nullable=False),
            sa.Column("model_category", sa.String(16), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column("prompt_tokens", sa.Integer(), nullable=True),
            sa.Column("completion_tokens", sa.Integer(), nullable=True),
            sa.Column("total_tokens", sa.Integer(), nullable=True),
            sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="ok"),
            sa.Column("error_code", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_model_usage_logs_context_id"), "model_usage_logs", ["context_id"])

    # -- system_settings ---------------------------------------------
    if not _has_table("system_settings"):
        op.create_table(
            "system_settings",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("namespace", sa.String(64), nullable=False),
            sa.Column("key", sa.String(128), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("value_json", sa.JSON(), nullable=False),
            sa.Column("updated_by_user_id", sa.String(36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_system_settings_namespace"), "system_settings", ["namespace"])
        op.create_index(op.f("ix_system_settings_key"), "system_settings", ["key"])

    # -- provider_settings -------------------------------------------
    if not _has_table("provider_settings"):
        op.create_table(
            "provider_settings",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("active_provider", sa.String(64), nullable=False, server_default="openai_api"),
            sa.Column("model_mappings_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("openai_config_meta_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("validation_status_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("updated_by_user_id", sa.String(36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        )

    # -- secrets_store -----------------------------------------------
    if not _has_table("secrets_store"):
        op.create_table(
            "secrets_store",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("secret_name", sa.String(128), nullable=False),
            sa.Column("ciphertext", sa.Text(), nullable=False),
            sa.Column("key_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("masked_preview", sa.String(255), nullable=False),
            sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("updated_by_user_id", sa.String(36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("secret_name"),
        )
        op.create_index(op.f("ix_secrets_store_secret_name"), "secrets_store", ["secret_name"])

    # -- audit_logs --------------------------------------------------
    if not _has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("actor_user_id", sa.String(36), nullable=True),
            sa.Column("action_type", sa.String(128), nullable=False),
            sa.Column("entity_type", sa.String(128), nullable=False),
            sa.Column("entity_id", sa.String(36), nullable=True),
            sa.Column("before_json", sa.JSON(), nullable=True),
            sa.Column("after_json", sa.JSON(), nullable=True),
            sa.Column("result", sa.String(32), nullable=False, server_default="success"),
            sa.Column("reason", sa.String(1024), nullable=True),
            sa.Column("ip_address", sa.String(64), nullable=True),
            sa.Column("user_agent", sa.String(512), nullable=True),
            sa.Column("trace_id", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"])
        op.create_index(op.f("ix_audit_logs_action_type"), "audit_logs", ["action_type"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("secrets_store")
    op.drop_table("provider_settings")
    op.drop_table("system_settings")
    op.drop_table("model_usage_logs")
    op.drop_table("evaluation_metrics_summary")
    op.drop_table("evaluation_run_items")
    op.drop_table("evaluation_runs")
    op.drop_table("evaluation_dataset_items")
    op.drop_table("evaluation_datasets")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("document_processing_job_events")
    op.drop_table("document_processing_jobs")
    op.drop_table("documents")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    sa.Enum(name="documentstatusenum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="roleenum").drop(op.get_bind(), checkfirst=True)
