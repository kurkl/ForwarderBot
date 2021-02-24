"""Rework entities

Revision ID: a01f54e28486
Revises: 330668cd2e5d
Create Date: 2021-02-24 20:31:27.076452

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a01f54e28486"
down_revision = "330668cd2e5d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_dt", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_dt", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_table(
        "subscribers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("created_dt", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("expiration_dt", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "forwarder_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("max_count", sa.SmallInteger(), nullable=False),
        sa.Column(
            "subscriber_walls_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("subscriber_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["subscriber_id"], ["subscribers.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "targets",
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("sleep", sa.SmallInteger(), nullable=True),
        sa.Column("admin_access", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_dt", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_dt", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("forwarder_target_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["forwarder_target_id"], ["forwarder_targets.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("source_id"),
    )
    op.drop_table("vkpostdevdata")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "vkpostdevdata",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("idx", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("attachments", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name="vkpostdevdata_pkey"),
        sa.UniqueConstraint("idx", name="vkpostdevdata_idx_key"),
    )
    op.drop_table("targets")
    op.drop_table("forwarder_targets")
    op.drop_table("subscribers")
    op.drop_table("users")
    # ### end Alembic commands ###