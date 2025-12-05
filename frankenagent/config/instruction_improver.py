"""Instruction improvement service for FrankenAgent Lab.

This module provides LLM-assisted instruction improvement to help users
create more effective system prompts for their agents.
"""

import os
from typing import Dict, Any, List
from agno.agent import Agent
from agno.models.openai import OpenAIChat


class InstructionImprover:
    """Service for improving agent instructions using LLM assistance."""
    
    def __init__(self):
        """Initialize the instruction improver with a specialized agent."""
        # Create a specialized agent for instruction improvement
        self.improver_agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            instructions="""You are an expert at writing effective AI agent instructions.

Your task is to improve system prompts for AI agents while:
1. Preserving the user's original intent
2. Making instructions clearer and more specific
3. Adding relevant context and guidelines
4. Ensuring the instructions work well with the agent's available tools
5. Following best practices for prompt engineering

Provide:
- Improved instructions
- Brief explanation of changes
- Optional suggestions for further improvement""",
            markdown=False
        )
    
    def improve(
        self,
        current_instructions: str,
        improvement_goal: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Improve instructions using LLM assistance.
        
        Args:
            current_instructions: The current system prompt
            improvement_goal: What the user wants to improve
            context: Additional context (agent purpose, tools, etc.)
        
        Returns:
            Dictionary with improved instructions, explanation, and suggestions
        """
        # Build prompt for the improver agent
        prompt = self._build_improvement_prompt(
            current_instructions,
            improvement_goal,
            context
        )
        
        try:
            # Run the improver agent
            result = self.improver_agent.run(prompt)
            
            # Parse the response
            improved = self._parse_improvement_response(result.content)
            
            return {
                "improved_instructions": improved.get("instructions", current_instructions),
                "explanation": improved.get("explanation", ""),
                "suggestions": improved.get("suggestions", [])
            }
        except Exception as e:
            # If improvement fails, return original with error
            return {
                "improved_instructions": current_instructions,
                "explanation": f"Failed to improve instructions: {str(e)}",
                "suggestions": []
            }
    
    def _build_improvement_prompt(
        self,
        current: str,
        goal: str,
        context: Dict[str, Any]
    ) -> str:
        """Build the prompt for the improver agent.
        
        Args:
            current: Current instructions
            goal: Improvement goal
            context: Additional context
        
        Returns:
            Formatted prompt string
        """
        tools_info = ""
        if context.get("tools_available"):
            tools_info = f"\nAvailable tools: {', '.join(context['tools_available'])}"
        
        purpose_info = ""
        if context.get("agent_purpose"):
            purpose_info = f"\nAgent purpose: {context['agent_purpose']}"
        
        return f"""Please improve these agent instructions:

Current instructions:
{current}

Improvement goal: {goal}{purpose_info}{tools_info}

Provide your response in this format:

IMPROVED INSTRUCTIONS:
[Your improved version here]

EXPLANATION:
[Brief explanation of what you changed and why]

SUGGESTIONS:
- [Optional suggestion 1]
- [Optional suggestion 2]
"""
    
    def _parse_improvement_response(self, response: str) -> Dict[str, Any]:
        """Parse the improver agent's response.
        
        Args:
            response: Raw response from the improver agent
        
        Returns:
            Dictionary with parsed instructions, explanation, and suggestions
        """
        # Simple parsing - split by section headers
        sections = {}
        
        if "IMPROVED INSTRUCTIONS:" in response:
            parts = response.split("IMPROVED INSTRUCTIONS:")
            if len(parts) > 1:
                rest = parts[1]
                if "EXPLANATION:" in rest:
                    inst_parts = rest.split("EXPLANATION:")
                    sections["instructions"] = inst_parts[0].strip()
                    
                    if "SUGGESTIONS:" in inst_parts[1]:
                        exp_parts = inst_parts[1].split("SUGGESTIONS:")
                        sections["explanation"] = exp_parts[0].strip()
                        
                        # Parse suggestions
                        suggestions_text = exp_parts[1].strip()
                        suggestions = [
                            s.strip().lstrip("-").strip()
                            for s in suggestions_text.split("\n")
                            if s.strip() and s.strip().startswith("-")
                        ]
                        sections["suggestions"] = suggestions
                    else:
                        sections["explanation"] = inst_parts[1].strip()
        
        return sections
