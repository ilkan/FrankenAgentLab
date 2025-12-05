# Agno Documentation

## Introduction

Agno is an incredibly fast multi-agent framework, runtime, and control plane designed for building sophisticated AI systems. It provides a comprehensive platform for creating AI agents with memory, knowledge bases, tool integration, and Model Context Protocol (MCP) support. Agno enables developers to orchestrate agents as multi-agent teams for greater autonomy or as step-based agentic workflows for more granular control. The framework ships with AgentOS, a high-performance FastAPI runtime that provides a pre-built web application for serving and managing agent systems.

The framework includes a complete agentic solution with an integrated control plane accessible at os.agno.com, allowing developers to test, monitor, and manage their AI systems in real-time. AgentOS runs entirely in your cloud environment, ensuring complete data privacy with no external data transmission required. Agno supports multiple LLM providers (OpenAI, Anthropic, Google, and more), various database backends for session and memory storage (SQLite, PostgreSQL), vector databases for knowledge bases (LanceDB, Pinecone), and seamless integration with external tools and APIs through its extensible tools system.

## Core APIs and Key Functions

### Basic Agent Creation

Create a simple AI agent with personality and instructions.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Create an agent with custom instructions and personality
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="""
        You are an enthusiastic news reporter with a flair for storytelling!
        Think of yourself as a mix between a witty comedian and a sharp journalist.

        Your style guide:
        - Start with an attention-grabbing headline using emoji
        - Share news with enthusiasm and NYC attitude
        - Keep your responses concise but entertaining
        - End with a catchy sign-off like 'Back to you in the studio!'
    """,
    markdown=True,
)

# Run the agent with a message
agent.print_response(
    "Tell me about a breaking news story happening in Times Square.",
    stream=True
)
```

### Agent with Tools

Create an agent with web search capabilities and tool integration.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Create agent with DuckDuckGo search tool
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="""
        You are an enthusiastic news reporter!
        Always use the search tool to find current, accurate information.
        Present news with authentic NYC enthusiasm and local flavor.
    """,
    tools=[DuckDuckGoTools()],
    markdown=True,
)

# Agent will automatically use tools when needed
agent.print_response(
    "What's the latest headline from Wall Street?",
    stream=True
)
```

### Agent with Knowledge Base

Create an agent with persistent knowledge storage using vector search.

```python
from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.lancedb import LanceDb, SearchType

# Create knowledge base with LanceDB
knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="recipe_knowledge",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

# Add content from URL (PDF, webpage, etc.)
knowledge.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
)

# Create agent with knowledge base and web search
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="""
        You are a Thai cuisine expert!
        Always search your knowledge base first for authentic recipes.
        If information is incomplete, supplement with web searches.
    """,
    knowledge=knowledge,
    tools=[DuckDuckGoTools()],
    markdown=True,
)

# Agent automatically searches knowledge base and web as needed
agent.print_response("How do I make Pad Thai?", stream=True)
```

### Structured Output with Pydantic

Generate structured JSON responses using Pydantic models.

```python
from agno.agent import Agent, RunOutput
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from typing import List

# Define output schema
class MovieScript(BaseModel):
    name: str = Field(..., description="Movie title")
    genre: str = Field(..., description="Primary and secondary genres")
    setting: str = Field(..., description="Detailed location and time period")
    characters: List[str] = Field(..., description="4-6 main characters with roles")
    storyline: str = Field(..., description="Three-sentence plot summary")
    ending: str = Field(..., description="Movie conclusion")

# Agent with structured output (JSON mode)
json_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are an acclaimed Hollywood screenwriter. Create compelling movie concepts.",
    output_schema=MovieScript,
    use_json_mode=True,
)

# Agent with structured output (enhanced mode)
structured_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are an acclaimed Hollywood screenwriter. Create compelling movie concepts.",
    output_schema=MovieScript,
)

# Get structured response
response: RunOutput = structured_agent.run("Tokyo")
print(response.content)  # Returns MovieScript object
```

### Agent with Session Storage

Create an agent with persistent session management and conversation history.

