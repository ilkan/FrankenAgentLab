# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Check the project structure. Add Agno framework and related dependencies to pyproject.toml
  - Create directory structure for runtime, compiler, tools, and api modules
  - Configure environment variables for API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, TAVILY_API_KEY)
  - _Requirements: 1.1, 2.1, 3.3_

- [x] 2. Implement data models and validation schemas
  - Create Pydantic models for AgentBlueprint (HeadConfig, ArmConfig, LegsConfig, HeartConfig, SpineConfig)
  - Create Pydantic models for API requests (ValidateRequest, RunRequest) and responses (ValidateResponse, RunResponse, ExecutionResult)
  - Create Pydantic models for logging (ToolCallLog, LogEntry)
  - _Requirements: 1.1, 1.2, 9.1, 9.2_

- [x] 3. Implement blueprint validator
  - Create BlueprintValidator class in frankenagent/compiler/validator.py
  - Implement validation for required fields (head, legs)
  - Implement validation for supported providers (openai, anthropic) and models
  - Implement validation for supported tool types (tavily_search)
  - Implement validation for guardrail values (max_tool_calls, timeout_seconds)
  - Implement blueprint normalization and ID generation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 4. Implement tool registry
  - Create ToolRegistry class in frankenagent/tools/registry.py
  - Implement create_tool method that maps arm configs to Agno tools
  - Implement _create_tavily_tool method using TavilyTools from Agno
  - Add API key validation from environment variables
  - Add stub for future HTTP tool support
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 5. Implement agent compiler
  - Create AgentCompiler class in frankenagent/compiler/compiler.py
  - Implement compile method that transforms blueprint to Agno Agent
  - Implement _build_model method for OpenAI and Anthropic providers
  - Implement _build_tools method using ToolRegistry
  - Implement _build_memory method for conversation history (SQLite for MVP)
  - Create CompiledAgent wrapper class with agent and guardrails
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2_

- [x] 6. Implement session manager
  - Create SessionManager class in frankenagent/runtime/session_manager.py
  - Implement create_new_session method with UUID generation
  - Implement get_or_create method for session retrieval
  - Implement log_tool_call method for recording tool invocations
  - Implement get_logs method for retrieving session logs
  - Use in-memory storage for MVP (dict-based)
  - _Requirements: 4.5, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7. Implement execution orchestrator with guardrails
  - Create ExecutionOrchestrator class in frankenagent/runtime/executor.py
  - Implement execute method that orchestrates agent execution
  - Implement _execute_with_guardrails method with timeout enforcement
  - Implement _run_agent_with_tool_limit method to track and limit tool calls
  - Implement tool call logging and timing
  - Create GuardrailViolation exception class
  - Handle execution errors and return ExecutionResult
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 7.2, 7.3, 7.4_

- [x] 8. Implement FastAPI endpoints
  - Create FastAPI app in frankenagent/api/server.py
  - Implement POST /api/blueprints/validate-and-compile endpoint
  - Implement POST /api/agents/run endpoint
  - Implement GET /api/agents/logs endpoint
  - Add request validation and error handling
  - Add CORS middleware for frontend integration
  - Return appropriate HTTP status codes (200, 400, 404, 500)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 9. Implement error handling and logging
  - Create custom exception classes (FrankenAgentError, ValidationError, CompilationError, ExecutionError, GuardrailViolation)
  - Add error response formatting in API layer
  - Configure Python logging with appropriate levels
  - Add structured logging for execution events
  - Add error logging for LLM provider errors and tool failures
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 10. Wire frontend to backend endpoints
  - Update frontend to call /api/blueprints/validate-and-compile when user clicks "Validate"
  - Update frontend to call /api/agents/run when user sends a message
  - Update frontend to call /api/agents/logs to populate logs panel
  - Handle API errors and display error messages in UI
  - Display tool calls and execution metadata in logs panel
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 11. Create example blueprints for testing
  - Create simple_assistant.yaml with basic OpenAI agent
  - Create search_agent.yaml with Tavily search tool
  - Create guardrails_test.yaml with strict limits for testing
  - Create memory_agent.yaml with conversation history enabled
  - _Requirements: 1.5, 2.5, 3.1, 6.1_

