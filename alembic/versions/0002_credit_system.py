"""Add credit and usage tracking system

Revision ID: 0002_credit_system
Revises: 0001_google_cloud_core_schema
Create Date: 2025-12-03 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '0002_credit_system'
down_revision = '0001_google_cloud_core_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add credit_balance to users table
    op.add_column('users', sa.Column('credit_balance', sa.Integer(), nullable=False, server_default='1000'))
    op.add_column('users', sa.Column('monthly_credit_limit', sa.Integer(), nullable=False, server_default='1000'))
    op.add_column('users', sa.Column('credit_reset_date', sa.DateTime(), nullable=True))
    
    # Create credit_transactions table
    op.create_table(
        'credit_transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transaction_type', sa.String(50), nullable=False),  # 'debit', 'credit', 'refund'
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('meta_data', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index('idx_credit_transactions_user_created', 'user_id', 'created_at'),
    )
    
    # Create usage_logs table
    op.create_table(
        'usage_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('blueprint_id', UUID(as_uuid=True), sa.ForeignKey('blueprints.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('usage_type', sa.String(50), nullable=False),  # 'llm_call', 'tool_call', 'agent_execution'
        sa.Column('component_type', sa.String(50), nullable=True),  # 'mcp_tool', 'http_tool', 'workflow', 'team'
        sa.Column('credits_used', sa.Integer(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),  # For LLM calls
        sa.Column('model_name', sa.String(100), nullable=True),  # For LLM calls
        sa.Column('details', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index('idx_usage_logs_user_created', 'user_id', 'created_at'),
        sa.Index('idx_usage_logs_type', 'usage_type'),
    )


def downgrade() -> None:
    op.drop_table('usage_logs')
    op.drop_table('credit_transactions')
    op.drop_column('users', 'credit_reset_date')
    op.drop_column('users', 'monthly_credit_limit')
    op.drop_column('users', 'credit_balance')
