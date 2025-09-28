"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create assistants table
    op.create_table(
        'assistants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('personality', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assistants_id'), 'assistants', ['id'], unique=False)
    op.create_unique_constraint('uq_assistants_name', 'assistants', ['name'])

    # Create memories table
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assistant_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('memory_type', sa.String(length=50), nullable=True, default='general'),
        sa.Column('importance', sa.Integer(), nullable=True, default=5),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('is_shared', sa.Boolean(), nullable=True, default=False),
        sa.Column('shared_category', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True, default=0),
        sa.ForeignKeyConstraint(['assistant_id'], ['assistants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memories_id'), 'memories', ['id'], unique=False)
    op.create_index('ix_memories_assistant_type', 'memories', ['assistant_id', 'memory_type'], unique=False)
    op.create_index('ix_memories_created_at', 'memories', ['created_at'], unique=False)
    op.create_index('ix_memories_importance', 'memories', ['importance'], unique=False)
    op.create_index('ix_memories_shared', 'memories', ['is_shared', 'shared_category'], unique=False)

    # Create memory embeddings table
    op.create_table(
        'memory_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('memory_id', sa.Integer(), nullable=False),
        sa.Column('embedding_vector', sa.Text(), nullable=True),
        sa.Column('embedding_model', sa.String(length=50), nullable=True, default='text-embedding-ada-002'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_embeddings_id'), 'memory_embeddings', ['id'], unique=False)
    op.create_index('ix_memory_embeddings_memory_id', 'memory_embeddings', ['memory_id'], unique=False)

    # Create shared memories table
    op.create_table(
        'shared_memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('memory_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('access_level', sa.String(length=20), nullable=True, default='read'),
        sa.Column('last_accessed_by', sa.Integer(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['last_accessed_by'], ['assistants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shared_memories_id'), 'shared_memories', ['id'], unique=False)

    # Create memory stats table
    op.create_table(
        'memory_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assistant_id', sa.Integer(), nullable=False),
        sa.Column('total_memories', sa.Integer(), nullable=True, default=0),
        sa.Column('total_shared_memories', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_importance', sa.Float(), nullable=True, default=5.0),
        sa.Column('most_used_type', sa.String(length=50), nullable=True),
        sa.Column('memories_created_today', sa.Integer(), nullable=True, default=0),
        sa.Column('memories_accessed_today', sa.Integer(), nullable=True, default=0),
        sa.Column('date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assistant_id'], ['assistants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_stats_id'), 'memory_stats', ['id'], unique=False)
    op.create_index('ix_memory_stats_assistant_date', 'memory_stats', ['assistant_id', 'date'], unique=False)

    # Create search logs table
    op.create_table(
        'search_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assistant_id', sa.Integer(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('search_type', sa.String(length=20), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assistant_id'], ['assistants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_logs_id'), 'search_logs', ['id'], unique=False)
    op.create_index('ix_search_logs_created_at', 'search_logs', ['created_at'], unique=False)
    op.create_index('ix_search_logs_assistant_id', 'search_logs', ['assistant_id'], unique=False)

    # Insert default assistants
    op.execute("""
        INSERT INTO assistants (name, personality, is_active) VALUES 
        ('Sienna', 'Dry, sharp, sarcastic, cutting truth-teller who doesn''t sugarcoat anything', true),
        ('Vale', 'Quieter, reflective, precise assistant who thinks deeply before speaking', true)
    """)


def downgrade() -> None:
    op.drop_table('search_logs')
    op.drop_table('memory_stats')
    op.drop_table('shared_memories')
    op.drop_table('memory_embeddings')
    op.drop_table('memories')
    op.drop_table('assistants')