```python
from typing import List, Optional
from agno.agent import Agent
from agno.db.base import SessionType
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.session import AgentSession

# Setup database for session storage
db = SqliteDb(db_file="tmp/agents.db")

# Configure agent with database
agent = Agent(
    user_id="user-123",
    session_id=None,  # Will auto-create or load existing
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are a helpful Thai cuisine expert.",
    db=db,
    knowledge=agent_knowledge,
    # Option 1: Add tool to read chat history
    read_chat_history=True,
    # Option 2: Automatically add history to context
    # add_history_to_context=True,
    # num_history_runs=3,
    markdown=True,
)

# Check for existing sessions
existing_sessions: List[AgentSession] = db.get_sessions(
    user_id="user-123",
    session_type=SessionType.AGENT
)

if existing_sessions:
    session_id = existing_sessions[0].session_id
    print(f"Continuing Session: {session_id}")

# Run interactive CLI app with persistence
agent.cli_app(markdown=True)
```

### Multi-Agent Teams

Coordinate multiple specialized agents working together.

```python
from typing import List
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.hackernews import HackerNewsTools
from agno.tools.newspaper4k import Newspaper4kTools
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str = Field(..., description="Article title")
    summary: str = Field(..., description="Article summary")
    reference_links: List[str] = Field(..., description="Reference links")

# Create specialized agents
hn_researcher = Agent(
    name="HackerNews Researcher",
    model=OpenAIChat("gpt-5-mini"),
    role="Gets top stories from hackernews.",
    tools=[HackerNewsTools()],
)

article_reader = Agent(
    name="Article Reader",
    model=OpenAIChat("gpt-5-mini"),
    role="Reads articles from URLs.",
    tools=[Newspaper4kTools()],
)

# Create coordinated team
hn_team = Team(
    name="HackerNews Team",
    model=OpenAIChat("gpt-5-mini"),
    members=[hn_researcher, article_reader],
    instructions=[
        "First, search hackernews for what the user is asking about.",
        "Then, ask the article reader to read the links for the stories.",
        "Important: you must provide the article reader with the links to read.",
        "Finally, provide a thoughtful and engaging summary.",
    ],
    output_schema=Article,
    add_member_tools_to_context=False,
    markdown=True,
    show_members_responses=True,
)

# Execute team task
hn_team.print_response(
    input="Write an article about the top 2 stories on hackernews",
    stream=True
)
```

### Sequential Workflows

Create multi-step workflows with agents and teams.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

# Define specialized agents
hackernews_agent = Agent(
    name="Hackernews Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[HackerNewsTools()],
    role="Extract key insights from Hackernews posts",
)

web_agent = Agent(
    name="Web Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[GoogleSearchTools()],
    role="Search the web for latest news and trends",
)

# Create research team
research_team = Team(
    name="Research Team",
    members=[hackernews_agent, web_agent],
    instructions="Research tech topics from Hackernews and the web",
)

content_planner = Agent(
    name="Content Planner",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Plan a content schedule over 4 weeks for the provided topic",
        "Ensure that I have posts for 3 posts per week",
    ],
)

# Define workflow steps
research_step = Step(
    name="Research Step",
    team=research_team,
)

content_planning_step = Step(
    name="Content Planning Step",
    agent=content_planner,
)

# Create workflow with persistence
content_creation_workflow = Workflow(
    name="Content Creation Workflow",
    description="Automated content creation from research to social media",
    db=SqliteDb(
        session_table="workflow_session",
        db_file="tmp/workflow.db",
    ),
    steps=[research_step, content_planning_step],
)

# Execute workflow
content_creation_workflow.print_response(
    input="AI trends in 2025",
    markdown=True,
)
```

### AgentOS with Web Interface

Deploy agents with FastAPI runtime and web UI.

```python
from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI

# Create agent
chat_agent = Agent(
    name="Assistant",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are a helpful AI assistant.",
    add_datetime_to_context=True,
    markdown=True,
)

# Create AgentOS with web interface
agent_os = AgentOS(
    agents=[chat_agent],
    interfaces=[AGUI(agent=chat_agent)],
)

# Get FastAPI app
app = agent_os.get_app()

# Serve with auto-reload
if __name__ == "__main__":
    agent_os.serve(app="basic:app", reload=True)