- [ ] 12. Add integration tests
- [x] 12.1 Write test for blueprint validation (valid and invalid cases)
  - Test valid blueprint passes validation
  - Test missing required fields returns errors
  - Test unsupported provider returns error
  - Test unsupported tool type returns error
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 12.2 Write test for agent compilation
  - Test blueprint compiles to Agno Agent
  - Test LLM model is configured correctly
  - Test tools are attached correctly
  - Test memory is configured when enabled
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 12.3 Write test for agent execution with Tavily
  - Test agent can execute simple query without tools
  - Test agent invokes Tavily when search is needed
  - Test tool call is logged correctly
  - Test response includes tool call metadata
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4_

- [x] 12.4 Write test for guardrail enforcement
  - Test max_tool_calls limit is enforced
  - Test timeout_seconds limit is enforced
  - Test guardrail violations return appropriate errors
  - Test guardrail violations are logged
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 12.5 Write test for conversation memory
  - Test session is created and persisted
  - Test conversation history is maintained across messages
  - Test history is included in agent context
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 12.6 Write end-to-end API tests
  - Test /validate-and-compile endpoint with valid blueprint
  - Test /validate-and-compile endpoint with invalid blueprint
  - Test /agents/run endpoint with simple query
  - Test /agents/run endpoint with search query
  - Test /agents/logs endpoint returns correct logs
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 13. Implement component configuration schema service
- [x] 13.1 Create ComponentSchemaProvider class in frankenagent/config/schemas.py
  - Implement get_all_schemas method that returns schemas for all components
  - Implement get_head_schema with providers, models, and parameter validation rules
  - Implement get_arms_schema with tool types and tool-specific configurations
  - Implement get_legs_schema with execution modes and requirements
  - Implement get_heart_schema with memory and knowledge configuration
  - Implement get_spine_schema with guardrail parameter ranges
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ]* 13.2 Write property test for component schema completeness
  - **Property 1: Component Schema Completeness**
  - **Validates: Requirements 11.2, 11.3, 11.4, 11.5, 11.6**

- [x] 14. Implement instruction improvement service
- [x] 14.1 Create InstructionImprover class in frankenagent/config/instruction_improver.py
  - Create specialized Agno Agent for instruction improvement
  - Implement improve method that takes current instructions, goal, and context
  - Implement _build_improvement_prompt to construct effective prompts
  - Implement _parse_improvement_response to extract improved instructions and explanation
  - Add error handling to return original instructions on failure
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ]* 14.2 Write property test for instruction improvement preservation
  - **Property 3: Instruction Improvement Preservation**
  - **Validates: Requirements 13.3**

- [ ]* 14.3 Write property test for instruction improvement fallback
  - **Property 10: Instruction Improvement Fallback**
  - **Validates: Requirements 13.5**

- [x] 15. Add new API endpoints for component configuration
- [x] 15.1 Add GET /api/components/schemas endpoint
  - Create endpoint that returns ComponentSchemaProvider.get_all_schemas()
  - Add response model ComponentSchemasResponse
  - Add error handling for schema generation failures
  - _Requirements: 11.1_

- [x] 15.2 Add POST /api/instructions/improve endpoint
  - Create endpoint that accepts ImproveInstructionsRequest
  - Call InstructionImprover.improve with request data
  - Return ImproveInstructionsResponse with improved instructions
  - Add error handling and fallback to original instructions
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 16. Enhance blueprint validation for component configurations
- [x] 16.1 Update HeadConfig validation
  - Add validator for system_prompt max length (10000 characters)
  - Add validator for temperature range (0.0 to 2.0)
  - Add validator for max_tokens positive integer
  - _Requirements: 12.2, 12.3, 12.4_

- [ ]* 16.2 Write property test for head configuration validation
  - **Property 2: Head Configuration Validation**
  - **Validates: Requirements 12.2, 12.3, 12.4**

- [x] 16.3 Update ArmConfig validation
  - Add validator for tool-specific config parameters
  - Validate tavily_search max_results (1-10) and search_depth (basic/advanced)
  - Preserve tool order in configuration
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ]* 16.4 Write property test for arms configuration ordering
  - **Property 4: Arms Configuration Ordering**
  - **Validates: Requirements 14.3**

- [x] 16.4 Update LegsConfig validation
  - Add validator for workflow_steps when execution_mode is "workflow"
  - Add validator for team_members when execution_mode is "team"
  - Ensure required fields are present for each mode
  - _Requirements: 15.1, 15.2, 15.3, 15.4_

