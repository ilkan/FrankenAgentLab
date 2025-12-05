# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create Python project with Poetry
  - Initialize folder structure (frankenagent/, blueprints/, tests/)
  - Configure pyproject.toml with dependencies (agno, pydantic, fastapi, click, pyyaml)
  - Create .env.example with required API keys
  - Create .gitignore for Python project
  - _Requirements: 12.1_

- [x] 2. Implement Agent Blueprint schema and validation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3_

- [x] 2.1 Create Pydantic models for blueprint schema
  - Write HeadConfig model with model, provider, system_prompt, temperature, max_tokens fields
  - Write ArmConfig model with name, type, config fields
  - Write LegsConfig model with execution_mode, workflow_steps, team_members fields
  - Write HeartConfig model with memory and knowledge fields
  - Write SpineConfig model with max_tool_calls, timeout_seconds, allowed_domains fields
  - Write AgentBlueprint root model combining all sections
  - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] 2.2 Implement blueprint loader with YAML and JSON support
  - Write BlueprintLoader.load_from_file() to read YAML/JSON files
  - Write BlueprintLoader.load_from_dict() to validate dictionaries
  - Add file format detection based on extension
  - Implement Pydantic validation with descriptive error messages
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 2.3 Write unit tests for schema validation
  - Test valid blueprint loading
  - Test invalid blueprint rejection with error messages
  - Test YAML and JSON format support
  - Test missing required fields
  - Test invalid field types
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [-] 3. Build tool registry and tool mapping
  - _Requirements: 3.2, 3.3_

- [x] 3.1 Create ToolRegistry class
  - Define TOOL_MAP dictionary mapping tool types to Agno tool classes
  - Implement get_tool() method to instantiate tools from type and config
  - Add support for tavily_search, python_eval, file_tools, duckduckgo_search
  - Handle tool configuration parameters (API keys, options)
  - Add error handling for unknown tool types
  - _Requirements: 3.3_

- [ ]* 3.2 Write unit tests for tool registry
  - Test tool instantiation for each supported type
  - Test error handling for unknown tool types
  - Test tool configuration passing
  - _Requirements: 3.3_

- [x] 4. Implement blueprint compiler
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4.1 Create BlueprintCompiler class with single agent support
  - Write compile() method that routes to appropriate builder based on execution_mode
  - Implement _build_single_agent() to create Agno Agent from blueprint
  - Map head config to Agent model and instructions parameters
  - Map arms config to Agent tools parameter using ToolRegistry
  - Map heart config to Agent memory parameter
  - Return configured Agent instance
  - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.7_

- [x] 4.2 Add workflow execution mode support
  - Implement _build_workflow() to create Agno Workflow from blueprint
  - Parse workflow_steps from legs config
  - Create workflow with steps and tools
  - Handle workflow-specific configuration
  - _Requirements: 3.1, 3.4, 3.7_

- [x] 4.3 Add team execution mode support
  - Implement _build_team() to create Agno Team from blueprint
  - Parse team_members from legs config
  - Create individual agents for each team member
  - Assign tools to specific team members
  - Configure team coordination
  - _Requirements: 3.1, 3.4, 3.7_

- [x] 4.4 Implement guardrails wrapper
  - Create GuardrailWrapper class to enforce spine constraints
  - Implement max_tool_calls enforcement
  - Implement timeout_seconds enforcement
  - Add guardrail violation logging
  - Wrap compiled agents with guardrails
  - _Requirements: 3.6, 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 4.5 Write unit tests for compiler
  - Test single_agent compilation
  - Test workflow compilation
  - Test team compilation
  - Test guardrail application
  - Test error handling for invalid configs
  - _Requirements: 3.1, 3.7, 10.3_

- [x] 5. Create execution tracing system
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5.1 Implement ToolTrace and ExecutionResult data classes
  - Create ToolTrace dataclass with tool_name, timestamp, inputs, outputs, duration_ms
  - Create ExecutionResult dataclass with response, execution_trace, total_duration_ms, error
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 5.2 Build tracing wrapper for agents
  - Create TracingWrapper class to intercept tool calls
  - Capture tool invocations with timestamps
  - Record tool inputs and outputs
  - Calculate execution duration for each tool call
  - Store traces in chronological order
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 5.3 Write unit tests for tracing
  - Test tool call capture
  - Test timestamp recording
  - Test input/output logging
  - Test trace ordering
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Implement RuntimeService
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 10.4_

- [x] 6.1 Create RuntimeService class
  - Initialize with blueprints_dir parameter
  - Create BlueprintCompiler and BlueprintLoader instances
  - Implement execute() method accepting blueprint_id and message
  - Load blueprint from file using loader
  - Compile blueprint to agent using compiler
  - Wrap agent with tracing
  - Execute agent with message and capture response
  - Return ExecutionResult with response and trace
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6.2 Add error handling and logging
  - Handle blueprint not found errors with descriptive messages
  - Handle validation errors with field details
  - Handle compilation errors with context
  - Handle execution errors with agent error details
  - Log all errors with timestamps
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 6.3 Write integration tests for RuntimeService
  - Test end-to-end execution with mock blueprint
  - Test error handling for missing blueprints
  - Test error handling for invalid blueprints
  - Test trace capture accuracy
  - _Requirements: 4.1, 4.5, 10.1, 10.4_

- [x] 7. Build CLI interface
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 12.4_

