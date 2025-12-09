"""add contest publication type"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = "20251209_0008"
down_revision = "20241121_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum value
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE publication_type ADD VALUE IF NOT EXISTS 'contest';")

    # Seed default schedule for contests (once per day, no start offset)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO publication_schedule (id, publication_type, interval_minutes, start_time, is_active, updated_at)
            VALUES (:id, 'contest', 1440, NULL, true, now())
            ON CONFLICT (publication_type) DO NOTHING;
            """
        ),
        {"id": uuid4()},
    )


def downgrade() -> None:
    # Remove contest rows to allow type recreation without the value
    op.execute("DELETE FROM publication WHERE type = 'contest';")
    op.execute("DELETE FROM tg_user_subscriptions WHERE publication_type = 'contest';")
    op.execute("DELETE FROM publication_schedule WHERE publication_type = 'contest';")

    # Recreate enum without contest
    op.execute("ALTER TYPE publication_type RENAME TO publication_type_old;")
    op.execute("CREATE TYPE publication_type AS ENUM ('job', 'internship', 'conference');")

    tables_and_columns = [
        ("publication", "type"),
        ("tg_user_subscriptions", "publication_type"),
        ("publication_schedule", "publication_type"),
    ]

    for table, column in tables_and_columns:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE publication_type USING {column}::text::publication_type;"
        )

    op.execute("DROP TYPE publication_type_old;")
