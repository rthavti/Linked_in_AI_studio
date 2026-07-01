"""commit 6 schema changes

Revision ID: bf95e528eb3d
Revises: 641df88f2dea
Create Date: 2026-07-01 11:57:32.084388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf95e528eb3d'
down_revision: Union[str, Sequence[str], None] = '641df88f2dea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "topics",
        sa.Column("media_asset_urn", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "topics",
        sa.Column("media_mime_type", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("topics", "media_mime_type")
    op.drop_column("topics", "media_asset_urn")
