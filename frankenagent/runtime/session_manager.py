"""Session manager for tracking agent execution sessions and logs."""

from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid


class SessionManager:
    """Manages agent execution sessions and logging.
    
    For MVP, uses in-memory storage with dict-based data structures.
    Future versions will use database storage for persistence.
    """
    
    def __init__(self):
        """Initialize session manager with in-memory storage."""
        # Store session metadata and conversation history
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Store execution logs per session
        self.logs: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_new_session(self) -> str:
        """Create a new session and return its unique identifier.
        
        Returns:
            str: Session ID in format 'sess_<uuid>'
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        self.sessions[session_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "messages": []
        }
        
        self.logs[session_id] = []
        
        return session_id
    
    def get_or_create(self, session_id: str) -> Dict[str, Any]:
        """Get existing session or create new one if it doesn't exist.
        
        Args:
            session_id: Session identifier
            
        Returns:
            dict: Session metadata including created_at and messages
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "messages": []
            }
            self.logs[session_id] = []
        
        return self.sessions[session_id]
    
    def log_event(
        self,
        session_id: str,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a general execution event for a session.
        
        Args:
            session_id: Session identifier
            event_type: Type of event (e.g., 'execution_start', 'compilation', 'agent_response')
            message: Human-readable message describing the event
            details: Optional additional details about the event
        """
        # Ensure session exists
        if session_id not in self.logs:
            self.logs[session_id] = []
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "message": message,
            "details": details or {}
        }
        
        self.logs[session_id].append(log_entry)
    
    def log_tool_call(
        self,
        session_id: str,
        tool_name: str,
        args: Dict[str, Any],
        duration_ms: int,
        success: bool,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Log a tool call event for a session.
        
        Args:
            session_id: Session identifier
            tool_name: Name of the tool that was invoked
            args: Input arguments passed to the tool
            duration_ms: Execution duration in milliseconds
            success: Whether the tool call succeeded
            result: Tool output (truncated to 200 chars for storage)
            error: Error message if tool call failed
        """
        # Ensure session exists
        if session_id not in self.logs:
            self.logs[session_id] = []
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "tool_call",
            "tool_name": tool_name,
            "args": args,
            "duration_ms": duration_ms,
            "success": success,
            "result": result[:200] if result else None,  # Truncate for storage
            "error": error
        }
        
        self.logs[session_id].append(log_entry)
    
    def get_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all logs for a session in chronological order.
        
        Args:
            session_id: Session identifier
            
        Returns:
            list: List of log entries for the session, empty list if session not found
        """
        return self.logs.get(session_id, [])
