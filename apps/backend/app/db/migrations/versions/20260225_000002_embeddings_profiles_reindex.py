"""embedding profiles and reindex runs"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260225_000002"
down_revision = "20260225_000001"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return _inspector().has_table(name)


def upgrade() -> None:
    # -- embedding_profiles ------------------------------------------
    if not _has_table("embedding_profiles"):
        op.create_table(
            "embedding_profiles",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("provider", sa.String(64), nullable=False),
            sa.Column("model_id", sa.String(255), nullable=False),
            sa.Column("dimensions", sa.Integer(), nullable=False),
            sa.Column("distance_metric", sa.String(32), nullable=False, server_default="cosine"),
            sa.Column("normalize_embeddings", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("input_prefix_mode", sa.String(32), nullable=False, server_default="e5"),
            sa.Column("qdrant_collection_name", sa.String(255), nullable=False),
            sa.Column("qdrant_alias_name", sa.String(255), nullable=True, server_default="documents_chunks_active"),
            sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("validation_status_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_by_user_id", sa.String(36), nullable=True),
            sa.Column("updated_by_user_id", sa.String(36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_embedding_profiles_name"), "embedding_profiles", ["name"])
        op.create_index(op.f("ix_embedding_profiles_provider"), "embedding_profiles", ["provider"])
        op.create_index(op.f("ix_embedding_profiles_status"), "embedding_profiles", ["status"])
        op.create_index(op.f("ix_embedding_profiles_is_active"), "embedding_profiles", ["is_active"])
        op.create_index(op.f("ix_embedding_profiles_created_by_user_id"), "embedding_profiles", ["created_by_user_id"])
        op.create_index(op.f("ix_embedding_profiles_updated_by_user_id"), "embedding_profiles", ["updated_by_user_id"])

    # -- embedding_reindex_runs --------------------------------------
    if not _has_table("embedding_reindex_runs"):
        op.create_table(
            "embedding_reindex_runs",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("target_embedding_profile_id", sa.String(36), nullable=False),
            sa.Column("source_embedding_profile_id", sa.String(36), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
            sa.Column("scope_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("qdrant_staging_collection", sa.String(255), nullable=False),
            sa.Column("started_by_user_id", sa.String(36), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("applied_by_user_id", sa.String(36), nullable=True),
            sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("summary_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("drift_detected_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_summary", sa.String(1024), nullable=True),
            sa.Column("trace_id", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["target_embedding_profile_id"], ["embedding_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_embedding_profile_id"], ["embedding_profiles.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["started_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["applied_by_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index(op.f("ix_embedding_reindex_runs_target_embedding_profile_id"), "embedding_reindex_runs", ["target_embedding_profile_id"])
        op.create_index(op.f("ix_embedding_reindex_runs_source_embedding_profile_id"), "embedding_reindex_runs", ["source_embedding_profile_id"])
        op.create_index(op.f("ix_embedding_reindex_runs_status"), "embedding_reindex_runs", ["status"])
        op.create_index(op.f("ix_embedding_reindex_runs_started_by_user_id"), "embedding_reindex_runs", ["started_by_user_id"])
        op.create_index(op.f("ix_embedding_reindex_runs_applied_by_user_id"), "embedding_reindex_runs", ["applied_by_user_id"])

    # -- embedding_reindex_run_items ---------------------------------
    if not _has_table("embedding_reindex_run_items"):
        op.create_table(
            "embedding_reindex_run_items",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("run_id", sa.String(36), nullable=False),
            sa.Column("document_id", sa.String(36), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("document_content_hash_snapshot", sa.String(128), nullable=True),
            sa.Column("indexed_chunk_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_summary", sa.String(1024), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_seen_document_updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("needs_catchup", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("processing_log_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["run_id"], ["embedding_reindex_runs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        )
        op.create_index(op.f("ix_embedding_reindex_run_items_run_id"), "embedding_reindex_run_items", ["run_id"])
        op.create_index(op.f("ix_embedding_reindex_run_items_document_id"), "embedding_reindex_run_items", ["document_id"])
        op.create_index(op.f("ix_embedding_reindex_run_items_status"), "embedding_reindex_run_items", ["status"])


def downgrade() -> None:
    op.drop_table("embedding_reindex_run_items")
    op.drop_table("embedding_reindex_runs")
    op.drop_table("embedding_profiles")
