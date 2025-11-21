"""add deadline_notified to publication"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241121_0006"
down_revision = "20241121_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("publication", sa.Column("deadline_notified", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("publication", "deadline_notified")
