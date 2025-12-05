"""Credit and usage tracking models for FrankenAgent Lab."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from frankenagent.db.base import Base


class CreditTransaction(Base):
    """Credit transaction model.
    
    Tracks all credit additions, deductions, and refunds for users.
    """
    
    __tablename__ = "credit_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # 'debit', 'credit', 'refund'
    amount = Column(Integer, nullable=False)  # Positive for credit, negative for debit
    balance_after = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)
    meta_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_credit_transactions_user_created", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<CreditTransaction(id={self.id}, user_id={self.user_id}, type={self.transaction_type}, amount={self.amount})>"


class UsageLog(Base):
    """Usage log model.
    
    Tracks detailed usage of LLM calls, tools, and agent executions.
    """
    
    __tablename__ = "usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("blueprints.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    usage_type = Column(String(50), nullable=False)  # 'llm_call', 'tool_call', 'agent_execution'
    component_type = Column(String(50), nullable=True)  # 'mcp_tool', 'http_tool', 'workflow', 'team', 'single_agent'
    credits_used = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=True)  # For LLM calls
    model_name = Column(String(100), nullable=True)  # For LLM calls
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_usage_logs_user_created", "user_id", "created_at"),
        Index("idx_usage_logs_type", "usage_type"),
    )
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, user_id={self.user_id}, type={self.usage_type}, credits={self.credits_used})>"
