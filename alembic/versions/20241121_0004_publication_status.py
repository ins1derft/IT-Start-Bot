"""add publication status and decline reason"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241121_0004"
down_revision = "20241121_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status_enum = postgresql.ENUM("new", "declined", "ready", "sent", name="publication_status", create_type=False)
    status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("publication", sa.Column("status", status_enum, nullable=False, server_default="new"))
    op.add_column("publication", sa.Column("decline_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("publication", "decline_reason")
    op.drop_column("publication", "status")
    postgresql.ENUM(name="publication_status").drop(op.get_bind(), checkfirst=True)