# Access web interface:
# 1. Clone AG-UI: git clone https://github.com/ag-ui-protocol/ag-ui.git
# 2. Install: cd ag-ui/typescript-sdk && pnpm install
# 3. Build integration: cd integrations/agno && pnpm run build
# 4. Start Dojo: cd ../../apps/dojo && pnpm run dev
# 5. Access at http://localhost:3000
```

### AgentOS with Database and MCP Support

Create a production-ready agent with persistence and MCP server integration.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.mcp import MCPTools

# Create agent with all features
agno_agent = Agent(
    name="Agno Agent",
    model=Claude(id="claude-sonnet-4-5"),
    db=SqliteDb(db_file="agno.db"),
    tools=[
        MCPTools(
            transport="streamable-http",
            url="https://docs.agno.com/mcp"
        )
    ],
    add_history_to_context=True,
    markdown=True,
)

# Create AgentOS runtime
agent_os = AgentOS(agents=[agno_agent])
app = agent_os.get_app()

# Run with auto-reload
if __name__ == "__main__":
    agent_os.serve(app="agno_agent:app", reload=True)

# Connect to AgentOS UI at https://os.agno.com
```

### AgentOS REST API - Create Agent Run

Execute an agent via HTTP API with streaming support.

```bash
# Non-streaming request
curl -X POST "https://api.example.com/agents/main-agent/runs" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "message=What can you help me with?" \
  -F "stream=false" \
  -F "session_id=6f6cfbfd-9643-479a-ae47-b8f32eb4d710" \
  -F "user_id=user-123"

# Streaming request with Server-Sent Events
curl -X POST "https://api.example.com/agents/main-agent/runs" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "message=Write a long story" \
  -F "stream=true" \
  -N

# With file upload (supports PDF, CSV, images, audio, video)
curl -X POST "https://api.example.com/agents/main-agent/runs" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "message=Analyze this document" \
  -F "files=@/path/to/document.pdf" \
  -F "stream=false"
```

### AgentOS REST API - Session Management

List and manage conversation sessions.

```bash
# List sessions with filtering
curl -X GET "https://api.example.com/sessions?type=agent&user_id=user-123&limit=10&sort_order=desc" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# {
#   "data": [
#     {
#       "session_id": "6f6cfbfd-9643-479a-ae47-b8f32eb4d710",
#       "session_name": "What tools do you have?",
#       "session_state": {},
#       "created_at": "2025-09-05T16:02:09Z",
#       "updated_at": "2025-09-05T16:02:09Z"
#     }
#   ]
# }

# Get specific session details
curl -X GET "https://api.example.com/sessions/6f6cfbfd-9643-479a-ae47-b8f32eb4d710" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Delete session
curl -X DELETE "https://api.example.com/sessions/6f6cfbfd-9643-479a-ae47-b8f32eb4d710" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### AgentOS REST API - Memory Management

Create and retrieve user memories for context.

```bash
# Create memory
curl -X POST "https://api.example.com/memories" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "memory": "User prefers technical explanations with code examples",
    "user_id": "user-456",
    "topics": ["preferences", "communication_style", "technical"]
  }'

# Response:
# {
#   "memory_id": "mem-123",
#   "memory": "User prefers technical explanations with code examples",
#   "topics": ["preferences", "communication_style", "technical"],
#   "user_id": "user-456",
#   "created_at": "2025-01-15T10:30:00Z",
#   "updated_at": "2025-01-15T10:30:00Z"
# }

# List memories with filtering
curl -X GET "https://api.example.com/memories?user_id=user-123&topics=preferences,technical&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search within memory content
curl -X GET "https://api.example.com/memories?user_id=user-123&search_content=coding" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update memory
curl -X PATCH "https://api.example.com/memories/mem-123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "memory": "User prefers detailed technical explanations with Python code examples"
  }'
```

### AgentOS REST API - Knowledge Base Management

Upload and search knowledge base content.

```bash
# Upload file to knowledge base
curl -X POST "https://api.example.com/knowledge/content" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "name=Technical Documentation" \
  -F "description=API documentation for v2.0" \
  -F 'metadata={"category": "documentation", "priority": "high"}'

