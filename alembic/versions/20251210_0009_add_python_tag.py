"""
Add python language tag if missing

Revision ID: 20251210_0009
Revises: 20251209_0008
Create Date: 2025-12-10 12:40:00
"""
from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251210_0009"
down_revision = "20251209_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO tag (id, name, category)
            VALUES (:id, :name, :category)
            ON CONFLICT (name, category) DO NOTHING;
            """
        ),
        {"id": str(uuid.uuid4()), "name": "python", "category": "language"},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM tag WHERE name = :name AND category = :category;"
        ),
        {"name": "python", "category": "language"},
    )
