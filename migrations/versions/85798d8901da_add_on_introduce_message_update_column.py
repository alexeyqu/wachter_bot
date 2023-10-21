"""add on_introduce_message_update column

Revision ID: 85798d8901da
Revises: e34af99a19b5
Create Date: 2023-10-23 22:48:45.471633

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "85798d8901da"
down_revision = "e34af99a19b5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chats",
        sa.Column(
            "on_introduce_message_update",
            sa.Text(),
            nullable=False,
            server_default="Если вы хотите обновить, то добавьте тег #update к сообщению.",
        ),
    )


def downgrade():
    op.drop_column(
        "chats",
        sa.Column(
            "on_introduce_message_update",
            sa.Text(),
            nullable=False,
            server_default="Если вы хотите обновить, то добавьте тег #update к сообщению.",
        ),
    )