# Response (202 Accepted - processing asynchronously):
# {
#   "id": "content-123",
#   "name": "example-document.pdf",
#   "description": "Sample document for processing",
#   "metadata": {"category": "documentation", "priority": "high"},
#   "status": "processing"
# }

# Upload from URL
curl -X POST "https://api.example.com/knowledge/content" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "url=https://example.com/article" \
  -F "name=Blog Article"

# Search knowledge base (vector search)
curl -X POST "https://api.example.com/knowledge/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "JavaScript React best practices",
    "search_type": "semantic",
    "max_results": 10
  }'

# Response:
# {
#   "data": [
#     {
#       "id": "doc_123",
#       "content": "React best practices include...",
#       "name": "react_guide",
#       "meta_data": {"page": 1, "chunk": 1},
#       "reranking_score": 0.95,
#       "content_id": "content_456"
#     }
#   ],
#   "meta": {
#     "page": 1,
#     "limit": 20,
#     "total_pages": 2,
#     "total_count": 35
#   }
# }

# List all knowledge base content
curl -X GET "https://api.example.com/knowledge/content?limit=20&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### AgentOS REST API - Agent and Configuration Management

Retrieve agent configurations and OS settings.

```bash
# List all agents
curl -X GET "https://api.example.com/agents" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# [
#   {
#     "id": "main-agent",
#     "name": "Main Agent",
#     "db_id": "c6bf0644-feb8-4930-a305-380dae5ad6aa",
#     "model": {
#       "name": "OpenAIChat",
#       "model": "gpt-4o",
#       "provider": "OpenAI"
#     },
#     "sessions": {"session_table": "agno_sessions"},
#     "knowledge": {"knowledge_table": "main_knowledge"},
#     "system_message": {
#       "markdown": true,
#       "add_datetime_to_context": true
#     }
#   }
# ]

# Get specific agent details
curl -X GET "https://api.example.com/agents/main-agent" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get OS configuration
curl -X GET "https://api.example.com/config" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response includes available models, databases, agents, teams, workflows:
# {
#   "id": "demo",
#   "description": "Example AgentOS configuration",
#   "available_models": [],
#   "databases": ["9c884dc4-9066-448c-9074-ef49ec7eb73c"],
#   "agents": [
#     {"id": "main-agent", "name": "Main Agent", "db_id": "..."}
#   ],
#   "teams": [],
#   "workflows": [],
#   "interfaces": []
# }

# List teams
curl -X GET "https://api.example.com/teams" \
  -H "Authorization: Bearer YOUR_TOKEN"

# List workflows
curl -X GET "https://api.example.com/workflows" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get available models
curl -X GET "https://api.example.com/models" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Summary and Integration Patterns

Agno provides a complete framework for building production-ready AI agent systems, from simple single agents to complex multi-agent teams and workflows. The framework excels in scenarios requiring persistent conversation history, contextual memory across sessions, knowledge base integration with semantic search, and coordinated multi-agent collaboration. Common use cases include customer support chatbots with memory, research assistants that coordinate multiple specialized agents, document analysis systems with knowledge bases, content creation workflows with multiple processing stages, and interactive AI applications with web interfaces.

The integration patterns are flexible and composable. For simple applications, use standalone agents with tools and knowledge bases. For complex systems, orchestrate multiple agents as teams with shared context or as workflows with sequential/parallel execution. The AgentOS runtime provides production-ready FastAPI endpoints for all agent operations, session management, memory storage, and knowledge base queries. All AgentOS deployments are private by design, running entirely in your infrastructure with no external data transmission. Connect the AgentOS UI control plane for real-time testing, monitoring, and debugging without sacrificing data privacy or security. The framework supports any LLM provider, any database backend, and seamless integration with external APIs through the extensible tools system and MCP protocol support.
---
inclusion: always
---
<!------------------------------------------------------------------------------------
   Add rules to this file or a short description and have Kiro refine them for you.
   
   Learn about inclusion modes: https://kiro.dev/docs/steering/#inclusion-modes
-------------------------------------------------------------------------------------> 