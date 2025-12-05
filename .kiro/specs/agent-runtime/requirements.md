# Requirements Document

## Introduction

This document specifies the requirements for the FrankenAgent Lab core agent runtime system. The runtime is responsible for taking agent blueprints (configurations created in the visual frontend) and executing them as functional AI agents using the Agno framework. The system validates blueprints, compiles them into Agno agents with tools (starting with Tavily Search), manages execution with guardrails, and provides logging for observability.

## Glossary

- **Agent_Runtime**: The backend system that validates, compiles, and executes agent blueprints
- **Blueprint**: A JSON/YAML configuration defining an agent's head (LLM), arms (tools), legs (execution mode), heart (memory), and spine (guardrails)
- **Agno_Agent**: An instance of an agent created using the Agno framework
- **Tavily_Tool**: A web search tool integration that allows agents to search the internet
- **Guardrail**: A safety constraint that limits agent behavior (max tool calls, timeout, allowed domains)
- **Compilation**: The process of transforming a blueprint into a runnable Agno_Agent
- **Session**: A single execution context for an agent handling one or more messages
- **Tool_Call**: An invocation of an external tool by the Agno_Agent during execution
- **Component_Configuration**: The structured settings for each agent body part (head, arms, legs, heart, spine)
- **Instruction_Improvement**: An LLM-assisted feature that helps users refine system prompts and instructions
- **Configuration_Schema**: The validation rules and available options for each component type

## Requirements

### Requirement 1: Blueprint Validation

**User Story:** As a developer, I want the runtime to validate agent blueprints before execution, so that I receive clear error messages for invalid configurations rather than runtime failures.

#### Acceptance Criteria

1. WHEN a blueprint is submitted to the validation endpoint, THE Agent_Runtime SHALL verify that all required fields (head, legs) are present
2. WHEN a blueprint contains an unsupported provider or model, THE Agent_Runtime SHALL return a validation error with the list of supported providers
3. WHEN a blueprint contains an unsupported tool type, THE Agent_Runtime SHALL return a validation error with the list of supported tool types
4. WHEN a blueprint contains invalid guardrail values, THE Agent_Runtime SHALL return a validation error specifying the valid ranges
5. WHEN a blueprint passes all validation checks, THE Agent_Runtime SHALL return a success response with a normalized blueprint and unique identifier

### Requirement 2: Blueprint Compilation

**User Story:** As a developer, I want blueprints to be compiled into Agno agents with the correct LLM configuration and tools, so that the agent behaves according to the blueprint specification.

#### Acceptance Criteria

1. WHEN a validated blueprint is compiled, THE Agent_Runtime SHALL create an Agno_Agent with the LLM provider and model specified in the head section
2. WHEN a blueprint includes system_prompt in the head section, THE Agent_Runtime SHALL configure the Agno_Agent with those instructions
3. WHEN a blueprint includes temperature or max_tokens in the head section, THE Agent_Runtime SHALL apply those parameters to the Agno_Agent
4. WHEN a blueprint includes a tavily_search tool in the arms section, THE Agent_Runtime SHALL attach the Tavily_Tool to the Agno_Agent with appropriate configuration
5. WHEN a blueprint specifies single_agent execution mode, THE Agent_Runtime SHALL create a single Agno_Agent instance

### Requirement 3: Tool Integration

**User Story:** As a developer, I want agents to use Tavily Search when needed, so that agents can retrieve real-time information from the web to answer user queries.

#### Acceptance Criteria

1. WHEN an Agno_Agent is compiled with tavily_search in the arms section, THE Agent_Runtime SHALL register the Tavily_Tool with a clear description for the LLM
2. WHEN the Agno_Agent determines a web search is needed, THE Agno_Agent SHALL invoke the Tavily_Tool with appropriate search parameters
3. WHEN the Tavily_Tool is invoked, THE Agent_Runtime SHALL use the TAVILY_API_KEY from environment variables
4. WHEN a Tavily_Tool call completes, THE Agent_Runtime SHALL log the tool name, arguments, duration, and success status
5. WHERE allowed_domains are specified in the spine section, THE Agent_Runtime SHALL enforce domain restrictions on web-based tools

