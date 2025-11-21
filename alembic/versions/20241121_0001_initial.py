"""initial schema aligned with db_schemes.sql"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241121_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    publication_type = postgresql.ENUM(
        "job", "internship", "conference", name="publication_type", create_type=False
    )
    publication_type.create(op.get_bind(), checkfirst=True)

    tag_category = postgresql.ENUM(
        "format",
        "occupation",
        "platform",
        "language",
        "location",
        "technology",
        "duration",
        name="tag_category",
        create_type=False,
    )
    tag_category.create(op.get_bind(), checkfirst=True)

    admin_role = postgresql.ENUM("admin", "moderator", name="admin_role", create_type=False)
    admin_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "publication",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", publication_type, nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("vacancy_created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime()),
        sa.Column("editor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_edited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_declined", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deadline_at", sa.DateTime()),
        sa.Column("contact_info_encrypted", sa.LargeBinary()),
        sa.UniqueConstraint("url", name="uq_publication_url"),
    )

    op.create_table(
        "tag",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", tag_category, nullable=False),
        sa.UniqueConstraint("name", "category", name="uq_tag_name_category"),
    )

    op.create_table(
        "tg_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        sa.Column("register_at", sa.DateTime(), nullable=False),
        sa.Column("refused_at", sa.DateTime()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tg_id", name="uq_tg_user_tg_id"),
    )

    op.create_table(
        "parser",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("executable_file_path", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("interval", sa.Integer(), nullable=False),
        sa.Column("parsing_start_time", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "admin_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", admin_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("otp_secret", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("username", name="uq_admin_username"),
    )

    op.create_table(
        "publication_tags",
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("publication_id", "tag_id", name="pk_publication_tags"),
        sa.ForeignKeyConstraint(["publication_id"], ["publication.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "tg_user_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_type", publication_type, nullable=False),
        sa.Column("deadline_reminder", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["user_id"], ["tg_user.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "publication_type", name="uq_sub_user_type"),
    )

    op.create_table(
        "parsing_result",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("parser_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("received_amount", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["parser_id"], ["parser.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "tg_user_subscription_tags",
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("subscription_id", "tag_id", name="pk_sub_tags"),
        sa.ForeignKeyConstraint(["subscription_id"], ["tg_user_subscriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
    )

    op.create_index("idx_publication_type_created_at", "publication", ["type", "created_at"], unique=False)
    op.create_index("idx_publication_tags_tag", "publication_tags", ["tag_id"], unique=False)
    op.create_index("idx_parsing_result_parser_date", "parsing_result", ["parser_id", "date"], unique=False)
    op.create_index("idx_tg_user_refused_at", "tg_user", ["refused_at"], unique=False)
    op.create_index("idx_tg_user_subscriptions_user_type", "tg_user_subscriptions", ["user_id", "publication_type"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_tg_user_subscriptions_user_type", table_name="tg_user_subscriptions")
    op.drop_index("idx_tg_user_refused_at", table_name="tg_user")
    op.drop_index("idx_parsing_result_parser_date", table_name="parsing_result")
    op.drop_index("idx_publication_tags_tag", table_name="publication_tags")
    op.drop_index("idx_publication_type_created_at", table_name="publication")
    op.drop_table("tg_user_subscription_tags")
    op.drop_table("parsing_result")
    op.drop_table("tg_user_subscriptions")
    op.drop_table("publication_tags")
    op.drop_table("admin_user")
    op.drop_table("parser")
    op.drop_table("tg_user")
    op.drop_table("tag")
    op.drop_table("publication")
    postgresql.ENUM(name="publication_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="tag_category").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="admin_role").drop(op.get_bind(), checkfirst=True)
