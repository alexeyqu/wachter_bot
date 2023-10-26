"""remove default values

Revision ID: 296da7f6d724
Revises: 85798d8901da
Create Date: 2023-10-25 15:37:35.767976

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "296da7f6d724"
down_revision = "85798d8901da"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("chats", schema=None) as batch_op:
        batch_op.alter_column(
            "on_new_chat_member_message", existing_type=sa.TEXT(), server_default=None
        )
        batch_op.alter_column(
            "on_known_new_chat_member_message",
            existing_type=sa.TEXT(),
            server_default=None,
        )
        batch_op.alter_column(
            "on_introduce_message", existing_type=sa.TEXT(), server_default=None
        )
        batch_op.alter_column(
            "on_kick_message", existing_type=sa.TEXT(), server_default=None
        )
        batch_op.alter_column(
            "notify_message", existing_type=sa.TEXT(), server_default=None
        )
        batch_op.alter_column(
            "kick_timeout", existing_type=sa.INTEGER(), server_default=None
        )
        batch_op.alter_column(
            "notify_timeout", existing_type=sa.INTEGER(), server_default=None
        )
        batch_op.alter_column(
            "whois_length", existing_type=sa.INTEGER(), server_default=None
        )
        batch_op.alter_column(
            "on_introduce_message_update", existing_type=sa.TEXT(), server_default=None
        )


def downgrade():
    with op.batch_alter_table("chats", schema=None) as batch_op:
        batch_op.alter_column(
            "on_new_chat_member_message",
            existing_type=sa.TEXT(),
            server_default="Пожалуйста, представьтесь и поздоровайтесь с сообществом.",
        )
        batch_op.alter_column(
            "on_known_new_chat_member_message",
            existing_type=sa.TEXT(),
            server_default="Добро пожаловать. Снова",
        )
        batch_op.alter_column(
            "on_introduce_message",
            existing_type=sa.TEXT(),
            server_default="Добро пожаловать.",
        )
        batch_op.alter_column(
            "on_kick_message",
            existing_type=sa.TEXT(),
            server_default="%USER\_MENTION% молчит и покидает чат",
        )
        batch_op.alter_column(
            "notify_message",
            existing_type=sa.TEXT(),
            server_default="%USER\_MENTION%, пожалуйста, представьтесь и поздоровайтесь с сообществом.",
        )
        batch_op.alter_column(
            "kick_timeout", existing_type=sa.INTEGER(), server_default="0"
        )
        batch_op.alter_column(
            "notify_timeout", existing_type=sa.INTEGER(), server_default="0"
        )
        batch_op.alter_column(
            "whois_length", existing_type=sa.INTEGER(), server_default="60"
        )
        batch_op.alter_column(
            "on_introduce_message_update",
            existing_type=sa.TEXT(),
            server_default="Если вы хотите обновить, то добавьте тег #update к сообщению.",
        )