### Requirement 4: Agent Execution

**User Story:** As a developer, I want to send messages to compiled agents and receive responses, so that I can integrate the runtime with the frontend chat interface.

#### Acceptance Criteria

1. WHEN a run request is received with a blueprint and message, THE Agent_Runtime SHALL compile or retrieve the corresponding Agno_Agent
2. WHEN an Agno_Agent processes a message, THE Agent_Runtime SHALL pass the message to the agent and await the response
3. WHEN an Agno_Agent completes processing, THE Agent_Runtime SHALL return the final response to the caller
4. WHEN an Agno_Agent invokes tools during execution, THE Agent_Runtime SHALL allow the agent to use tool results in its reasoning
5. WHEN a run request includes a session identifier, THE Agent_Runtime SHALL maintain conversation context across multiple messages

### Requirement 5: Guardrail Enforcement

**User Story:** As a developer, I want guardrails to prevent runaway agent execution, so that agents cannot exceed resource limits or make excessive tool calls.

#### Acceptance Criteria

1. WHEN a blueprint specifies max_tool_calls in the spine section, THE Agent_Runtime SHALL terminate execution if the limit is exceeded
2. WHEN a blueprint specifies timeout_seconds in the spine section, THE Agent_Runtime SHALL terminate execution if the timeout is reached
3. WHEN a guardrail is violated during execution, THE Agent_Runtime SHALL return an error response indicating which guardrail was triggered
4. WHEN a guardrail is violated, THE Agent_Runtime SHALL log the violation with timestamp and context
5. WHEN execution completes within guardrail limits, THE Agent_Runtime SHALL return the successful response

### Requirement 6: Memory Management

**User Story:** As a developer, I want agents to maintain conversation history when memory is enabled, so that agents can reference previous messages in multi-turn conversations.

#### Acceptance Criteria

1. WHEN a blueprint enables memory in the heart section, THE Agent_Runtime SHALL attach conversation memory to the Agno_Agent
2. WHEN an Agno_Agent with memory processes a message, THE Agent_Runtime SHALL include previous messages in the context
3. WHEN a session identifier is provided, THE Agent_Runtime SHALL retrieve and restore the conversation history for that session
4. WHEN a new session is started, THE Agent_Runtime SHALL initialize empty conversation history
5. WHEN a message is processed, THE Agent_Runtime SHALL store the message and response in the session history

### Requirement 7: Execution Logging

**User Story:** As a developer, I want detailed logs of agent execution, so that I can debug issues and display execution traces in the frontend.

#### Acceptance Criteria

1. WHEN an agent execution begins, THE Agent_Runtime SHALL create a log entry with timestamp and blueprint identifier
2. WHEN a Tool_Call is made during execution, THE Agent_Runtime SHALL log the tool name, input arguments, and execution duration
3. WHEN a Tool_Call completes, THE Agent_Runtime SHALL log the success status and output summary
4. WHEN execution completes, THE Agent_Runtime SHALL log the total latency and final response status
5. WHEN logs are requested for a session, THE Agent_Runtime SHALL return all log entries for that session in chronological order

### Requirement 8: Error Handling

**User Story:** As a developer, I want clear error messages when execution fails, so that I can identify and fix issues quickly.

#### Acceptance Criteria

1. WHEN blueprint validation fails, THE Agent_Runtime SHALL return an error response with specific field-level validation messages
2. WHEN an LLM provider returns an error, THE Agent_Runtime SHALL return an error response with the provider error details
3. WHEN a Tool_Call fails, THE Agent_Runtime SHALL log the error and allow the agent to continue or return an error response
4. WHEN a guardrail is violated, THE Agent_Runtime SHALL return an error response indicating which limit was exceeded
5. WHEN an unexpected error occurs, THE Agent_Runtime SHALL return a generic error response and log the full error details

### Requirement 9: API Endpoints

