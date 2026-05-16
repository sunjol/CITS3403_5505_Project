"""Add prompt likes table.

Revision ID: 0002_add_prompt_likes
Revises: 0001_initial_promptshare_schema
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_prompt_likes"
down_revision = "0001_initial_promptshare_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prompt_like",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["prompt_id"], ["prompt.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "prompt_id", name="uq_prompt_like_user_prompt"),
    )


def downgrade():
    op.drop_table("prompt_like")
