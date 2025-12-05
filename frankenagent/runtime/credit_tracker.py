"""Credit tracking wrapper for agent execution."""

import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from frankenagent.services.credit_service import CreditService

logger = logging.getLogger(__name__)


class CreditTracker:
    """Tracks credit usage during agent execution."""
    
    def __init__(self, credit_service: CreditService):
        self.credit_service = credit_service
        self.execution_credits = 0
        self.tool_credits = 0
        self.llm_credits = 0
        self.usage_details: List[Dict[str, Any]] = []
    
    def track_llm_call(
        self,
        token_count: int,
        model_name: str,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        has_tools: bool = False,
        tool_types: Optional[List[str]] = None
    ) -> int:
        """Track an LLM call and calculate credits.
        
        Simple pricing:
        - LLM only: 1 credit
        - LLM + Tavily: 5 credits
        - LLM + MCP: 10 credits
        """
        credits = self.credit_service.calculate_llm_cost(
            token_count=token_count,
            model_name=model_name,
            has_tools=has_tools,
            tool_types=tool_types or []
        )
        self.llm_credits += credits
        
        self.usage_details.append({
            "type": "llm_call",
            "model": model_name,
            "tokens": token_count,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "has_tools": has_tools,
            "tool_types": tool_types,
            "credits": credits
        })
        
        logger.debug(f"LLM call tracked: {model_name}, {credits} credits (tools: {has_tools})")
        return credits
    
    def track_tool_call(
        self,
        tool_name: str,
        component_type: str,
        duration_ms: float
    ) -> int:
        """Track a tool call and calculate credits."""
        credits = self.credit_service.CREDIT_COSTS.get(component_type, 1)
        self.tool_credits += credits
        
        self.usage_details.append({
            "type": "tool_call",
            "tool": tool_name,
            "component_type": component_type,
            "duration_ms": duration_ms,
            "credits": credits
        })
        
        logger.debug(f"Tool call tracked: {tool_name} ({component_type}), {credits} credits")
        return credits
    
    def track_execution_mode(self, execution_mode: str, num_agents: int = 1) -> int:
        """Track execution mode cost.
        
        Pricing:
        - single_agent: 1 credit
        - workflow: 3 credits
        - team: n x 2 credits (where n is number of agents)
        """
        if execution_mode == "team":
            credits = num_agents * self.credit_service.CREDIT_COSTS["team_base"]
        else:
            credits = self.credit_service.CREDIT_COSTS.get(execution_mode, 1)
        
        self.execution_credits += credits
        
        self.usage_details.append({
            "type": "execution_mode",
            "mode": execution_mode,
            "num_agents": num_agents if execution_mode == "team" else 1,
            "credits": credits
        })
        
        logger.debug(f"Execution mode tracked: {execution_mode}, {credits} credits (agents: {num_agents})")
        return credits
    
    def get_total_credits(self) -> int:
        """Get total credits used."""
        return self.execution_credits + self.tool_credits + self.llm_credits
    
    def get_breakdown(self) -> Dict[str, Any]:
        """Get credit usage breakdown."""
        return {
            "total_credits": self.get_total_credits(),
            "execution_credits": self.execution_credits,
            "tool_credits": self.tool_credits,
            "llm_credits": self.llm_credits,
            "details": self.usage_details
        }
    
    def commit_usage(
        self,
        db: Session,
        user_id: UUID,
        blueprint_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> None:
        """Commit usage to database and deduct credits."""
        total_credits = self.get_total_credits()
        
        if total_credits == 0:
            logger.debug("No credits to commit")
            return
        
        try:
            # Deduct credits from user balance
            self.credit_service.deduct_credits(
                db=db,
                user_id=user_id,
                amount=total_credits,
                description=f"Agent execution ({len(self.usage_details)} operations)",
                metadata=self.get_breakdown()
            )
            
            # Log each usage detail
            for detail in self.usage_details:
                usage_type = detail.get("type", "unknown")
                component_type = detail.get("component_type") or detail.get("mode")
                
                self.credit_service.log_usage(
                    db=db,
                    user_id=user_id,
                    blueprint_id=blueprint_id,
                    session_id=session_id,
                    usage_type=usage_type,
                    component_type=component_type,
                    credits_used=detail.get("credits", 0),
                    token_count=detail.get("tokens"),
                    model_name=detail.get("model"),
                    details=detail
                )
            
            logger.info(f"Committed {total_credits} credits for user {user_id}")
            
        except ValueError as e:
            logger.error(f"Failed to commit credits: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error committing credits: {e}")
            raise


class CreditAwareExecutor:
    """Wrapper that adds credit tracking to agent execution."""
    
    def __init__(self, credit_service: CreditService):
        self.credit_service = credit_service
    
    def check_sufficient_credits(
        self,
        db: Session,
        user_id: UUID,
        estimated_credits: int = 10
    ) -> bool:
        """Check if user has sufficient credits before execution."""
        try:
            balance = self.credit_service.get_user_balance(db, user_id)
            return balance >= estimated_credits
        except Exception as e:
            logger.error(f"Error checking credits: {e}")
            return False
    
    def create_tracker(self) -> CreditTracker:
        """Create a new credit tracker for an execution."""
        return CreditTracker(self.credit_service)
    
    def extract_token_usage(self, agent_response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage from agent response if available."""
        try:
            # Agno agents may include usage info in response
            if hasattr(agent_response, 'usage'):
                usage = agent_response.usage
                return {
                    "total_tokens": getattr(usage, 'total_tokens', 0),
                    "prompt_tokens": getattr(usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(usage, 'completion_tokens', 0)
                }
            
            # Try to get from metrics
            if hasattr(agent_response, 'metrics'):
                metrics = agent_response.metrics
                if hasattr(metrics, 'total_tokens'):
                    return {
                        "total_tokens": metrics.total_tokens,
                        "prompt_tokens": getattr(metrics, 'prompt_tokens', 0),
                        "completion_tokens": getattr(metrics, 'completion_tokens', 0)
                    }
        except Exception as e:
            logger.debug(f"Could not extract token usage: {e}")
        
        return None
    
    def estimate_tokens_from_text(self, text: str) -> int:
        """Rough estimation of tokens from text (4 chars ≈ 1 token)."""
        return len(text) // 4
