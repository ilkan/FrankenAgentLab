# Marketplace Blueprints

This directory contains ready-to-use agent blueprints for the FrankenAgent Lab marketplace.

## Available Blueprints

### 🔍 Web Search & Research

#### 1. **Web Search Expert** (`tavily_search_expert.yaml`)

- **Tool:** Tavily Search
- **Use Case:** Advanced web search and research
- **Features:**
  - Advanced search depth for comprehensive results
  - AI-generated answer summaries
  - Markdown-formatted results
  - Source citations
- **Best For:** Research, fact-checking, current events

#### 2. **News Aggregator** (`news_aggregator.yaml`)

- **Tool:** Tavily Search
- **Use Case:** Find and summarize news from multiple sources
- **Features:**
  - Focus on recent news (24-48 hours)
  - Multi-source aggregation
  - Key facts extraction
  - Perspective comparison
- **Best For:** Staying informed, news monitoring

#### 3. **Research Powerhouse** (`research_powerhouse.yaml`)

- **Tools:** Tavily Search + HTTP Tool
- **Use Case:** Comprehensive research combining web search and API data
- **Features:**
  - Web search for context
  - API calls for structured data
  - Cross-referencing sources
  - Comprehensive synthesis
- **Best For:** In-depth research, data analysis

---

### 👥 Multi-Agent Teams

#### 4. **Research & Writing Team** (`research_writing_team.yaml`) ⭐ NEW

- **Type:** Team Mode (Multi-Agent)
- **Tools:** Tavily Search
- **Use Case:** Collaborative research and content creation
- **Team Members:**
  - 🔍 Research Specialist - Finds and analyzes information
  - ✍️ Content Writer - Creates engaging articles
- **Features:**
  - Specialized agent roles
  - Coordinated workflow
  - Research-backed content
  - Professional writing quality
- **Best For:** Article writing, content creation, research reports

---

### 🌐 API Integration

#### 5. **GitHub API Assistant** (`github_api_assistant.yaml`)

- **Tool:** HTTP Tool
- **Use Case:** Manage GitHub repositories, issues, and PRs
- **Features:**
  - List repos, issues, PRs
  - Create and update resources
  - Search GitHub
  - Natural language interface
- **Best For:** GitHub automation, repository management

#### 6. **REST API Tester** (`rest_api_tester.yaml`)

- **Tool:** HTTP Tool
- **Use Case:** Test and interact with any REST API
- **Features:**
  - All HTTP methods (GET, POST, PUT, DELETE, PATCH)
  - Flexible endpoint testing
  - Response analysis
  - Error debugging
- **Best For:** API testing, debugging, exploration

#### 7. **Weather Assistant** (`weather_assistant.yaml`)

- **Tool:** HTTP Tool (OpenWeatherMap)
- **Use Case:** Get weather forecasts and conditions
- **Features:**
  - Current weather by city
  - 5-day forecasts
  - Weather alerts
  - Temperature conversions
- **Best For:** Weather information, travel planning

#### 8. **Crypto Price Tracker** (`crypto_tracker.yaml`)

- **Tool:** HTTP Tool (CoinGecko)
- **Use Case:** Track cryptocurrency prices and market data
- **Features:**
  - Real-time prices
  - 24h price changes
  - Market cap and volume
  - Multi-coin comparison
- **Best For:** Crypto monitoring, market analysis

---

### 📚 Documentation & Knowledge

#### 9. **AWS Documentation Expert** (`aws_docs_expert.yaml`)

- **Tool:** MCP Tool (AWS Docs Server)
- **Use Case:** Search and understand AWS documentation
- **Features:**
  - Search AWS docs
  - Read specific pages
  - Best practices
  - Step-by-step guidance
- **Best For:** AWS learning, troubleshooting, architecture

---

## Tool Types

### Tavily Search

**Configuration:**

```yaml
type: "tavily_search"
config:
  search_depth: "advanced" # "basic" or "advanced"
  max_tokens: 6000 # Max tokens in results
  include_answer: true # Include AI summary
  format: "markdown" # "json" or "markdown"
  use_search_context: true # Enhanced context
```

**Requirements:**

- Tavily API key (stored in user settings)

### HTTP Tool

**Configuration:**

```yaml
type: "http_tool"
config:
  name: "API Client"
  description: "Make HTTP requests"
  base_url: "https://api.example.com" # Optional
  default_headers:
    Accept: "application/json"
  timeout: 30
```

**Requirements:**

- No API key needed for public APIs
- Some APIs may require authentication headers

### MCP Tool

**Configuration:**

```yaml
type: "mcp_tool"
config:
  server_name: "aws-docs"
  command: "uvx"
  args:
    - "awslabs.aws-documentation-mcp-server@latest"
  env:
    FASTMCP_LOG_LEVEL: "ERROR"
  timeout: 60
```

**Requirements:**

- `uvx` or `npx` installed
- MCP server package available

---

## How to Use

### 1. Import from Marketplace

1. Open FrankenAgent Lab
2. Click "Marketplace"
3. Browse available blueprints
4. Click "Use This Blueprint"

### 2. Configure API Keys

Some blueprints require API keys:

- **Tavily Search**: Add Tavily API key in Settings
- **OpenWeatherMap**: Add API key as query parameter or header
- **CoinGecko**: No API key needed (public API)
- **GitHub**: Optional - add personal access token for private repos

### 3. Test the Agent

1. Load the blueprint
2. Start a conversation
3. Ask relevant questions
4. Review tool calls and responses

### 4. Customize

- Modify system prompts
- Adjust guardrails (max_tool_calls, timeout)
- Add/remove tools
- Change LLM model or temperature

---

## Blueprint Structure

All blueprints follow the FrankenAgent schema:

```yaml
name: "Agent Name"
description: "What this agent does"
version: "1.0"

head: # LLM Configuration
  provider: "openai"
  model: "gpt-4o"
  system_prompt: |
    Agent instructions...
  temperature: 0.7
  max_tokens: 2000

arms: # Tools
  - type: "tool_type"
    config:
      # Tool-specific config

legs: # Execution Mode
  execution_mode: "single_agent"

heart: # Memory
  memory_enabled: true
  history_length: 10

spine: # Guardrails
  max_tool_calls: 15
  timeout_seconds: 90
```

---

## Testing

Run the validation script to test all blueprints:

```bash
python test_blueprints.py
```

This validates:

- ✅ YAML syntax
- ✅ Schema compliance
- ✅ Tool configuration
- ✅ Compilation readiness

---

## Contributing

To add a new marketplace blueprint:

1. Create a new YAML file in this directory
2. Follow the blueprint structure above
3. Include comprehensive system prompt
4. Test with `python test_blueprints.py`
5. Document in this README

---

## Support

For issues or questions:

- Check `TOOL_CONFIGURATION_VERIFICATION.md` for tool details
- Review `CODE_STRUCTURE_ANALYSIS.md` for architecture
- Open an issue on GitHub

---

**Created:** 2025-11-30  
**Updated:** 2025-12-03  
**Total Blueprints:** 9  
**Tool Coverage:** Tavily (4), HTTP (5), MCP (1)  
**Execution Modes:** Single Agent (8), Team (1)
