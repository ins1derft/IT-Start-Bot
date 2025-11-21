"""Align parser fields, contact_info, user preferences with DB TЗ"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241121_0002"
down_revision = "20241121_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # parser type enum
    parser_type = postgresql.ENUM(
        "api_client", "website_parser", "tg_channel_parser", name="parser_type", create_type=False
    )
    parser_type.create(op.get_bind(), checkfirst=True)

    # parser table adjustments
    op.alter_column(
        "parser",
        "type",
        existing_type=sa.String(length=255),
        type_=parser_type,
        postgresql_using="type::parser_type",
    )
    op.alter_column("parser", "name", new_column_name="source_name")
    op.alter_column("parser", "interval", new_column_name="parsing_interval")
    op.alter_column(
        "parser",
        "parsing_start_time",
        existing_type=sa.Integer(),
        type_=sa.DateTime(),
        postgresql_using="to_timestamp(parsing_start_time)",
    )
    op.alter_column("parser", "enabled", new_column_name="is_active")
    op.add_column("parser", sa.Column("last_parsed_at", sa.DateTime(), nullable=True))

    # publication contact info (plain text per TЗ, alongside encrypted)
    op.add_column("publication", sa.Column("contact_info", sa.Text(), nullable=True))

    # user preferences (global)
    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["tg_user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "tag_id", name="pk_user_preferences"),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_column("publication", "contact_info")

    op.drop_column("parser", "last_parsed_at")
    op.alter_column("parser", "is_active", new_column_name="enabled")
    op.alter_column(
        "parser",
        "parsing_start_time",
        existing_type=sa.DateTime(),
        type_=sa.Integer(),
        postgresql_using="extract(epoch from parsing_start_time)",
    )
    op.alter_column("parser", "parsing_interval", new_column_name="interval")
    op.alter_column("parser", "source_name", new_column_name="name")
    op.alter_column(
        "parser",
        "type",
        existing_type=postgresql.ENUM(
            "api_client", "website_parser", "tg_channel_parser", name="parser_type"
        ),
        type_=sa.String(length=255),
    )

    parser_type = postgresql.ENUM(
        "api_client", "website_parser", "tg_channel_parser", name="parser_type"
    )
    parser_type.drop(op.get_bind(), checkfirst=True)
