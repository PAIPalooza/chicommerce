"""add webhook_logs table

Revision ID: d79c568a4563
Revises: b026acee0c6b
Create Date: 2026-02-15 11:30:03.147892

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd79c568a4563'
down_revision = 'b026acee0c6b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'webhook_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('http_method', sa.String(length=10), nullable=False),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('headers', sa.Text(), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('is_success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_logs_id'), 'webhook_logs', ['id'], unique=False)
    op.create_index(op.f('ix_webhook_logs_event_id'), 'webhook_logs', ['event_id'], unique=False)
    op.create_index(op.f('ix_webhook_logs_event_type'), 'webhook_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_logs_response_status'), 'webhook_logs', ['response_status'], unique=False)
    op.create_index(op.f('ix_webhook_logs_sent_at'), 'webhook_logs', ['sent_at'], unique=False)
    op.create_index(op.f('ix_webhook_logs_is_success'), 'webhook_logs', ['is_success'], unique=False)
    op.create_index('idx_webhook_log_event_type_sent_at', 'webhook_logs', ['event_type', 'sent_at'], unique=False)
    op.create_index('idx_webhook_log_status_sent_at', 'webhook_logs', ['response_status', 'sent_at'], unique=False)
    op.create_index('idx_webhook_log_success_sent_at', 'webhook_logs', ['is_success', 'sent_at'], unique=False)


def downgrade():
    op.drop_index('idx_webhook_log_success_sent_at', table_name='webhook_logs')
    op.drop_index('idx_webhook_log_status_sent_at', table_name='webhook_logs')
    op.drop_index('idx_webhook_log_event_type_sent_at', table_name='webhook_logs')
    op.drop_index(op.f('ix_webhook_logs_is_success'), table_name='webhook_logs')
    op.drop_index(op.f('ix_webhook_logs_sent_at'), table_name='webhook_logs')
    op.drop_index(op.f('ix_webhook_logs_response_status'), table_name='webhook_logs')
    op.drop_index(op.f('ix_webhook_logs_event_type'), table_name='webhook_logs')
    op.drop_index(op.f('ix_webhook_logs_event_id'), table_name='webhook_logs')
    op.drop_index(op.f('ix_webhook_logs_id'), table_name='webhook_logs')
    op.drop_table('webhook_logs')
