"""initial schema

Revision ID: 20240101_0000
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20240101_0000"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- jobs -----------------------------------------------------------
    op.create_table(
        "jobs",
        sa.Column("task_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("method", sa.String(64), nullable=False),
        sa.Column("queue_strategy", sa.String(16), nullable=False),
        sa.Column("pinned_host", sa.String(255), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])

    # --- service_instances ----------------------------------------------
    op.create_table(
        "service_instances",
        sa.Column("service_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("service_model", sa.String(255), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="deploying"),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_service_instances_state", "service_instances", ["state"])

    # --- service_instance_versions --------------------------------------
    op.create_table(
        "service_instance_versions",
        sa.Column("version_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "service_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("service_instances.service_id"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("service_id", "version", name="uq_service_version"),
    )
    op.create_index("ix_service_instance_versions_service_id", "service_instance_versions", ["service_id"])

    # --- scheduled_jobs -------------------------------------------------
    op.create_table(
        "scheduled_jobs",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("method", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("trigger", sa.String(16), nullable=False),
        sa.Column(
            "trigger_args",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_scheduled_jobs_next_run_at", "scheduled_jobs", ["next_run_at"])


def downgrade() -> None:
    op.drop_table("scheduled_jobs")
    op.drop_index("ix_service_instance_versions_service_id", table_name="service_instance_versions")
    op.drop_table("service_instance_versions")
    op.drop_index("ix_service_instances_state", table_name="service_instances")
    op.drop_table("service_instances")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_table("jobs")
