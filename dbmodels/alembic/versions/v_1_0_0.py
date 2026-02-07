"""v_1_0_0

Revision ID: 74e89a8ebb2e
Revises:
Create Date: 2026-02-07 14:55:40.319553

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "74e89a8ebb2e"
down_revision = None
branch_labels = None
depends_on = None

status_enum = postgresql.ENUM("new", "queued", "done", name="status", create_type=False)


def upgrade():
    status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("email_address", sa.TEXT(), nullable=True),
        sa.Column(
            "processing_state",
            status_enum,
            nullable=False,
        ),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("updated", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_users_processing_state"), "users", ["processing_state"], unique=False
    )
    op.create_table(
        "clicks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("shop_url", sa.TEXT(), nullable=False),
        sa.Column("click_timestamp", sa.DateTime(), nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("clicks")
    op.drop_index(op.f("ix_users_processing_state"), table_name="users")
    op.drop_table("users")
    status_enum.drop(op.get_bind(), checkfirst=True)
