"""change tg_id to bigint"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241121_0007"
down_revision = "20241121_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("tg_user", "tg_id", existing_type=sa.Integer(), type_=sa.BigInteger())


def downgrade() -> None:
    op.alter_column("tg_user", "tg_id", existing_type=sa.BigInteger(), type_=sa.Integer())
