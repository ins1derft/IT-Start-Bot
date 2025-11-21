"""add publication_schedule table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4
import datetime

# revision identifiers, used by Alembic.
revision = "20241121_0005"
down_revision = "20241121_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "publication_schedule",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column("publication_type", sa.Enum(name="publication_type"), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("publication_type", name="uq_publication_schedule_type"),
    )

    # seed defaults: jobs 6h, internships/conferences 24h
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO publication_schedule (id, publication_type, interval_minutes, start_time, is_active, updated_at)
            VALUES (:id1, 'job', 360, NULL, true, now()),
                   (:id2, 'internship', 1440, NULL, true, now()),
                   (:id3, 'conference', 1440, NULL, true, now())
            """
        ),
        {
            "id1": uuid4(),
            "id2": uuid4(),
            "id3": uuid4(),
        },
    )


def downgrade() -> None:
    op.drop_table("publication_schedule")
