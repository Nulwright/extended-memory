python"""Add analytics and reporting tables

Revision ID: 003
Revises: 002
Create Date: 2024-02-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add export jobs table
    op.create_table(
        'export_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),  # UUID
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('format', sa.String(length=10), nullable=False),
        sa.Column('assistant_id', sa.Integer(), nullable=True),
        sa.Column('include_shared', sa.Boolean(), nullable=True, default=True),
        sa.Column('memory_type', sa.String(length=50), nullable=True),
        sa.Column('date_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True, default=0),
        sa.Column('record_count', sa.Integer(), nullable=True, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assistant_id'], ['assistants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_export_jobs_status', 'export_jobs', ['status'], unique=False)
    op.create_index('ix_export_jobs_created_at', 'export_jobs', ['created_at'], unique=False)

    # Add webhook logs table
    op.create_table(
        'webhook_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('processing_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_webhook_logs_type', 'webhook_logs', ['webhook_type'], unique=False)
    op.create_index('ix_webhook_logs_status', 'webhook_logs', ['status'], unique=False)
    op.create_index('ix_webhook_logs_created_at', 'webhook_logs', ['created_at'], unique=False)

    # Add session tracking table for WebSocket connections
    op.create_table(
        'websocket_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),  # UUID
        sa.Column('client_id', sa.String(length=100), nullable=False),
        sa.Column('assistant_id', sa.Integer(), nullable=True),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('disconnected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('messages_sent', sa.Integer(), nullable=True, default=0),
        sa.Column('messages_received', sa.Integer(), nullable=True, default=0),
        sa.ForeignKeyConstraint(['assistant_id'], ['assistants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_websocket_sessions_client_id', 'websocket_sessions', ['client_id'], unique=False)
    op.create_index('ix_websocket_sessions_connected_at', 'websocket_sessions', ['connected_at'], unique=False)

    # Enhance search_logs with more analytics fields
    op.add_column('search_logs', sa.Column('user_agent', sa.String(length=500), nullable=True))
    op.add_column('search_logs', sa.Column('ip_address', sa.String(length=45), nullable=True))
    op.add_column('search_logs', sa.Column('session_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('search_logs', 'session_id')
    op.drop_column('search_logs', 'ip_address')
    op.drop_column('search_logs', 'user_agent')
    op.drop_table('websocket_sessions')
    op.drop_table('webhook_logs')
    op.drop_table('export_jobs')