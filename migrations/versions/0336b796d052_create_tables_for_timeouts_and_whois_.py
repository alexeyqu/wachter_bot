"""create tables for timeouts and whois length

Revision ID: e34af99a19b5
Revises: 0336b796d052
Create Date: 2023-10-21 16:56:05.421923

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e34af99a19b5"
down_revision = "0336b796d052"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chats",
        sa.Column("notify_timeout", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "chats",
        sa.Column("whois_length", sa.Integer(), nullable=False, server_default="60"),
    )


def downgrade():
    op.drop_column(
        "chats",
        sa.Column("notify_timeout", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_column(
        "chats",
        sa.Column("whois_length", sa.Integer(), nullable=False, server_default="60"),
    )
