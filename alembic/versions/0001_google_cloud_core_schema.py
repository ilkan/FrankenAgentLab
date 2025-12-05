"""Initial Google Cloud aligned schema.

Revision ID: 0001_google_cloud_core_schema
Revises: None
Create Date: 2025-02-20 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_google_cloud_core_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create core tables."""
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("token_quota", sa.Integer(), nullable=False, default=100000),
        sa.Column("token_used", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "blueprints",
        sa.Column("id", postgresql.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("blueprint_data", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("is_public", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("clone_count", sa.Integer(), nullable=False, default=0),
        sa.Column("rating_sum", sa.Integer(), nullable=False, default=0),
        sa.Column("rating_count", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_blueprints_public", "blueprints", ["is_public"])
    op.create_index("ix_blueprints_user_id", "blueprints", ["user_id"])

    op.create_table(
        "user_api_keys",
        sa.Column("id", postgresql.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("key_name", sa.String(length=255), nullable=True),
        sa.Column("encrypted_key", sa.LargeBinary(), nullable=False),
        sa.Column("encrypted_dek", sa.LargeBinary(), nullable=False),
        sa.Column("key_last_four", sa.String(length=4), nullable=False),
        sa.Column("nonce", sa.LargeBinary(), nullable=False),
        sa.Column("kms_key_version", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
    )
    op.create_index("idx_user_api_keys_provider", "user_api_keys", ["user_id", "provider"])

    op.create_table(
        "marketplace_ratings",
        sa.Column("id", postgresql.UUID(), primary_key=True, nullable=False),
        sa.Column("blueprint_id", postgresql.UUID(), sa.ForeignKey("blueprints.id", ondelete="CASCADE")),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )
    op.create_index("idx_ratings_unique", "marketplace_ratings", ["blueprint_id", "user_id"], unique=True)

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("blueprint_id", postgresql.UUID(), sa.ForeignKey("blueprints.id", ondelete="CASCADE")),
        sa.Column("messages", sa.JSON(), nullable=False, default=list),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_sessions_last_message", "sessions", ["user_id", "last_message_at"])

    op.create_table(
        "user_activities",
        sa.Column("id", postgresql.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("activity_type", sa.String(length=128), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_user_activity_type", "user_activities", ["user_id", "activity_type"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("idx_user_activity_type", table_name="user_activities")
    op.drop_table("user_activities")
    op.drop_index("idx_sessions_last_message", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("idx_ratings_unique", table_name="marketplace_ratings")
    op.drop_table("marketplace_ratings")
    op.drop_index("idx_user_api_keys_provider", table_name="user_api_keys")
    op.drop_table("user_api_keys")
    op.drop_index("ix_blueprints_user_id", table_name="blueprints")
    op.drop_index("idx_blueprints_public", table_name="blueprints")
    op.drop_table("blueprints")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