**User Story:** As a frontend developer, I want REST API endpoints to validate, compile, and run agents, so that I can integrate the runtime with the visual builder interface.

#### Acceptance Criteria

1. THE Agent_Runtime SHALL expose a POST endpoint at /api/blueprints/validate-and-compile that accepts blueprint JSON
2. THE Agent_Runtime SHALL expose a POST endpoint at /api/agents/run that accepts blueprint and message parameters
3. THE Agent_Runtime SHALL expose a GET endpoint at /api/agents/logs that accepts session_id query parameter
4. WHEN an API request is malformed, THE Agent_Runtime SHALL return a 400 status code with error details
5. WHEN an API request succeeds, THE Agent_Runtime SHALL return a 200 status code with the response payload

### Requirement 10: Blueprint File Persistence

**User Story:** As a developer, I want to save agent configurations as YAML/JSON files, so that each deployed agent has a persistent configuration file that can be run directly with Agno or loaded by the runtime.

#### Acceptance Criteria

1. WHEN a user saves an agent configuration, THE Agent_Runtime SHALL write the blueprint to a YAML file in the blueprints directory
2. WHEN saving a blueprint file, THE Agent_Runtime SHALL assign a unique filename based on the agent name and timestamp
3. WHEN a blueprint file is saved, THE Agent_Runtime SHALL ensure the file is valid YAML/JSON that can be loaded by the runtime
4. WHEN listing available agents, THE Agent_Runtime SHALL scan the blueprints directory and return all saved blueprint files
5. WHEN a blueprint file is loaded, THE Agent_Runtime SHALL validate and compile it into a runnable Agno_Agent

### Requirement 10b: Blueprint Caching

**User Story:** As a developer, I want the option to cache compiled blueprints in memory, so that I can avoid recompiling the same blueprint on every request.

#### Acceptance Criteria

1. THE Agent_Runtime SHALL support ephemeral blueprints that are compiled on each request
2. WHERE blueprint caching is enabled, THE Agent_Runtime SHALL store compiled agents with a unique identifier
3. WHERE a blueprint_id is provided in a run request, THE Agent_Runtime SHALL retrieve the cached compiled agent
4. WHEN a cached blueprint is requested that does not exist, THE Agent_Runtime SHALL return an error response
5. WHERE blueprint persistence is implemented, THE Agent_Runtime SHALL provide an endpoint to save blueprints with assigned identifiers

### Requirement 11: Component Configuration Schema

**User Story:** As a frontend developer, I want to retrieve configuration schemas for each component type, so that I can build dynamic configuration forms with proper validation and available options.

#### Acceptance Criteria

1. THE Agent_Runtime SHALL expose a GET endpoint at /api/components/schemas that returns configuration schemas for all component types
2. WHEN a schema is requested for the head component, THE Agent_Runtime SHALL return available providers, models per provider, and parameter ranges
3. WHEN a schema is requested for the arms component, THE Agent_Runtime SHALL return available tool types and their configuration options
4. WHEN a schema is requested for the legs component, THE Agent_Runtime SHALL return available execution modes and their requirements
5. WHEN a schema is requested for the heart component, THE Agent_Runtime SHALL return memory configuration options and knowledge base settings
6. WHEN a schema is requested for the spine component, THE Agent_Runtime SHALL return guardrail parameter ranges and validation rules

### Requirement 12: Head Configuration Management

**User Story:** As a user, I want to configure the agent's head (LLM brain) with a text editor for instructions, so that I can define how the agent should behave and respond.

#### Acceptance Criteria

1. WHEN a user edits the system_prompt field in the head configuration, THE Agent_Runtime SHALL accept multi-line text input
2. WHEN a head configuration is saved, THE Agent_Runtime SHALL validate that the system_prompt does not exceed 10000 characters
3. WHEN a head configuration includes temperature, THE Agent_Runtime SHALL validate the value is between 0.0 and 2.0
4. WHEN a head configuration includes max_tokens, THE Agent_Runtime SHALL validate the value is a positive integer within model limits
5. WHEN a head configuration is compiled, THE Agent_Runtime SHALL pass all parameters to the Agno model constructor

