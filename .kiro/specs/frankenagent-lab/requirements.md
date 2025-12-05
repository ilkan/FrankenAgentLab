# Requirements Document

## Introduction

FrankenAgent Lab is a visual agent builder that enables developers to assemble AI agents using a Frankenstein-inspired metaphor. The MVP focuses on the backend foundation and a minimal UI preview that demonstrates the core concept: composing agents from modular "body parts" (head=LLM, arms=tools, legs=execution mode, heart=memory, spine=guardrails) that compile into functional Agno agents.

This MVP is developer-focused and excludes drag-and-drop canvas, authentication, multi-tenancy, and production deployment features.

## Glossary

- **Agent Blueprint**: A YAML or JSON configuration file that defines an agent's anatomy (head, arms, legs, heart, spine)
- **FrankenAgent Lab**: The system that enables visual agent composition using the Frankenstein metaphor
- **Agno**: The underlying agent framework used to execute compiled agents
- **Compiler**: The component that transforms an Agent Blueprint into a runnable Agno agent or team
- **Head**: The agent's LLM brain configuration (model, provider, system prompt, temperature)
- **Arms**: The tools and external integrations available to the agent
- **Legs**: The execution mode (single_agent, workflow, or team)
- **Heart**: Memory and knowledge base components
- **Spine**: Guardrails, safety constraints, and execution limits
- **Execution Trace**: A log of tool activations and agent actions during message processing
- **Runtime Service**: The CLI or HTTP service that executes agents from blueprints

## Requirements

### Requirement 1

**User Story:** As a developer, I want to define an Agent Blueprint using a structured config file, so that I can specify my agent's capabilities declaratively

#### Acceptance Criteria

1. THE FrankenAgent Lab SHALL support Agent Blueprint files in YAML format
2. THE FrankenAgent Lab SHALL support Agent Blueprint files in JSON format
3. THE Agent Blueprint schema SHALL include a head section with model, provider, system_prompt, and temperature fields
4. THE Agent Blueprint schema SHALL include an arms section containing a list of tool configurations
5. THE Agent Blueprint schema SHALL include a legs section specifying execution_mode as single_agent, workflow, or team
6. THE Agent Blueprint schema SHALL include a heart section for memory and knowledge configuration
7. THE Agent Blueprint schema SHALL include a spine section for guardrails including max_tool_calls limit

### Requirement 2

**User Story:** As a developer, I want the system to validate my Agent Blueprint, so that I can catch configuration errors before runtime

#### Acceptance Criteria

1. WHEN a developer loads an Agent Blueprint, THE FrankenAgent Lab SHALL validate the file format
2. WHEN a developer loads an Agent Blueprint, THE FrankenAgent Lab SHALL validate required fields are present
3. WHEN a developer loads an Agent Blueprint, THE FrankenAgent Lab SHALL validate field types match the schema
4. IF an Agent Blueprint contains invalid configuration, THEN THE FrankenAgent Lab SHALL return a descriptive error message
5. WHEN validation succeeds, THE FrankenAgent Lab SHALL return a validated blueprint object

### Requirement 3

**User Story:** As a developer, I want to compile an Agent Blueprint into a runnable Agno agent, so that I can execute the agent I designed

#### Acceptance Criteria

1. THE Compiler SHALL transform a validated Agent Blueprint into an Agno agent configuration
2. THE Compiler SHALL map the head section to Agno LLM model configuration
3. THE Compiler SHALL map the arms section to Agno tool registrations
4. THE Compiler SHALL map the legs section to Agno execution mode (single agent, workflow, or team)
5. THE Compiler SHALL map the heart section to Agno memory configuration
6. THE Compiler SHALL map the spine section to Agno guardrail constraints
7. WHEN compilation succeeds, THE Compiler SHALL return a runnable Agno agent instance

### Requirement 4

**User Story:** As a developer, I want to send messages to my compiled agent, so that I can interact with and test my agent's behavior

#### Acceptance Criteria

1. THE Runtime Service SHALL accept a blueprint identifier and a message string as input
2. WHEN a message is received, THE Runtime Service SHALL load and compile the specified blueprint
3. WHEN a message is received, THE Runtime Service SHALL execute the compiled agent with the message
4. THE Runtime Service SHALL return the agent's response text
5. THE Runtime Service SHALL capture and return an execution trace showing tool activations

### Requirement 5

**User Story:** As a developer, I want to inspect tool activation logs, so that I can understand which tools my agent used during execution

