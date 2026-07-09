"""engagement engine tables

Revision ID: f1a2b3c4d5e6
Revises: e7b4c3d2a1f0
Create Date: 2026-07-03 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e7b4c3d2a1f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "engagement_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("require_review", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("auto_post_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("posts_to_search_per_day", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("comments_per_day", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("min_reactions", sa.Integer(), nullable=False, server_default=sa.text("50")),
        sa.Column("author_cooldown_hours", sa.Integer(), nullable=False, server_default=sa.text("72")),
        sa.Column("style", sa.String(length=40), nullable=False, server_default="professional"),
        sa.Column("topics", sa.Text(), nullable=False, server_default=""),
        sa.Column("blocked_keywords", sa.Text(), nullable=False, server_default=""),
        sa.Column("own_author_identifiers", sa.Text(), nullable=False, server_default=""),
        sa.Column("run_time", sa.String(length=5), nullable=False, server_default="09:30"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_engagement_settings_id"), "engagement_settings", ["id"], unique=False)

    op.create_table(
        "engagement_comment_histories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_url", sa.String(length=1200), nullable=False),
        sa.Column("post_urn", sa.String(length=255), nullable=True),
        sa.Column("post_author", sa.String(length=255), nullable=True),
        sa.Column("post_language", sa.String(length=32), nullable=True),
        sa.Column("post_content", sa.Text(), nullable=False),
        sa.Column("post_published_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("post_reaction_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("style", sa.String(length=40), nullable=False, server_default="professional"),
        sa.Column("relevance_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("generated_comment", sa.Text(), nullable=True),
        sa.Column("posted_comment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="REVIEW_PENDING"),
        sa.Column("skip_reason", sa.Text(), nullable=True),
        sa.Column("is_company_page", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_sponsored", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_recruiter", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_repost", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("linkedin_comment_id", sa.String(length=255), nullable=True),
        sa.Column("posted_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("likes_received", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("replies_received", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_engagement_comment_histories_id"), "engagement_comment_histories", ["id"], unique=False)
    op.create_index(op.f("ix_engagement_comment_histories_post_url"), "engagement_comment_histories", ["post_url"], unique=False)
    op.create_index(op.f("ix_engagement_comment_histories_post_urn"), "engagement_comment_histories", ["post_urn"], unique=False)
    op.create_index(op.f("ix_engagement_comment_histories_post_author"), "engagement_comment_histories", ["post_author"], unique=False)
    op.create_index(op.f("ix_engagement_comment_histories_topic"), "engagement_comment_histories", ["topic"], unique=False)
    op.create_index(op.f("ix_engagement_comment_histories_status"), "engagement_comment_histories", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_engagement_comment_histories_status"), table_name="engagement_comment_histories")
    op.drop_index(op.f("ix_engagement_comment_histories_topic"), table_name="engagement_comment_histories")
    op.drop_index(op.f("ix_engagement_comment_histories_post_author"), table_name="engagement_comment_histories")
    op.drop_index(op.f("ix_engagement_comment_histories_post_urn"), table_name="engagement_comment_histories")
    op.drop_index(op.f("ix_engagement_comment_histories_post_url"), table_name="engagement_comment_histories")
    op.drop_index(op.f("ix_engagement_comment_histories_id"), table_name="engagement_comment_histories")
    op.drop_table("engagement_comment_histories")

    op.drop_index(op.f("ix_engagement_settings_id"), table_name="engagement_settings")
    op.drop_table("engagement_settings")
