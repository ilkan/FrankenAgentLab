"""Credit management service for FrankenAgent Lab."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from frankenagent.db.credit_models import CreditTransaction, UsageLog
from frankenagent.db.models import User

logger = logging.getLogger(__name__)


class CreditService:
    """Service for managing user credits and usage tracking."""
    
    # Credit costs for different operations
    CREDIT_COSTS = {
        # LLM calls - simple flat rate
        "llm_simple": 1,  # Simple LLM call (no tools)
        "llm_with_tavily": 5,  # LLM + Tavily search
        "llm_with_mcp": 10,  # LLM + MCP tool
        
        # Tool usage (individual)
        "mcp_tool": 10,  # MCP tool call
        "http_tool": 1,  # HTTP tool call
        "tavily_search": 5,  # Web search (Tavily)
        "python_eval": 2,  # Python evaluation
        "file_tool": 1,  # File operations
        
        # Execution modes
        "single_agent": 1,  # Base cost for single agent
        "workflow": 3,  # Workflow execution
        "team_base": 2,  # Base cost per agent in team (multiplied by n agents)
        
        # Guardrails
        "guardrail_check": 0,  # Free - part of execution
    }
    
    def __init__(self):
        self.monthly_credit_limit = 1000
    
    def get_user_balance(self, db: Session, user_id: UUID) -> int:
        """Get current credit balance for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check if monthly reset is needed
        self._check_monthly_reset(db, user)
        
        return user.credit_balance
    
    def _check_monthly_reset(self, db: Session, user: User) -> None:
        """Check if monthly credit reset is needed."""
        now = datetime.utcnow()
        
        # Initialize reset date if not set
        if user.credit_reset_date is None:
            user.credit_reset_date = now + timedelta(days=30)
            db.commit()
            return
        
        # Check if reset date has passed
        if now >= user.credit_reset_date:
            old_balance = user.credit_balance
            user.credit_balance = user.monthly_credit_limit
            user.credit_reset_date = now + timedelta(days=30)
            
            # Log the reset transaction
            transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="credit",
                amount=user.monthly_credit_limit,
                balance_after=user.credit_balance,
                description="Monthly credit reset",
                meta_data={
                    "previous_balance": old_balance,
                    "reset_date": now.isoformat()
                }
            )
            db.add(transaction)
            db.commit()
            
            logger.info(f"Reset credits for user {user.id}: {old_balance} -> {user.credit_balance}")
    
    def deduct_credits(
        self,
        db: Session,
        user_id: UUID,
        amount: int,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CreditTransaction:
        """Deduct credits from user balance."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check monthly reset
        self._check_monthly_reset(db, user)
        
        # Check sufficient balance
        if user.credit_balance < amount:
            raise ValueError(
                f"Insufficient credits. Required: {amount}, Available: {user.credit_balance}"
            )
        
        # Deduct credits
        user.credit_balance -= amount
        
        # Create transaction record
        transaction = CreditTransaction(
            user_id=user_id,
            transaction_type="debit",
            amount=-amount,
            balance_after=user.credit_balance,
            description=description,
            meta_data=metadata or {}
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Deducted {amount} credits from user {user_id}. New balance: {user.credit_balance}")
        return transaction
    
    def add_credits(
        self,
        db: Session,
        user_id: UUID,
        amount: int,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CreditTransaction:
        """Add credits to user balance."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        user.credit_balance += amount
        
        transaction = CreditTransaction(
            user_id=user_id,
            transaction_type="credit",
            amount=amount,
            balance_after=user.credit_balance,
            description=description,
            meta_data=metadata or {}
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Added {amount} credits to user {user_id}. New balance: {user.credit_balance}")
        return transaction
    
    def calculate_llm_cost(self, token_count: int, model_name: str, has_tools: bool = False, tool_types: Optional[List[str]] = None) -> int:
        """Calculate credit cost for an LLM call.
        
        Simple pricing:
        - LLM only: 1 credit
        - LLM + Tavily: 5 credits
        - LLM + MCP: 10 credits
        
        Args:
            token_count: Number of tokens (not used in simple pricing)
            model_name: Model name (not used in simple pricing)
            has_tools: Whether tools were used
            tool_types: List of tool types used
            
        Returns:
            Credit cost for the LLM call
        """
        if not has_tools or not tool_types:
            logger.debug(f"LLM cost: 1 credit (no tools)")
            return self.CREDIT_COSTS["llm_simple"]
        
        logger.debug(f"LLM cost calculation - tool_types: {tool_types}")
        
        # Check for MCP tools (highest priority)
        if any("mcp" in tool.lower() for tool in tool_types):
            logger.debug(f"LLM cost: 10 credits (MCP tool detected)")
            return self.CREDIT_COSTS["llm_with_mcp"]
        
        # Check for Tavily search
        if any("tavily" in tool.lower() or tool.lower() == "tavily_search" for tool in tool_types):
            logger.debug(f"LLM cost: 5 credits (Tavily detected)")
            return self.CREDIT_COSTS["llm_with_tavily"]
        
        # Default to simple LLM cost
        logger.debug(f"LLM cost: 1 credit (default, tools: {tool_types})")
        return self.CREDIT_COSTS["llm_simple"]
    
    def calculate_component_cost(self, component_type: str, execution_mode: str = "single_agent", num_agents: int = 1) -> int:
        """Calculate credit cost for a component.
        
        Args:
            component_type: Type of component (tool type)
            execution_mode: Execution mode (single_agent, workflow, team)
            num_agents: Number of agents (for team mode)
            
        Returns:
            Credit cost for the component
        """
        cost = 0
        
        # Add execution mode cost
        if execution_mode == "team":
            # Team cost: n x 2 credits (where n is number of agents)
            cost += num_agents * self.CREDIT_COSTS["team_base"]
        else:
            cost += self.CREDIT_COSTS.get(execution_mode, 1)
        
        # Add component cost if specified
        if component_type:
            cost += self.CREDIT_COSTS.get(component_type, 0)
        
        return max(1, cost)  # Minimum 1 credit
    
    def log_usage(
        self,
        db: Session,
        user_id: UUID,
        usage_type: str,
        credits_used: int,
        blueprint_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        component_type: Optional[str] = None,
        token_count: Optional[int] = None,
        model_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> UsageLog:
        """Log a usage event."""
        usage_log = UsageLog(
            user_id=user_id,
            blueprint_id=blueprint_id,
            session_id=session_id,
            usage_type=usage_type,
            component_type=component_type,
            credits_used=credits_used,
            token_count=token_count,
            model_name=model_name,
            details=details or {}
        )
        db.add(usage_log)
        db.commit()
        db.refresh(usage_log)
        
        logger.debug(f"Logged usage for user {user_id}: {usage_type}, {credits_used} credits")
        return usage_log
    
    def get_transaction_history(
        self,
        db: Session,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get credit transaction history for a user."""
        transactions = (
            db.query(CreditTransaction)
            .filter(CreditTransaction.user_id == user_id)
            .order_by(desc(CreditTransaction.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        return [
            {
                "id": str(t.id),
                "transaction_type": t.transaction_type,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "description": t.description,
                "metadata": t.meta_data,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
    
    def get_usage_logs(
        self,
        db: Session,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        usage_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get usage logs for a user."""
        query = db.query(UsageLog).filter(UsageLog.user_id == user_id)
        
        if usage_type:
            query = query.filter(UsageLog.usage_type == usage_type)
        
        logs = (
            query
            .order_by(desc(UsageLog.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        return [
            {
                "id": str(log.id),
                "usage_type": log.usage_type,
                "component_type": log.component_type,
                "credits_used": log.credits_used,
                "token_count": log.token_count,
                "model_name": log.model_name,
                "details": log.details,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    
    def get_usage_summary(self, db: Session, user_id: UUID) -> Dict[str, Any]:
        """Get usage summary for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check monthly reset
        self._check_monthly_reset(db, user)
        
        # Calculate total usage this month
        if user.credit_reset_date:
            month_start = user.credit_reset_date - timedelta(days=30)
        else:
            month_start = datetime.utcnow() - timedelta(days=30)
        
        total_used = (
            db.query(UsageLog)
            .filter(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= month_start
            )
            .count()
        )
        
        return {
            "credit_balance": user.credit_balance,
            "monthly_limit": user.monthly_credit_limit,
            "credits_used_this_month": user.monthly_credit_limit - user.credit_balance,
            "reset_date": user.credit_reset_date.isoformat() if user.credit_reset_date else None,
            "total_operations": total_used
        }
