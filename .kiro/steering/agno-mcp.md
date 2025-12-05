# Model Context Protocol (MCP)

> Learn how to use MCP with Agno to enable your agents to interact with external systems through a standardized interface.

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) enables Agents to interact with external systems through a standardized interface.
You can connect your Agents to any MCP server, using Agno's MCP integration.

Below is a simple example shows how to connect an Agent to the Agno MCP server:

```python  theme={null}
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools

# Create the Agent
agno_agent = Agent(
    name="Agno Agent",
    model=Claude(id="claude-sonnet-4-0"),
    # Add the Agno MCP server to the Agent
    tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
)
```

## The Basic Flow

<Steps>
  <Step title="Find the MCP server you want to use">
    You can use any working MCP server. To see some examples, you can check [this GitHub repository](https://github.com/modelcontextprotocol/servers), by the maintainers of the MCP themselves.
  </Step>

  <Step title="Initialize the MCP integration">
    Initialize the `MCPTools` class and connect to the MCP server.
    The recommended way to define the MCP server is to use the `command` or `url` parameters.
    With `command`, you can pass the command used to run the MCP server you want. With `url`, you can pass the URL of the running MCP server you want to use.

    For example, to connect to the Agno documentation MCP server, you can do the following:

    ```python  theme={null}
    from agno.tools.mcp import MCPTools

    # Initialize and connect to the MCP server
    mcp_tools = MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp"))
    await mcp_tools.connect()
    ```
  </Step>

  <Step title="Provide the MCPTools to the Agent">
    When initializing the Agent, pass the `MCPTools` instance in the `tools` parameter. Remember to close the connection when you're done.

    The agent will now be ready to use the MCP server:

    ```python  theme={null}
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from agno.tools.mcp import MCPTools

    # Initialize and connect to the MCP server
    mcp_tools = MCPTools(url="https://docs.agno.com/mcp")
    await mcp_tools.connect()

    try:
        # Setup and run the agent
        agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
        await agent.aprint_response("Tell me more about MCP support in Agno", stream=True)
    finally:
        # Always close the connection when done
        await mcp_tools.close()
    ```
  </Step>
</Steps>

### Example: Filesystem Agent

Here's a filesystem agent that uses the [Filesystem MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) to explore and analyze files:

```python filesystem_agent.py theme={null}
import asyncio
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools


async def run_agent(message: str) -> None:
    """Run the filesystem agent with the given message."""

    file_path = "<path to the directory you want to explore>"

    # Initialize and connect to the MCP server to access the filesystem
    mcp_tools = MCPTools(command=f"npx -y @modelcontextprotocol/server-filesystem {file_path}")
    await mcp_tools.connect()

    try:
        agent = Agent(
            model=OpenAIChat(id="gpt-5-mini"),
            tools=[mcp_tools],
            instructions=dedent("""\
                You are a filesystem assistant. Help users explore files and directories.

                - Navigate the filesystem to answer questions
                - Use the list_allowed_directories tool to find directories that you can access
                - Provide clear context about files you examine
                - Use headings to organize your responses
                - Be concise and focus on relevant information\
            """),
            markdown=True,
        )

        # Run the agent
        await agent.aprint_response(message, stream=True)
    finally:
        # Always close the connection when done
        await mcp_tools.close()


# Example usage
if __name__ == "__main__":
    # Basic example - exploring project license
    asyncio.run(run_agent("What is the license for this project?"))
```

## Connecting your MCP server

### Using `connect()` and `close()`

It is recommended to use the `connect()` and `close()` methods to manage the connection lifecycle of the MCP server.

```python  theme={null}
mcp_tools = MCPTools(command="uvx mcp-server-git")
await mcp_tools.connect()
```

After you're done, you should close the connection to the MCP server.

```python  theme={null}
await mcp_tools.close()
```

<Check>
  This is the recommended way to manage the connection lifecycle of the MCP server when using `Agent` or `Team` instances.
</Check>

### Automatic Connection Management

If you pass the `MCPTools` instance to the `Agent` or `Team` instances without first calling `connect()`, the connection will be managed automatically.

For example:

```python  theme={null}
mcp_tools = MCPTools(command="uvx mcp-server-git")
agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
await agent.aprint_response("What is the license for this project?", stream=True)  # The connection is established and closed on each run.
```

<Note>
  Here the connection to the MCP server (in the case of hosted MCP servers) is established and closed on each run.
  Additionally the list of available tools is refreshed on each run.

  This has an impact on performance and is not recommended for production use.
</Note>

### Using Async Context Manager

If you prefer, you can also use `MCPTools` or `MultiMCPTools` as async context managers for automatic resource cleanup:

```python  theme={null}
async with MCPTools(command="uvx mcp-server-git") as mcp_tools:
    agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
    await agent.aprint_response("What is the license for this project?", stream=True)
```

This pattern automatically handles connection and cleanup, but the explicit `.connect()` and `.close()` methods provide more control over connection lifecycle.

### Automatic Connection Management in AgentOS

When using MCPTools within AgentOS, the lifecycle is automatically managed. No need to manually connect or disconnect the `MCPTools` instance. This does not automatically refresh connections, you can use [`refresh_connection`](#connection-refresh) to do so.

See the [AgentOS + MCPTools](/agent-os/mcp/tools) page for more details.

<Check>
  This is the recommended way to manage the connection lifecycle of the MCP server when using `AgentOS`.
</Check>

## Connection Refresh

You can set `refresh_connection` on the `MCPTools` and `MultiMCPTools` instances to refresh the connection to the MCP server on each run.

```python  theme={null}
mcp_tools = MCPTools(command="uvx mcp-server-git", refresh_connection=True)
await mcp_tools.connect()

agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
await agent.aprint_response("What is the license for this project?", stream=True)  # The connection will be refreshed on each run.

await mcp_tools.close()
```

### How it works

* When you call the `connect()` method, a new session is established with the MCP server. If that server becomes unavailable, that connection is closed and a new one has to be established.
* If you set `refresh_connection` to `True`, each time the agent is run the connection to the MCP server is checked and re-established if needed, and the list of available tools is then refreshed.
* This is particularly useful for hosted MCP servers that are prone to restarts or that often change their schema or list of tools.
* It is recommended to only use this when you manually manage the connection lifecycle of the MCP server, or when using agents/teams with [`MCPTools` in `AgentOS`](/agent-os/mcp/tools).

## Transports

Transports in the Model Context Protocol (MCP) define how messages are sent and received. The Agno integration supports the three existing types:

* [stdio](https://modelcontextprotocol.io/docs/basics/transports#standard-input%2Foutput-stdio) -> See the [stdio transport documentation](/basics/tools/mcp/transports/stdio)
* [Streamable HTTP](https://modelcontextprotocol.io/specification/draft/basic/transports#streamable-http) -> See the [streamable HTTP transport documentation](/basics/tools/mcp/transports/streamable_http)
* [SSE](https://modelcontextprotocol.io/docs/basics/transports#server-sent-events-sse) -> See the [SSE transport documentation](/basics/tools/mcp/transports/sse)

<Note>
  The stdio (standard input/output) transport is the default one in Agno's `MCPTools` and `MultiMCPTools`.
</Note>

## Best Practices

1. **Resource Cleanup**: Always close MCP connections when done to prevent resource leaks:

```python  theme={null}
mcp_tools = MCPTools(command="uvx mcp-server-git")
await mcp_tools.connect()

try:
    # Your agent code here
    pass
finally:
    await mcp_tools.close()
```

2. **Error Handling**: Always include proper error handling for MCP server connections and operations.

3. **Clear Instructions**: Provide clear and specific instructions to your agent:

```python  theme={null}
instructions = """
You are a filesystem assistant. Help users explore files and directories.
- Navigate the filesystem to answer questions
- Use the list_allowed_directories tool to find accessible directories
- Provide clear context about files you examine
- Be concise and focus on relevant information
"""
```

## Developer Resources

* See how to use MCP with AgentOS [here](/agent-os/mcp/tools).
* Find examples of Agents that use MCP [here](/basics/tools/mcp/usage/airbnb).
* Find a collection of MCP servers [here](https://github.com/modelcontextprotocol/servers).


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt



# MCP Toolbox

> Learn how to use MCPToolbox with Agno to connect to MCP Toolbox for Databases with tool filtering capabilities.

<Badge icon="code-branch" color="orange">
  <Tooltip tip="Introduced in v2.0.9" cta="View release notes" href="https://github.com/agno-agi/agno/releases/tag/v2.0.9">v2.0.9</Tooltip>
</Badge>

**MCPToolbox** enables Agents to connect to Google's [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/getting-started/introduction/) with advanced filtering capabilities. It extends Agno's `MCPTools` functionality to filter tools by toolset or tool name, allowing agents to load only the specific database tools they need.

## Prerequisites

You'll need the following to use MCPToolbox:

```bash  theme={null}
pip install toolbox-core
```

Our default setup will also require you to have Docker or Podman installed, to run the MCP Toolbox server and database for the examples.

## Quick Start

Get started with MCPToolbox instantly using our fully functional demo.

```bash  theme={null}
# Clone the repo and navigate to the demo folder
git clone https://github.com/agno-agi/agno.git
cd agno/cookbook/tools/mcp/mcp_toolbox_demo

# Start the database and MCP Toolbox servers

# With Docker and Docker Compose
docker-compose up -d

# With Podman
podman compose up -d

# Install dependencies
uv sync

# Set your API key and run the basic agent
export OPENAI_API_KEY="your_openai_api_key"
uv run agent.py
```

This starts a PostgreSQL database with sample hotel data and an MCP Toolbox server that exposes database operations as filtered tools.

## Verification

To verify that your docker/podman setup is working correctly, you can check the database connection:

```bash  theme={null}
# Using Docker Compose
docker-compose exec db psql -U toolbox_user -d toolbox_db -c "SELECT COUNT(*) FROM hotels;"

# Using Podman
podman exec db psql -U toolbox_user -d toolbox_db -c "SELECT COUNT(*) FROM hotels;"
```

## Basic Example

Here's the simplest way to use MCPToolbox (after running the Quick Start setup):

```python  theme={null}
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp_toolbox import MCPToolbox

async def main():
    # Connect to the running MCP Toolbox server and filter to hotel tools only
    async with MCPToolbox(
        url="http://127.0.0.1:5001",
        toolsets=["hotel-management"]  # Only load hotel search tools
    ) as toolbox:
        agent = Agent(
            model=OpenAIChat(),
            tools=[toolbox],
            instructions="You help users find hotels. Always mention hotel ID, name, location, and price tier."
        )
        
        # Ask the agent to find hotels
        await agent.aprint_response("Find luxury hotels in Zurich")

# Run the example
asyncio.run(main())
```

## How MCPToolbox Works

MCPToolbox solves the **tool overload problem**. Without filtering, your agent gets overwhelmed with too many database tools:

**Without MCPToolbox (50+ tools):**

```python  theme={null}
# Agent gets ALL database tools - overwhelming!
tools = MCPTools(url="http://127.0.0.1:5001")  # 50+ tools
```

**With MCPToolbox (3 relevant tools):**

```python  theme={null}
# Agent gets only hotel management tools - focused!
tools = MCPToolbox(url="http://127.0.0.1:5001", toolsets=["hotel-management"])  # 3 tools
```

**The flow:**

1. MCP Toolbox Server exposes 50+ database tools
2. MCPToolbox connects and loads ALL tools internally
3. Filters to only the `hotel-management` toolset (3 tools)
4. Agent sees only the 3 relevant tools and stays focused

## Advanced Usage

### Multiple Toolsets

Load tools from multiple related toolsets:

```python cookbook/tools/mcp/mcp_toolbox_for_db.py theme={null}
import asyncio
from textwrap import dedent
from agno.agent import Agent
from agno.tools.mcp_toolbox import MCPToolbox

url = "http://127.0.0.1:5001"

async def run_agent(message: str = None) -> None:
    """Run an interactive CLI for the Hotel agent with the given message."""

    async with MCPToolbox(
        url=url, toolsets=["hotel-management", "booking-system"]
    ) as db_tools:
        print(db_tools.functions)  # Print available tools for debugging
        agent = Agent(
            tools=[db_tools],
            instructions=dedent(
                """ \
                You're a helpful hotel assistant. You handle hotel searching, booking and
                cancellations. When the user searches for a hotel, mention it's name, id,
                location and price tier. Always mention hotel ids while performing any
                searches. This is very important for any operations. For any bookings or
                cancellations, please provide the appropriate confirmation. Be sure to
                update checkin or checkout dates if mentioned by the user.
                Don't ask for confirmations from the user.
            """
            ),
            markdown=True,
            show_tool_calls=True,
            add_history_to_messages=True,
            debug_mode=True,
        )

        await agent.acli_app(message=message, stream=True)

if __name__ == "__main__":
    asyncio.run(run_agent(message=None))
```

### Custom Authentication and Parameters

For production scenarios with authentication:

```python  theme={null}
async def production_example():
    async with MCPToolbox(url=url) as toolbox:
        # Load with authentication and bound parameters
        hotel_tools = await toolbox.load_toolset(
            "hotel-management",
            auth_token_getters={"hotel_api": lambda: "your-hotel-api-key"},
            bound_params={"region": "us-east-1"},
        )

        booking_tools = await toolbox.load_toolset(
            "booking-system",
            auth_token_getters={"booking_api": lambda: "your-booking-api-key"},
            bound_params={"environment": "production"},
        )

        # Use individual tools instead of the toolbox
        all_tools = hotel_tools + booking_tools[:2]  # First 2 booking tools only
        
        agent = Agent(tools=all_tools, instructions="Hotel management with auth.")
        await agent.aprint_response("Book a hotel for tonight")
```

### Manual Connection Management

For explicit control over connections:

```python  theme={null}
async def manual_connection_example():
    # Initialize without auto-connection
    toolbox = MCPToolbox(url=url, toolsets=["hotel-management"])
    
    try:
        await toolbox.connect()
        agent = Agent(
            tools=[toolbox],
            instructions="Hotel search assistant.",
            markdown=True
        )
        await agent.aprint_response("Show me hotels in Basel")
    finally:
        await toolbox.close()  # Always clean up
```

## Toolkit Params

| Parameter   | Type                       | Default             | Description                                                                |
| ----------- | -------------------------- | ------------------- | -------------------------------------------------------------------------- |
| `url`       | `str`                      | -                   | Base URL for the toolbox service (automatically appends "/mcp" if missing) |
| `toolsets`  | `Optional[List[str]]`      | `None`              | List of toolset names to filter tools by. Cannot be used with `tool_name`. |
| `tool_name` | `Optional[str]`            | `None`              | Single tool name to load. Cannot be used with `toolsets`.                  |
| `headers`   | `Optional[Dict[str, Any]]` | `None`              | HTTP headers for toolbox client requests                                   |
| `transport` | `str`                      | `"streamable-http"` | MCP transport protocol. Options: `"stdio"`, `"sse"`, `"streamable-http"`   |

<Note>
  Only one of `toolsets` or `tool_name` can be specified. The implementation validates this and raises a `ValueError` if both are provided.
</Note>

## Toolkit Functions

| Function                                                                                            | Description                                                    |
| --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `async connect()`                                                                                   | Initialize and connect to both MCP server and toolbox client   |
| `async load_tool(tool_name, auth_token_getters={}, bound_params={})`                                | Load a single tool by name with optional authentication        |
| `async load_toolset(toolset_name, auth_token_getters={}, bound_params={}, strict=False)`            | Load all tools from a specific toolset                         |
| `async load_multiple_toolsets(toolset_names, auth_token_getters={}, bound_params={}, strict=False)` | Load tools from multiple toolsets                              |
| `async load_toolset_safe(toolset_name)`                                                             | Safely load a toolset and return tool names for error handling |
| `get_client()`                                                                                      | Get the underlying ToolboxClient instance                      |
| `async close()`                                                                                     | Close both toolbox client and MCP client connections           |

## Demo Examples

The complete demo includes multiple working patterns:

* **[Basic Agent](https://github.com/agno-agi/agno/blob/main/cookbook/tools/mcp/mcp_toolbox_demo/agent.py)**: Simple hotel assistant with toolset filtering
* **[AgentOS Integration](https://github.com/agno-agi/agno/blob/main/cookbook/tools/mcp/mcp_toolbox_demo/agent_os.py)**: Integration with AgentOS control plane
* **[Workflow Integration](https://github.com/agno-agi/agno/blob/main/cookbook/tools/mcp/mcp_toolbox_demo/hotel_management_workflows.py)**: Using MCPToolbox in Agno workflows
* **[Type-Safe Agent](https://github.com/agno-agi/agno/blob/main/cookbook/tools/mcp/mcp_toolbox_demo/hotel_management_typesafe.py)**: Implementation with Pydantic models

You can use `include_tools` or `exclude_tools` to modify the list of tools the agent has access to. Learn more about [selecting tools](/basics/tools/selecting-tools).

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/mcp_toolbox.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/mcp/mcp_toolbox_demo)

For more information about MCP Toolbox for Databases, visit the [official documentation](https://googleapis.github.io/genai-toolbox/getting-started/introduction/).


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt


# Multiple MCP Servers

> Understanding how to connect to multiple MCP servers with Agno

Agno's MCP integration also supports handling connections to multiple servers, specifying server parameters and using your own MCP servers

There are two approaches to this:

1. Using multiple `MCPTools` instances
2. Using a single `MultiMCPTools` instance

## Using multiple `MCPTools` instances

```python multiple_mcp_servers.py theme={null}
import asyncio
import os

from agno.agent import Agent
from agno.tools.mcp import MCPTools


async def run_agent(message: str) -> None:
    """Run the Airbnb and Google Maps agent with the given message."""

    env = {
        **os.environ,
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
    }

    # Initialize and connect to multiple MCP servers
    airbnb_tools = MCPTools(command="npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt")
    google_maps_tools = MCPTools(command="npx -y @modelcontextprotocol/server-google-maps", env=env)
    await airbnb_tools.connect()
    await google_maps_tools.connect()

    try:
        agent = Agent(
            tools=[airbnb_tools, google_maps_tools],
            markdown=True,
        )

        await agent.aprint_response(message, stream=True)
    finally:
        await airbnb_tools.close()
        await google_maps_tools.close()


# Example usage
if __name__ == "__main__":
    # Pull request example
    asyncio.run(
        run_agent(
            "What listings are available in Cape Town for 2 people for 3 nights from 1 to 4 August 2025?"
        )
    )
```

## Using a single `MultiMCPTools` instance

```python multiple_mcp_servers.py theme={null}
import asyncio
import os

from agno.agent import Agent
from agno.tools.mcp import MultiMCPTools


async def run_agent(message: str) -> None:
    """Run the Airbnb and Google Maps agent with the given message."""

    env = {
        **os.environ,
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
    }

    # Initialize and connect to multiple MCP servers
    mcp_tools = MultiMCPTools(
        commands=[
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
            "npx -y @modelcontextprotocol/server-google-maps",
        ],
        env=env,
    )
    await mcp_tools.connect()

    try:
        agent = Agent(
            tools=[mcp_tools],
            markdown=True,
        )

        await agent.aprint_response(message, stream=True)
    finally:
        # Always close the connection when done
        await mcp_tools.close()


# Example usage
if __name__ == "__main__":
    # Pull request example
    asyncio.run(
        run_agent(
            "What listings are available in Cape Town for 2 people for 3 nights from 1 to 4 August 2025?"
        )
    )
```

### Allowing partial failures with `MultiMCPTools`

If you are connecting to multiple MCP servers using the `MultiMCPTools` class, an error will be raised by default if connection to any MCP server fails.

If you want to avoid raising in that case, you can set the `allow_partial_failures` parameter to `True`.

This is useful if you are connecting to MCP servers that are not always available, and don't want to exit your program if one of the servers is not available.

```python  theme={null}
import asyncio
from os import getenv

from agno.agent import Agent
from agno.tools.mcp import MultiMCPTools


async def run_agent(message: str) -> None:
    # Initialize the MCP tools
    mcp_tools = MultiMCPTools(
        [
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
            "npx -y @modelcontextprotocol/server-brave-search",
        ],
        env={
            "BRAVE_API_KEY": getenv("BRAVE_API_KEY"),
        },
        timeout_seconds=30,
        # Set the allow_partial_failure to True to allow for partial failure connecting to the MCP servers
        allow_partial_failure=True,
    )

    # Connect to the MCP servers
    await mcp_tools.connect()

    # Use the MCP tools with an Agent
    agent = Agent(
        tools=[mcp_tools],
        markdown=True,
    )
    await agent.aprint_response(message)

    # Close the MCP connection
    await mcp_tools.close()


# Example usage
if __name__ == "__main__":
    asyncio.run(run_agent("What listings are available in Barcelona tonight?"))
    asyncio.run(run_agent("What's the fastest way to get to Barcelona from London?"))
```

## Avoiding tool name collisions

When using multiple MCP servers, you may encounter tool name collisions. This often happens when the same tool is available in multiple of the servers you are using.

To avoid this, you can use the `tool_name_prefix` parameter. This will add the given prefix to all tool names coming from the MCPTools instance.

```python  theme={null}
import asyncio

from agno.agent.agent import Agent
from agno.tools.mcp import MCPTools


async def run_agent():
    # Development environment tools
    dev_tools = MCPTools(
        transport="streamable-http",
        url="https://docs.agno.com/mcp",
        # By providing this tool_name_prefix, all the tool names will be prefixed with "dev_"
        tool_name_prefix="dev",
    )
    await dev_tools.connect()

    agent = Agent(tools=[dev_tools])
    await agent.aprint_response("Which tools do you have access to? List them all.")

    await dev_tools.close()


if __name__ == "__main__":
    asyncio.run(run_agent())
```


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt


# Stdio Transport

The stdio (standard input/output) transport is the default one in Agno's integration. It works best for local integrations.

To use it, simply initialize the `MCPTools` class with the `command` argument.
The command you want to pass is the one used to run the MCP server the agent will have access to.

For example `uvx mcp-server-git`, which runs a [git MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/git):

```python  theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

# Initialize and connect to the MCP server
# Can also use custom binaries: command="./my-mcp-server"
mcp_tools = MCPTools(command="uvx mcp-server-git")
await mcp_tools.connect()

try:
    agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
    await agent.aprint_response("What is the license for this project?", stream=True)
finally:
    # Always close the connection when done
    await mcp_tools.close()
```

You can also use multiple MCP servers at once, with the `MultiMCPTools` class. For example:

```python  theme={null}
import asyncio
import os

from agno.agent import Agent
from agno.tools.mcp import MultiMCPTools


async def run_agent(message: str) -> None:
    """Run the Airbnb and Google Maps agent with the given message."""

    env = {
        **os.environ,
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
    }

    # Initialize and connect to multiple MCP servers
    mcp_tools = MultiMCPTools(
        commands=[
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
            "npx -y @modelcontextprotocol/server-google-maps",
        ],
        env=env,
    )
    await mcp_tools.connect()

    try:
        agent = Agent(
            tools=[mcp_tools],
            markdown=True,
        )

        await agent.aprint_response(message, stream=True)
    finally:
        # Always close the connection when done
        await mcp_tools.close()


# Example usage
if __name__ == "__main__":
    # Pull request example
    asyncio.run(
        run_agent(
            "What listings are available in Cape Town for 2 people for 3 nights from 1 to 4 August 2025?"
        )
    )
```


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt


# Streamable HTTP Transport

The new [Streamable HTTP transport](https://modelcontextprotocol.io/specification/draft/basic/transports#streamable-http) replaces the HTTP+SSE transport from protocol version `2024-11-05`.

This transport enables the MCP server to handle multiple client connections, and can also use SSE for server-to-client streaming.

To use it, initialize the `MCPTools` passing the URL of the MCP server and setting the transport to `streamable-http`:

```python  theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

# Initialize and connect to the Streamable HTTP MCP server
mcp_tools = MCPTools(url="https://docs.agno.com/mcp", transport="streamable-http")
await mcp_tools.connect()

try:
    agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
    await agent.aprint_response("What can you tell me about MCP support in Agno?", stream=True)
finally:
    # Always close the connection when done
    await mcp_tools.close()
```

You can also use the `server_params` argument to define the MCP connection. This way you can specify the headers to send to the MCP server with every request, and the timeout values:

```python  theme={null}
from agno.tools.mcp import MCPTools, StreamableHTTPClientParams

server_params = StreamableHTTPClientParams(
    url=...,
    headers=...,
    timeout=...,
    sse_read_timeout=...,
    terminate_on_close=...,
)

# Initialize and connect using server parameters
mcp_tools = MCPTools(server_params=server_params, transport="streamable-http")
await mcp_tools.connect()

try:
    # Use mcp_tools with your agent
    pass
finally:
    await mcp_tools.close()
```

## Complete example

Let's set up a simple local server and connect to it using the Streamable HTTP transport:

<Steps>
  <Step title="Setup the server">
    ```python streamable_http_server.py theme={null}
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("calendar_assistant")


    @mcp.tool()
    def get_events(day: str) -> str:
        return f"There are no events scheduled for {day}."


    @mcp.tool()
    def get_birthdays_this_week() -> str:
        return "It is your mom's birthday tomorrow"


    if __name__ == "__main__":
        mcp.run(transport="streamable-http")
    ```
  </Step>

  <Step title="Setup the client">
    ```python streamable_http_client.py theme={null}
    import asyncio

    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from agno.tools.mcp import MCPTools, MultiMCPTools

    # This is the URL of the MCP server we want to use.
    server_url = "http://localhost:8000/mcp"


    async def run_agent(message: str) -> None:
        # Initialize and connect to the Streamable HTTP MCP server
        mcp_tools = MCPTools(transport="streamable-http", url=server_url)
        await mcp_tools.connect()

        try:
            agent = Agent(
                model=OpenAIChat(id="gpt-5-mini"),
                tools=[mcp_tools],
                markdown=True,
            )
            await agent.aprint_response(message=message, stream=True, markdown=True)
        finally:
            await mcp_tools.close()


    # Using MultiMCPTools, we can connect to multiple MCP servers at once, even if they use different transports.
    # In this example we connect to both our example server (Streamable HTTP transport), and a different server (stdio transport).
    async def run_agent_with_multimcp(message: str) -> None:
        # Initialize and connect to multiple MCP servers with different transports
        mcp_tools = MultiMCPTools(
            commands=["npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt"],
            urls=[server_url],
            urls_transports=["streamable-http"],
        )
        await mcp_tools.connect()

        try:
            agent = Agent(
                model=OpenAIChat(id="gpt-5-mini"),
                tools=[mcp_tools],
                markdown=True,
            )
            await agent.aprint_response(message=message, stream=True, markdown=True)
        finally:
            await mcp_tools.close()


    if __name__ == "__main__":
        asyncio.run(run_agent("Do I have any birthdays this week?"))
        asyncio.run(
            run_agent_with_multimcp(
                "Can you check when is my mom's birthday, and if there are any AirBnb listings in SF for two people for that day?"
            )
        )
    ```
  </Step>

  <Step title="Run the server">
    ```bash  theme={null}
    python streamable_http_server.py
    ```
  </Step>

  <Step title="Run the client">
    ```bash  theme={null}
    python streamable_http_client.py
    ```
  </Step>
</Steps>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt


# SSE Transport

Agno's MCP integration supports the [SSE transport](https://modelcontextprotocol.io/docs/basics/transports#server-sent-events-sse). This transport enables server-to-client streaming, and can prove more useful than [stdio](https://modelcontextprotocol.io/docs/basics/transports#standard-input%2Foutput-stdio) when working with restricted networks.

<Note>
  This transport is not recommended anymore by the MCP protocol. Use the [Streamable HTTP transport](/basics/tools/mcp/transports/streamable_http) instead.
</Note>

To use it, initialize the `MCPTools` passing the URL of the MCP server and setting the transport to `sse`:

```python  theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

server_url = "http://localhost:8000/sse"

# Initialize and connect to the SSE MCP server
mcp_tools = MCPTools(url=server_url, transport="sse")
await mcp_tools.connect()

try:
    agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
    await agent.aprint_response("What is the license for this project?", stream=True)
finally:
    # Always close the connection when done
    await mcp_tools.close()
```

You can also use the `server_params` argument to define the MCP connection. This way you can specify the headers to send to the MCP server with every request, and the timeout values:

```python  theme={null}
from agno.tools.mcp import MCPTools, SSEClientParams

server_params = SSEClientParams(
    url=...,
    headers=...,
    timeout=...,
    sse_read_timeout=...,
)

# Initialize and connect using server parameters
mcp_tools = MCPTools(server_params=server_params, transport="sse")
await mcp_tools.connect()

try:
    # Use mcp_tools with your agent
    pass
finally:
    await mcp_tools.close()
```

## Complete example

Let's set up a simple local server and connect to it using the SSE transport:

<Steps>
  <Step title="Setup the server">
    ```python sse_server.py theme={null}
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("calendar_assistant")


    @mcp.tool()
    def get_events(day: str) -> str:
        return f"There are no events scheduled for {day}."


    @mcp.tool()
    def get_birthdays_this_week() -> str:
        return "It is your mom's birthday tomorrow"


    if __name__ == "__main__":
        mcp.run(transport="sse")
    ```
  </Step>

  <Step title="Setup the client">
    ```python sse_client.py theme={null}
    import asyncio

    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from agno.tools.mcp import MCPTools, MultiMCPTools

    # This is the URL of the MCP server we want to use.
    server_url = "http://localhost:8000/sse"


    async def run_agent(message: str) -> None:
        # Initialize and connect to the SSE MCP server
        mcp_tools = MCPTools(transport="sse", url=server_url)
        await mcp_tools.connect()

        try:
            agent = Agent(
                model=OpenAIChat(id="gpt-5-mini"),
                tools=[mcp_tools],
                markdown=True,
            )
            await agent.aprint_response(message=message, stream=True, markdown=True)
        finally:
            await mcp_tools.close()


    # Using MultiMCPTools, we can connect to multiple MCP servers at once, even if they use different transports.
    # In this example we connect to both our example server (SSE transport), and a different server (stdio transport).
    async def run_agent_with_multimcp(message: str) -> None:
        # Initialize and connect to multiple MCP servers with different transports
        mcp_tools = MultiMCPTools(
            commands=["npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt"],
            urls=[server_url],
            urls_transports=["sse"],
        )
        await mcp_tools.connect()

        try:
            agent = Agent(
                model=OpenAIChat(id="gpt-5-mini"),
                tools=[mcp_tools],
                markdown=True,
            )
            await agent.aprint_response(message=message, stream=True, markdown=True)
        finally:
            await mcp_tools.close()


    if __name__ == "__main__":
        asyncio.run(run_agent("Do I have any birthdays this week?"))
        asyncio.run(
            run_agent_with_multimcp(
                "Can you check when is my mom's birthday, and if there are any AirBnb listings in SF for two people for that day?"
            )
        )
    ```
  </Step>

  <Step title="Run the server">
    ```bash  theme={null}
    python sse_server.py
    ```
  </Step>

  <Step title="Run the client">
    ```bash  theme={null}
    python sse_client.py
    ```
  </Step>
</Steps>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt

# Understanding Server Parameters

> Understanding how to configure the server parameters for the MCPTools and MultiMCPTools classes

The recommended way to configure `MCPTools` is to use the `command` or `url` parameters.

Alternatively, you can use the `server_params` parameter with `MCPTools` to configure the connection to the MCP server in more detail.

When using the **stdio** transport, the `server_params` parameter should be an instance of `StdioServerParameters`. It contains the following keys:

* `command`: The command to run the MCP server.
  * Use `npx` for mcp servers that can be installed via npm (or `node` if running on Windows).
  * Use `uvx` for mcp servers that can be installed via uvx.
  * Use custom binary executables (e.g., `./my-server`, `../usr/local/bin/my-server`, or binaries in your PATH).
* `args`: The arguments to pass to the MCP server.
* `env`: Optional environment variables to pass to the MCP server. Remember to include all current environment variables in the `env` dictionary. If `env` is not provided, the current environment variables will be used.
  e.g.

```python  theme={null}
{
    **os.environ,
    "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
}
```

When using the **SSE** transport, the `server_params` parameter should be an instance of `SSEClientParams`. It contains the following fields:

* `url`: The URL of the MCP server.
* `headers`: Headers to pass to the MCP server (optional).
* `timeout`: Timeout for the connection to the MCP server (optional).
* `sse_read_timeout`: Timeout for the SSE connection itself (optional).

When using the **Streamable HTTP** transport, the `server_params` parameter should be an instance of `StreamableHTTPClientParams`. It contains the following fields:

* `url`: The URL of the MCP server.
* `headers`: Headers to pass to the MCP server (optional).
* `timeout`: Timeout for the connection to the MCP server (optional).
* `sse_read_timeout`: how long (in seconds) the client will wait for a new event before disconnecting. All other HTTP operations are controlled by `timeout` (optional).
* `terminate_on_close`: Whether to terminate the connection when the client is closed (optional).


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt

# GitHub MCP agent

Using the [GitHub MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/github) to create an Agent that can explore, analyze and provide insights about GitHub repositories:

```python  theme={null}
"""🐙 MCP GitHub Agent - Your Personal GitHub Explorer!

This example shows how to create a GitHub agent that uses MCP to explore,
analyze, and provide insights about GitHub repositories. The agent leverages the Model
Context Protocol (MCP) to interact with GitHub, allowing it to answer questions
about issues, pull requests, repository details and more.

Example prompts to try:
- "List open issues in the repository"
- "Show me recent pull requests"
- "What are the repository statistics?"
- "Find issues labeled as bugs"
- "Show me contributor activity"

Run: `pip install agno mcp openai` to install the dependencies
Environment variables needed:
- Create a GitHub personal access token following these steps:
    - https://github.com/modelcontextprotocol/servers/tree/main/src/github#setup
- export GITHUB_TOKEN: Your GitHub personal access token
"""

import asyncio
import os
from textwrap import dedent

from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters


async def run_agent(message: str) -> None:
    """Run the GitHub agent with the given message."""

    # Initialize the MCP server
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
    )

    # Create a client session to connect to the MCP server
    async with MCPTools(server_params=server_params) as mcp_tools:
        agent = Agent(
            tools=[mcp_tools],
            instructions=dedent("""\
                You are a GitHub assistant. Help users explore repositories and their activity.

                - Use headings to organize your responses
                - Be concise and focus on relevant information\
            """),
            markdown=True,
                    )

        # Run the agent
        await agent.aprint_response(message, stream=True)


# Example usage
if __name__ == "__main__":
    # Pull request example
    asyncio.run(
        run_agent(
            "Tell me about Agno. Github repo: https://github.com/agno-agi/agno. You can read the README for more information."
        )
    )


# More example prompts to explore:
"""
Issue queries:
1. "Find issues needing attention"
2. "Show me issues by label"
3. "What issues are being actively discussed?"
4. "Find related issues"
5. "Analyze issue resolution patterns"

Pull request queries:
1. "What PRs need review?"
2. "Show me recent merged PRs"
3. "Find PRs with conflicts"
4. "What features are being developed?"
5. "Analyze PR review patterns"

Repository queries:
1. "Show repository health metrics"
2. "What are the contribution guidelines?"
3. "Find documentation gaps"
4. "Analyze code quality trends"
5. "Show repository activity patterns"
"""
```


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt


# Pipedream Google Calendar

> This example shows how to use the Google Calendar Pipedream MCP server with Agno Agents.

## Code

```python  theme={null}
"""
🗓️ Pipedream Google Calendar MCP

This example shows how to use Pipedream MCP servers (in this case the Google Calendar one) with Agno Agents.

1. Connect your Pipedream and Google Calendar accounts: https://mcp.pipedream.com/app/google-calendar
2. Get your Pipedream MCP server url: https://mcp.pipedream.com/app/google-calendar
3. Set the MCP_SERVER_URL environment variable to the MCP server url you got above
4. Install dependencies: pip install agno mcp-sdk
"""

import asyncio
import os

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from agno.utils.log import log_exception

mcp_server_url = os.getenv("MCP_SERVER_URL")


async def run_agent(task: str) -> None:
    try:
        async with MCPTools(
            url=mcp_server_url, transport="sse", timeout_seconds=20
        ) as mcp:
            agent = Agent(
                model=OpenAIChat(id="gpt-5-mini"),
                tools=[mcp],
                markdown=True,
            )
            await agent.aprint_response(
                message=task,
                stream=True,
            )
    except Exception as e:
        log_exception(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(
        run_agent("Tell me about all events I have in my calendar for tomorrow")
    )
```


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.agno.com/llms.txt