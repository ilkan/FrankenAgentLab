"""Credit and usage tracking API endpoints."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from frankenagent.api.auth import get_current_user
from frankenagent.db.database import get_db
from frankenagent.db.models import User
from frankenagent.services.credit_service import CreditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credits", tags=["credits"])
credit_service = CreditService()


# Response Models
class CreditBalanceResponse(BaseModel):
    """Credit balance response."""
    credit_balance: int = Field(..., description="Current credit balance")
    monthly_limit: int = Field(..., description="Monthly credit limit")
    credits_used_this_month: int = Field(..., description="Credits used this month")
    reset_date: Optional[str] = Field(None, description="Next reset date (ISO format)")
    total_operations: int = Field(..., description="Total operations this month")


class TransactionResponse(BaseModel):
    """Credit transaction response."""
    id: str
    transaction_type: str = Field(..., description="Transaction type: debit, credit, refund")
    amount: int = Field(..., description="Transaction amount (negative for debit)")
    balance_after: int = Field(..., description="Balance after transaction")
    description: str
    metadata: dict
    created_at: str


class UsageLogResponse(BaseModel):
    """Usage log response."""
    id: str
    usage_type: str = Field(..., description="Usage type: llm_call, tool_call, agent_execution")
    component_type: Optional[str] = Field(None, description="Component type: mcp_tool, http_tool, workflow, team")
    credits_used: int
    token_count: Optional[int] = Field(None, description="Token count for LLM calls")
    model_name: Optional[str] = Field(None, description="Model name for LLM calls")
    details: dict
    created_at: str


class CreditCostsResponse(BaseModel):
    """Credit costs configuration."""
    llm_base: int
    llm_per_1k_tokens: int
    mcp_tool: int
    http_tool: int
    tavily_search: int
    python_eval: int
    single_agent: int
    workflow: int
    team: int
    guardrail_check: int


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current credit balance and usage summary."""
    try:
        summary = credit_service.get_usage_summary(db, current_user.id)
        return CreditBalanceResponse(**summary)
    except Exception as e:
        logger.error(f"Error getting credit balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transaction_history(
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get credit transaction history."""
    try:
        transactions = credit_service.get_transaction_history(
            db, current_user.id, limit=limit, offset=offset
        )
        return [TransactionResponse(**t) for t in transactions]
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage", response_model=List[UsageLogResponse])
async def get_usage_logs(
    limit: int = Query(50, ge=1, le=100, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    usage_type: Optional[str] = Query(None, description="Filter by usage type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage logs with optional filtering."""
    try:
        logs = credit_service.get_usage_logs(
            db, current_user.id, limit=limit, offset=offset, usage_type=usage_type
        )
        return [UsageLogResponse(**log) for log in logs]
    except Exception as e:
        logger.error(f"Error getting usage logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs", response_model=CreditCostsResponse)
async def get_credit_costs(
    current_user: User = Depends(get_current_user)
):
    """Get credit costs for different operations."""
    return CreditCostsResponse(**credit_service.CREDIT_COSTS)
