"""engagement topic configs

Revision ID: a4b5c6d7e8f9
Revises: f1a2b3c4d5e6
Create Date: 2026-07-03 17:10:00.000000
"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "engagement_settings",
        sa.Column("topic_configs_json", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("engagement_settings", "topic_configs_json")