### Requirement 13: Instruction Improvement via LLM

**User Story:** As a user, I want to improve my agent instructions by asking an LLM for suggestions, so that I can create more effective system prompts without being an expert prompt engineer.

#### Acceptance Criteria

1. THE Agent_Runtime SHALL expose a POST endpoint at /api/instructions/improve that accepts current instructions and improvement goals
2. WHEN an instruction improvement request is received, THE Agent_Runtime SHALL use an Agno_Agent to generate improved instructions
3. WHEN generating improved instructions, THE Agent_Runtime SHALL preserve the user's intent while enhancing clarity and effectiveness
4. WHEN the improvement is complete, THE Agent_Runtime SHALL return the improved instructions with an explanation of changes made
5. WHEN the improvement request fails, THE Agent_Runtime SHALL return the original instructions with an error message

### Requirement 14: Arms Configuration Management

**User Story:** As a user, I want to configure multiple tools (arms) for my agent, so that the agent can interact with external services and APIs.

#### Acceptance Criteria

1. WHEN a user adds a tool to the arms configuration, THE Agent_Runtime SHALL validate the tool type is supported
2. WHEN a tavily_search tool is configured, THE Agent_Runtime SHALL accept max_results and search_depth parameters
3. WHEN multiple tools are configured, THE Agent_Runtime SHALL preserve the order of tool definitions
4. WHEN a tool configuration includes custom parameters, THE Agent_Runtime SHALL validate parameters against the tool schema
5. WHEN arms are compiled, THE Agent_Runtime SHALL create all tool instances and attach them to the Agno_Agent

### Requirement 15: Legs Configuration Management

**User Story:** As a user, I want to configure the execution mode (legs) of my agent, so that I can choose between single agent, workflow, or team execution patterns.

#### Acceptance Criteria

1. WHEN a user selects single_agent execution mode, THE Agent_Runtime SHALL compile a single Agno_Agent instance
2. WHEN a user selects workflow execution mode, THE Agent_Runtime SHALL validate that workflow steps are defined
3. WHEN a user selects team execution mode, THE Agent_Runtime SHALL validate that team members are defined
4. WHEN the execution mode is changed, THE Agent_Runtime SHALL validate that all required configuration for that mode is present
5. WHEN legs are compiled, THE Agent_Runtime SHALL create the appropriate Agno execution structure

### Requirement 16: Heart Configuration Management

**User Story:** As a user, I want to configure memory and knowledge settings (heart) for my agent, so that the agent can remember conversations and access knowledge bases.

#### Acceptance Criteria

1. WHEN a user enables memory in the heart configuration, THE Agent_Runtime SHALL configure the Agno_Agent with conversation history
2. WHEN memory is enabled, THE Agent_Runtime SHALL accept a history_length parameter between 1 and 100
3. WHEN a user enables knowledge in the heart configuration, THE Agent_Runtime SHALL validate that a knowledge base is configured
4. WHEN heart configuration is compiled, THE Agent_Runtime SHALL attach the appropriate Agno database and memory settings
5. WHEN memory is disabled, THE Agent_Runtime SHALL create a stateless Agno_Agent without conversation history

### Requirement 17: Spine Configuration Management

**User Story:** As a user, I want to configure guardrails (spine) for my agent, so that I can prevent runaway execution and enforce safety constraints.

#### Acceptance Criteria

1. WHEN a user sets max_tool_calls in the spine configuration, THE Agent_Runtime SHALL validate the value is between 1 and 100
2. WHEN a user sets timeout_seconds in the spine configuration, THE Agent_Runtime SHALL validate the value is between 1 and 300
3. WHEN a user specifies allowed_domains in the spine configuration, THE Agent_Runtime SHALL validate each domain is a valid domain format
4. WHEN spine configuration is compiled, THE Agent_Runtime SHALL wrap the Agno_Agent with guardrail enforcement
5. WHEN guardrails are not specified, THE Agent_Runtime SHALL apply default values for safety