#### Acceptance Criteria

1. THE Runtime Service SHALL log each tool invocation with tool name and timestamp
2. THE Runtime Service SHALL log tool input parameters for each invocation
3. THE Runtime Service SHALL log tool output results for each invocation
4. THE Runtime Service SHALL include the execution trace in the response alongside the agent's message
5. THE Execution Trace SHALL display tool activations in chronological order

### Requirement 6

**User Story:** As a developer, I want to run agents via CLI, so that I can test agents quickly from my terminal

#### Acceptance Criteria

1. THE Runtime Service SHALL provide a CLI command accepting blueprint path and message arguments
2. WHEN the CLI command executes, THE Runtime Service SHALL load the blueprint from the specified path
3. WHEN the CLI command executes, THE Runtime Service SHALL compile and run the agent with the provided message
4. THE CLI SHALL output the agent response to stdout
5. THE CLI SHALL output the execution trace to stdout

### Requirement 7

**User Story:** As a developer, I want to run agents via HTTP API, so that I can integrate agent execution into web applications

#### Acceptance Criteria

1. THE Runtime Service SHALL provide an HTTP POST endpoint accepting blueprint_id and message in the request body
2. WHEN the HTTP endpoint receives a request, THE Runtime Service SHALL load the blueprint by ID
3. WHEN the HTTP endpoint receives a request, THE Runtime Service SHALL compile and execute the agent
4. THE HTTP endpoint SHALL return a JSON response containing the agent's message and execution trace
5. IF an error occurs, THEN THE HTTP endpoint SHALL return an appropriate HTTP status code and error message

### Requirement 8

**User Story:** As a developer, I want a minimal web UI to test agents, so that I can visually interact with my blueprints without writing API calls

#### Acceptance Criteria

1. THE FrankenAgent Lab SHALL provide a web page listing available Agent Blueprints
2. WHEN a developer selects a blueprint, THE web UI SHALL display the blueprint's name and description
3. THE web UI SHALL provide a text input field for entering messages
4. WHEN a developer submits a message, THE web UI SHALL send the message to the Runtime Service
5. THE web UI SHALL display the agent's response in a readable format
6. THE web UI SHALL display the execution trace showing which tools were activated

### Requirement 9

**User Story:** As a developer, I want example blueprints included, so that I can learn the schema and test the system immediately

#### Acceptance Criteria

1. THE FrankenAgent Lab SHALL include an example blueprint demonstrating single_agent execution mode
2. THE FrankenAgent Lab SHALL include an example blueprint demonstrating workflow execution mode
3. THE FrankenAgent Lab SHALL include an example blueprint demonstrating team execution mode
4. THE example blueprints SHALL include at least two different tool configurations
5. THE example blueprints SHALL be stored in a discoverable blueprints directory

### Requirement 10

**User Story:** As a developer, I want clear error messages when things fail, so that I can debug issues quickly

#### Acceptance Criteria

1. WHEN a blueprint file is not found, THE FrankenAgent Lab SHALL return an error message indicating the missing file path
2. WHEN blueprint validation fails, THE FrankenAgent Lab SHALL return an error message listing all validation failures
3. WHEN agent compilation fails, THE Compiler SHALL return an error message describing the compilation issue
4. WHEN agent execution fails, THE Runtime Service SHALL return an error message with the failure reason
5. THE FrankenAgent Lab SHALL log all errors with timestamps and context information

### Requirement 11

**User Story:** As a developer, I want the system to enforce guardrails, so that my agents operate within safe boundaries

#### Acceptance Criteria

1. WHEN a spine section specifies max_tool_calls, THE Runtime Service SHALL enforce this limit during execution
2. IF an agent exceeds max_tool_calls, THEN THE Runtime Service SHALL terminate execution and return an error
3. THE Runtime Service SHALL include guardrail violations in the execution trace
4. THE Runtime Service SHALL log guardrail enforcement events
5. WHEN no guardrails are specified, THE Runtime Service SHALL apply default safety limits

### Requirement 12

**User Story:** As a developer, I want documentation on creating blueprints, so that I can build agents without reading source code

#### Acceptance Criteria

1. THE FrankenAgent Lab SHALL include a README file with setup instructions
2. THE README SHALL document the Agent Blueprint schema with field descriptions
3. THE README SHALL provide examples of each execution mode
4. THE README SHALL document CLI usage with example commands
5. THE README SHALL document HTTP API endpoints with request and response examples