- [x] 7.1 Create CLI with Click
  - Set up Click CLI group
  - Implement run command accepting blueprint_path and message arguments
  - Load blueprint from specified path
  - Execute agent using RuntimeService
  - Format and print response to stdout
  - Format and print execution trace to stdout
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 7.2 Add list command
  - Implement list_blueprints command
  - Scan blueprints directory for YAML/JSON files
  - Display blueprint names and descriptions
  - _Requirements: 8.1_

- [x] 7.3 Add CLI error handling
  - Handle file not found errors
  - Handle validation errors
  - Handle execution errors
  - Display user-friendly error messages
  - _Requirements: 10.1, 10.2, 10.4_

- [ ]* 7.4 Write CLI integration tests
  - Test run command execution
  - Test list command output
  - Test error handling
  - _Requirements: 6.1, 6.5_

- [x] 8. Implement HTTP API with FastAPI
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8.1 Create FastAPI application
  - Initialize FastAPI app with title and description
  - Create RuntimeService instance
  - Define ExecuteRequest and ExecuteResponse Pydantic models
  - _Requirements: 7.1_

- [x] 8.2 Implement /execute endpoint
  - Create POST /execute endpoint accepting ExecuteRequest
  - Extract blueprint_id and message from request
  - Execute agent using RuntimeService
  - Convert ExecutionResult to ExecuteResponse
  - Return JSON response with response text and execution trace
  - Handle errors with appropriate HTTP status codes
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8.3 Implement /blueprints endpoints
  - Create GET /blueprints endpoint to list available blueprints
  - Create GET /blueprints/{blueprint_id} endpoint to get blueprint details
  - Return blueprint metadata (name, description, version)
  - _Requirements: 8.1_

- [x] 8.4 Add static file serving for web UI
  - Configure FastAPI to serve static files from ui/static directory
  - Mount static files at /static path
  - _Requirements: 8.1_

- [ ]* 8.5 Write API integration tests
  - Test /execute endpoint with valid request
  - Test /execute endpoint error handling
  - Test /blueprints listing
  - Test /blueprints/{id} details
  - _Requirements: 7.1, 7.4, 7.5_

- [x] 9. Create minimal web UI
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 9.1 Build single-page HTML interface
  - Create index.html with basic structure and styling
  - Add blueprints list section
  - Add chat interface section with message input
  - Add response display area
  - Add execution trace display area
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 9.2 Implement JavaScript for API interaction
  - Write loadBlueprints() function to fetch and display blueprints
  - Write selectBlueprint() function to handle blueprint selection
  - Write sendMessage() function to POST to /execute endpoint
  - Write displayResponse() function to render agent response and trace
  - Format execution trace with tool names, timestamps, and results
  - Add error handling and display
  - _Requirements: 8.2, 8.4, 8.5, 8.6_

- [x] 10. Create example blueprints
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 10.1 Create simple_assistant.yaml
  - Write blueprint with single_agent execution mode
  - Configure GPT-4o-mini model
  - Add tavily_search tool
  - Add basic memory configuration
  - Add simple guardrails
  - _Requirements: 9.1, 9.4_

- [x] 10.2 Create research_workflow.yaml
  - Write blueprint with workflow execution mode
  - Configure workflow steps (search, analyze, summarize)
  - Add web_search and file_tools
  - Configure workflow-specific settings
  - _Requirements: 9.2, 9.4_

- [x] 10.3 Create team_analyzer.yaml
  - Write blueprint with team execution mode
  - Configure team members (researcher, analyst)
  - Assign tools to specific team members
  - Configure shared memory
  - _Requirements: 9.3, 9.4_

- [x] 10.4 Verify all examples work end-to-end
  - Test each blueprint via CLI
  - Test each blueprint via API
  - Test each blueprint via web UI
  - Verify execution traces are captured correctly
  - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [ ] 11. Write documentation
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 11.1 Create comprehensive README
  - Write project overview with Frankenstein metaphor explanation
  - Document installation instructions with Poetry
  - Document Agent Blueprint schema with field descriptions
  - Provide CLI usage examples
  - Provide API usage examples with curl commands
  - Document environment variables and configuration
  - Add troubleshooting section
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 11.2 Add inline code documentation
  - Add docstrings to all classes and methods
  - Document function parameters and return types
  - Add usage examples in docstrings
  - _Requirements: 12.2_

- [ ]* 11.3 Create API documentation
  - Generate OpenAPI/Swagger docs from FastAPI
  - Document request/response schemas
  - Add endpoint usage examples
  - _Requirements: 12.5_

- [ ] 12. Final integration and polish
  - _Requirements: All_

- [ ] 12.1 End-to-end testing
  - Test complete flow: blueprint → compile → execute → trace
  - Test all three execution modes (single_agent, workflow, team)
  - Test CLI, API, and web UI interfaces
  - Verify error handling across all components
  - _Requirements: 3.7, 4.5, 7.5, 10.4_

- [ ] 12.2 Add logging throughout application
  - Configure Python logging with appropriate levels
  - Add debug logs for compilation steps
  - Add info logs for execution events
  - Add error logs with full context
  - _Requirements: 10.5_

- [ ] 12.3 Create startup script
  - Write script to check dependencies
  - Verify API keys are configured
  - Start FastAPI server
  - Open web UI in browser
  - _Requirements: 12.1_

- [ ]* 12.4 Performance verification
  - Verify agent execution completes within timeout
  - Verify trace capture doesn't significantly slow execution
  - Check memory usage with multiple executions
  - _Requirements: 11.1, 11.4_
