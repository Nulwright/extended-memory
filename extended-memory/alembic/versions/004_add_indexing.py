"""Add advanced indexing and constraints

Revision ID: 004
Revises: 003
Create Date: 2024-02-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add full-text search indexes (PostgreSQL specific)
    try:
        # Add GIN index for content search
        op.execute("CREATE INDEX CONCURRENTLY ix_memories_content_gin ON memories USING gin(to_tsvector('english', content))")
        op.execute("CREATE INDEX CONCURRENTLY ix_memories_summary_gin ON memories USING gin(to_tsvector('english', coalesce(summary, '')))")
    except Exception:
        # Fallback for databases that don't support full-text search
        op.create_index('ix_memories_content_text', 'memories', ['content'], unique=False)
        op.create_index('ix_memories_summary_text', 'memories', ['summary'], unique=False)

    # Add composite indexes for common query patterns
    op.create_index('ix_memories_assistant_created', 'memories', ['assistant_id', 'created_at'], unique=False)
    op.create_index('ix_memories_assistant_importance', 'memories', ['assistant_id', 'importance'], unique=False)
    op.create_index('ix_memories_shared_category', 'memories', ['is_shared', 'shared_category'], unique=False)
    op.create_index('ix_memories_type_importance', 'memories', ['memory_type', 'importance'], unique=False)

    # Add indexes for search logs analytics
    op.create_index('ix_search_logs_query_hash', 'search_logs', [sa.text('md5(query)')], unique=False)
    op.create_index('ix_search_logs_assistant_created', 'search_logs', ['assistant_id', 'created_at'], unique=False)

    # Add partial indexes for active records
    op.execute("CREATE INDEX ix_assistants_active ON assistants (name) WHERE is_active = true")
    op.execute("CREATE INDEX ix_memories_recent ON memories (created_at DESC) WHERE created_at > CURRENT_DATE - INTERVAL '30 days'")

    # Add constraints for data integrity
    op.create_check_constraint(
        'ck_memories_importance_range',
        'memories',
        sa.text('importance >= 1 AND importance <= 10')
    )
    
    op.create_check_constraint(
        'ck_memories_access_count_positive',
        'memories',
        sa.text('access_count >= 0')
    )
    
    op.create_check_constraint(
        'ck_memory_stats_positive_values',
        'memory_stats',
        sa.text('total_memories >= 0 AND total_shared_memories >= 0 AND memories_created_today >= 0 AND memories_accessed_today >= 0')
    )

    # Add unique constraint for memory stats per assistant per day
    op.create_unique_constraint('uq_memory_stats_assistant_date', 'memory_stats', ['assistant_id', sa.text('date::date')])


def downgrade() -> None:
    op.drop_constraint('uq_memory_stats_assistant_date', 'memory_stats')
    op.drop_constraint('ck_memory_stats_positive_values', 'memory_stats')
    op.drop_constraint('ck_memories_access_count_positive', 'memories')
    op.drop_constraint('ck_memories_importance_range', 'memories')
    
    # Drop partial indexes
    op.drop_index('ix_memories_recent', table_name='memories')
    op.drop_index('ix_assistants_active', table_name='assistants')
    
    # Drop composite indexes
    op.drop_index('ix_search_logs_assistant_created', table_name='search_logs')
    op.drop_index('ix_search_logs_query_hash', table_name='search_logs')
    op.drop_index('ix_memories_type_importance', table_name='memories')
    op.drop_index('ix_memories_shared_category', table_name='memories')
    op.drop_index('ix_memories_assistant_importance', table_name='memories')
    op.drop_index('ix_memories_assistant_created', table_name='memories')
    
    # Drop full-text indexes
    try:
        op.drop_index('ix_memories_summary_gin', table_name='memories')
        op.drop_index('ix_memories_content_gin', table_name='memories')
    except Exception:
        op.drop_index('ix_memories_summary_text', table_name='memories')
        op.drop_index('ix_memories_content_text', table_name='memories')