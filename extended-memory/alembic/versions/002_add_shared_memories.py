python"""Add shared memories enhancements

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes for better shared memory performance
    op.create_index('ix_shared_memories_category', 'shared_memories', ['category'], unique=False)
    op.create_index('ix_shared_memories_access_count', 'shared_memories', ['access_count'], unique=False)
    
    # Add constraint to ensure shared memories have categories
    op.create_check_constraint(
        'ck_shared_memory_category_not_null',
        'shared_memories',
        sa.text('category IS NOT NULL AND length(category) > 0')
    )
    
    # Add index for memory access patterns
    op.create_index('ix_memories_access_count', 'memories', ['access_count'], unique=False)
    op.create_index('ix_memories_accessed_at', 'memories', ['accessed_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_memories_accessed_at', table_name='memories')
    op.drop_index('ix_memories_access_count', table_name='memories')
    op.drop_constraint('ck_shared_memory_category_not_null', 'shared_memories')
    op.drop_index('ix_shared_memories_access_count', table_name='shared_memories')
    op.drop_index('ix_shared_memories_category', table_name='shared_memories')