- [ ]* 16.5 Write property test for legs mode requirements
  - **Property 5: Legs Mode Requirements**
  - **Validates: Requirements 15.2, 15.3, 15.4**

- [x] 16.6 Update HeartConfig validation
  - Add validator for history_length range (1-100)
  - Ensure memory configuration is applied correctly
  - _Requirements: 16.1, 16.2_

- [ ]* 16.7 Write property test for heart memory configuration
  - **Property 6: Heart Memory Configuration**
  - **Validates: Requirements 16.2, 16.4**

- [x] 16.8 Update SpineConfig validation
  - Add validator for max_tool_calls range (1-100)
  - Add validator for timeout_seconds range (1-300)
  - Add validator for allowed_domains format
  - _Requirements: 17.1, 17.2, 17.3_

- [ ]* 16.9 Write property test for spine guardrail bounds
  - **Property 7: Spine Guardrail Bounds**
  - **Validates: Requirements 17.1, 17.2, 17.3**

- [x] 17. Update compiler to handle enhanced component configurations
- [x] 17.1 Update AgentCompiler._build_model to use enhanced HeadConfig
  - Pass all head parameters to Agno model constructor
  - Validate system_prompt is applied correctly
  - _Requirements: 12.5_

- [x] 17.2 Update AgentCompiler._build_tools to preserve tool order
  - Ensure tools are attached in the order specified in arms
  - Validate tool configurations are applied correctly
  - _Requirements: 14.5_

- [x] 17.3 Update AgentCompiler._build_memory to use enhanced HeartConfig
  - Apply history_length parameter correctly
  - Handle knowledge_enabled flag (future feature)
  - _Requirements: 16.4, 16.5_

- [x] 17.4 Update AgentCompiler to apply default guardrails
  - Apply default spine values when not specified
  - Ensure guardrails are always present
  - _Requirements: 17.5_

- [ ]* 17.5 Write property test for component compilation completeness
  - **Property 8: Component Compilation Completeness**
  - **Validates: Requirements 12.5, 14.5, 15.5, 16.4, 17.4**

- [ ]* 17.6 Write property test for default guardrail application
  - **Property 9: Default Guardrail Application**
  - **Validates: Requirements 17.5**

- [ ] 18. Add integration tests for new features
- [ ]* 18.1 Write test for component schema endpoint
  - Test GET /api/components/schemas returns all schemas
  - Test schemas contain required fields and validation rules
  - Test schemas match ComponentSchemaProvider output
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ]* 18.2 Write test for instruction improvement endpoint
  - Test POST /api/instructions/improve with valid request
  - Test improved instructions preserve intent
  - Test explanation is provided
  - Test fallback on error returns original instructions
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ]* 18.3 Write test for enhanced component validation
  - Test head configuration with invalid temperature fails
  - Test arms configuration with invalid tool config fails
  - Test legs configuration without required fields fails
  - Test heart configuration with invalid history_length fails
  - Test spine configuration with out-of-range values fails
  - _Requirements: 12.2, 12.3, 12.4, 14.4, 15.4, 16.2, 17.1, 17.2, 17.3_

- [ ]* 18.4 Write test for complete blueprint with all components
  - Test blueprint with all five components configured compiles correctly
  - Test compiled agent has all configurations applied
  - Test agent executes correctly with all components
  - _Requirements: 12.5, 14.5, 15.5, 16.4, 17.4_

- [x] 19. Update frontend to use new component configuration features
- [x] 19.1 Fetch component schemas on app load
  - Call GET /api/components/schemas when app initializes
  - Store schemas in frontend state for form generation
  - Use schemas to populate dropdowns and validate inputs
  - _Requirements: 11.1_

- [x] 19.2 Add instruction improvement UI to head configuration
  - Add "Improve Instructions" button in head configuration panel
  - Create modal/dialog for improvement goal input
  - Call POST /api/instructions/improve with current instructions
  - Display improved instructions with explanation
  - Allow user to accept or reject improvements
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 19.3 Enhance component configuration forms with validation
  - Use schemas to add client-side validation
  - Show validation errors inline in forms
  - Display parameter descriptions and ranges from schemas
  - _Requirements: 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 20. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
