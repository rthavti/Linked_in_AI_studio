"""learning campaigns

Revision ID: c9a7f1a2b3c4
Revises: bf95e528eb3d
Create Date: 2026-07-02 06:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9a7f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "bf95e528eb3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("publish_time", sa.String(length=5), nullable=False),
        sa.Column("start_date", sa.String(length=10), nullable=False),
        sa.Column("auto_approve", sa.Boolean(), nullable=False),
        sa.Column("auto_publish", sa.Boolean(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("min_words", sa.Integer(), nullable=False),
        sa.Column("max_words", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_campaigns_id"), "learning_campaigns", ["id"], unique=False)
    op.create_index(op.f("ix_learning_campaigns_name"), "learning_campaigns", ["name"], unique=True)
    op.create_index(op.f("ix_learning_campaigns_status"), "learning_campaigns", ["status"], unique=False)

    op.create_table(
        "learning_campaign_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=500), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "AI",
                "DEVOPS",
                "CLOUD",
                "PYTHON",
                "DATA",
                "CAREER",
                "LINKEDIN",
                "AUTOMATION",
                "PRODUCTIVITY",
                "GENERAL",
                name="category",
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("HIGH", "MEDIUM", "LOW", name="priority"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scheduled_for", sa.TIMESTAMP(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["learning_campaigns.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_campaign_items_id"), "learning_campaign_items", ["id"], unique=False)
    op.create_index(op.f("ix_learning_campaign_items_campaign_id"), "learning_campaign_items", ["campaign_id"], unique=False)
    op.create_index(op.f("ix_learning_campaign_items_day_number"), "learning_campaign_items", ["day_number"], unique=False)
    op.create_index(op.f("ix_learning_campaign_items_status"), "learning_campaign_items", ["status"], unique=False)
    op.create_index(op.f("ix_learning_campaign_items_scheduled_for"), "learning_campaign_items", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_learning_campaign_items_topic_id"), "learning_campaign_items", ["topic_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_campaign_items_topic_id"), table_name="learning_campaign_items")
    op.drop_index(op.f("ix_learning_campaign_items_scheduled_for"), table_name="learning_campaign_items")
    op.drop_index(op.f("ix_learning_campaign_items_status"), table_name="learning_campaign_items")
    op.drop_index(op.f("ix_learning_campaign_items_day_number"), table_name="learning_campaign_items")
    op.drop_index(op.f("ix_learning_campaign_items_campaign_id"), table_name="learning_campaign_items")
    op.drop_index(op.f("ix_learning_campaign_items_id"), table_name="learning_campaign_items")
    op.drop_table("learning_campaign_items")

    op.drop_index(op.f("ix_learning_campaigns_status"), table_name="learning_campaigns")
    op.drop_index(op.f("ix_learning_campaigns_name"), table_name="learning_campaigns")
    op.drop_index(op.f("ix_learning_campaigns_id"), table_name="learning_campaigns")
    op.drop_table("learning_campaigns")
