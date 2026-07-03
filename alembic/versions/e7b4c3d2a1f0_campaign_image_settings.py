"""campaign image settings

Revision ID: e7b4c3d2a1f0
Revises: c9a7f1a2b3c4
Create Date: 2026-07-02 08:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7b4c3d2a1f0"
down_revision: Union[str, Sequence[str], None] = "c9a7f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "learning_campaigns",
        sa.Column("auto_generate_images", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "learning_campaigns",
        sa.Column("image_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "learning_campaigns",
        sa.Column("visual_style", sa.String(length=40), nullable=False, server_default="auto"),
    )
    op.add_column(
        "learning_campaign_items",
        sa.Column("visual_hint", sa.Text(), nullable=True),
    )
    op.add_column(
        "learning_campaign_items",
        sa.Column("prompt_brief", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("learning_campaign_items", "prompt_brief")
    op.drop_column("learning_campaign_items", "visual_hint")
    op.drop_column("learning_campaigns", "visual_style")
    op.drop_column("learning_campaigns", "image_count")
    op.drop_column("learning_campaigns", "auto_generate_images")
