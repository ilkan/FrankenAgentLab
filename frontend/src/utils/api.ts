/**
 * API client for FrankenAgent Lab backend
 */

import { API_BASE_URL } from '../config';

export interface ValidationError {
  field: string;
  message: string;
}

export interface ValidateResponse {
  valid: boolean;
  blueprint_id?: string;
  normalized_blueprint?: any;
  errors: ValidationError[];
}

export interface ToolCallLog {
  tool: string;
  args: Record<string, any>;
  duration_ms: number;
  success: boolean;
  result?: string;
  error?: string;
}

export interface RunResponse {
  response?: string;
  session_id: string;
  tool_calls: ToolCallLog[];
  guardrails_triggered: string[];
  total_latency_ms: number;
  error?: string;
}

export interface LogEntry {
  timestamp: string;
  event_type: string;
  message?: string;
  tool_name?: string;
  args?: Record<string, any>;
  duration_ms?: number;
  success?: boolean;
  result?: string;
  error?: string;
  details?: Record<string, any>;
}

export interface LogsResponse {
  session_id: string;
  logs: LogEntry[];
}

/**
 * Convert frontend AgentConfiguration to backend blueprint format
 */
export function convertToBlueprint(config: any): any {
  const isTeamMode = config.leg?.id === 'team';
  const teamMembers = config.teamMembers || [];
  
  // For team mode, use the leader's (first member's) head as the main head
  const leaderHead = isTeamMode && teamMembers.length > 0 ? teamMembers[0]?.head : null;
  
  const blueprint: any = {
    name: isTeamMode 
      ? (teamMembers[0]?.name || 'Team Agent')
      : (config.head?.name || 'Unnamed Agent'),
  };

  // Head (required) - use leader's head in team mode
  if (config.head || leaderHead) {
    const headSource = config.head || leaderHead;
    const headConfig = headSource.config || {};
    
    // Use model and provider from config, with fallback to defaults
    const provider = headConfig.provider || 'openai';
    const model = headConfig.model || 'gpt-4o-mini';
    
    blueprint.head = {
      provider,
      model,
      system_prompt: headConfig.systemPrompt || (isTeamMode 
        ? 'You are a team coordinator managing multiple specialized agents.'
        : 'You are a helpful AI assistant.'),
      temperature: headConfig.temperature || 0.7,
      max_tokens: headConfig.maxTokens || 1000,
    };
  }

  // Arms (tools)
  if (config.arms && config.arms.length > 0) {
    blueprint.arms = config.arms.map((arm: any) => {
      const armConfig = arm.config || {};
      
      // Map frontend tool IDs to backend tool types
      let toolType = arm.id; // Use arm.id directly as default
      let toolConfig: any = {};
      
      if (arm.id === 'tavily-search') {
        toolType = 'tavily_search';
        toolConfig = {
          max_results: armConfig.maxResults || 5,
          search_depth: armConfig.searchDepth || 'basic',
        };
      } else if (arm.id === 'http-tool') {
        toolType = 'http_tool';
        toolConfig = {
          name: armConfig.name || 'HTTP Request',
          description: armConfig.description || 'Make HTTP requests to external APIs',
          base_url: armConfig.baseUrl || '',
          default_headers: armConfig.defaultHeaders || {},
          timeout: armConfig.timeout || 30,
        };
      } else if (arm.id === 'mcp-tool') {
        toolType = 'mcp_tool';
        toolConfig = {
          transport_type: armConfig.transportType || 'sse',
          server_label: armConfig.serverLabel || armConfig.serverName || '',
          server_url: armConfig.serverUrl || '',
          allowed_tools: armConfig.allowedTools || [],
          require_approval: armConfig.requireApproval || 'never',
          api_token: armConfig.apiToken || '',
          auth_header: armConfig.authHeader || 'Authorization',
        };
      }
      // Other tools not yet supported in backend
      
      return {
        type: toolType,
        config: toolConfig,
      };
    });
  }

  // Legs (execution mode) - required
  if (config.leg) {
    // Map frontend leg IDs to backend execution modes
    let executionMode = 'single_agent';
    if (config.leg.id === 'single-agent') {
      executionMode = 'single_agent';
    } else if (config.leg.id === 'team') {
      executionMode = 'team';
    } else if (config.leg.id === 'workflow') {
      executionMode = 'workflow';
    } else {
      executionMode = config.leg.id;
    }
    
    blueprint.legs = {
      execution_mode: executionMode,
    };
    
    // For team mode, include team members
    if (config.leg.id === 'team' && config.teamMembers && config.teamMembers.length > 0) {
      blueprint.legs.team_members = config.teamMembers.map((member: any) => {
        const memberBlueprint: any = {
          name: member.name,
          role: member.role,
        };
        
        // Convert member's head
        if (member.head) {
          const headConfig = member.head.config || {};
          memberBlueprint.head = {
            provider: headConfig.provider || 'openai',
            model: headConfig.model || 'gpt-4o-mini',
            system_prompt: headConfig.systemPrompt || `You are ${member.name}. ${member.role}`,
            temperature: headConfig.temperature || 0.7,
            max_tokens: headConfig.maxTokens || 1000,
          };
        }
        
        // Convert member's arms (tools)
        if (member.arms && member.arms.length > 0) {
          memberBlueprint.arms = member.arms.map((arm: any) => {
            const armConfig = arm.config || {};
            let toolType = arm.id;
            let toolConfig: any = {};
            
            if (arm.id === 'tavily-search') {
              toolType = 'tavily_search';
              toolConfig = {
                max_results: armConfig.maxResults || 5,
                search_depth: armConfig.searchDepth || 'basic',
              };
            } else if (arm.id === 'http-tool') {
              toolType = 'http_tool';
              toolConfig = {
                name: armConfig.name || 'HTTP Request',
                description: armConfig.description || 'Make HTTP requests',
                base_url: armConfig.baseUrl || '',
                default_headers: armConfig.defaultHeaders || {},
                timeout: armConfig.timeout || 30,
              };
            } else if (arm.id === 'mcp-tool') {
              toolType = 'mcp_tool';
              toolConfig = {
                transport_type: armConfig.transportType || 'sse',
                server_label: armConfig.serverLabel || '',
                server_url: armConfig.serverUrl || '',
                allowed_tools: armConfig.allowedTools || [],
                require_approval: armConfig.requireApproval || 'never',
                api_token: armConfig.apiToken || '',
                auth_header: armConfig.authHeader || 'Authorization',
              };
            }
            
            return { type: toolType, config: toolConfig };
          });
        }
        
        // Convert member's heart (memory)
        if (member.heart) {
          const heartConfig = member.heart.config || {};
          memberBlueprint.heart = {
            memory_enabled: true,
            history_length: heartConfig.maxMessages || 10,
          };
        }
        
        return memberBlueprint;
      });
    }
  }

  // Heart (memory) - optional
  if (config.heart) {
    const heartConfig = config.heart.config || {};
    blueprint.heart = {
      memory_enabled: true,
      history_length: heartConfig.maxMessages || 10,
      knowledge_enabled: config.heart.id === 'kb-embeddings',
    };
  }

  // Spine (guardrails) - optional
  if (config.spine) {
    const spineConfig = config.spine.config || {};
    blueprint.spine = {};
    
    if (config.spine.id === 'max-tool-calls') {
      blueprint.spine.max_tool_calls = spineConfig.maxCalls || 10;
    } else if (config.spine.id === 'timeout') {
      blueprint.spine.timeout_seconds = spineConfig.duration || 60;
    } else if (config.spine.id === 'allowed-domains') {
      blueprint.spine.allowed_domains = spineConfig.domains || [];
    }
  }

  return blueprint;
}

/**
 * Validate and optionally compile a blueprint
 */
export async function validateBlueprint(
  blueprint: any,
  compile: boolean = false
): Promise<ValidateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/blueprints/validate-and-compile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      blueprint,
      compile,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Run an agent with a message
 */
export async function runAgent(
  blueprint: any,
  message: string,
  sessionId?: string,
  token?: string
): Promise<RunResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/api/agents/run`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      blueprint,
      message,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get logs for a session
 */
export async function getLogs(sessionId: string): Promise<LogsResponse> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/api/agents/logs?session_id=${sessionId}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Component schema types
 */
export interface ParameterSchema {
  type: string;
  min?: number;
  max?: number;
  max_length?: number;
  default?: any;
  optional?: boolean;
  description?: string;
  enum?: string[];
  items?: string;
}

export interface ToolConfigSchema {
  [key: string]: ParameterSchema;
}

export interface HeadSchema {
  providers: string[];
  models: Record<string, string[]>;
  parameters: Record<string, ParameterSchema>;
}

export interface ArmsSchema {
  tool_types: string[];
  tool_configs: Record<string, ToolConfigSchema>;
}

export interface LegsSchema {
  execution_modes: string[];
  mode_requirements: Record<string, any>;
}

export interface HeartSchema {
  memory_enabled: ParameterSchema;
  history_length: ParameterSchema;
  knowledge_enabled: ParameterSchema;
}

export interface SpineSchema {
  max_tool_calls: ParameterSchema;
  timeout_seconds: ParameterSchema;
  allowed_domains: ParameterSchema;
}

export interface ComponentSchemas {
  head: HeadSchema;
  arms: ArmsSchema;
  legs: LegsSchema;
  heart: HeartSchema;
  spine: SpineSchema;
}

/**
 * Get component configuration schemas
 */
export async function getComponentSchemas(): Promise<ComponentSchemas> {
  const response = await fetch(`${API_BASE_URL}/api/components/schemas`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Instruction improvement types
 */
export interface ImproveInstructionsRequest {
  current_instructions: string;
  improvement_goal: string;
  context?: {
    agent_purpose?: string;
    tools_available?: string[];
  };
}

export interface ImproveInstructionsResponse {
  improved_instructions: string;
  explanation: string;
  suggestions: string[];
}

/**
 * Improve agent instructions using LLM
 */
export async function improveInstructions(
  request: ImproveInstructionsRequest
): Promise<ImproveInstructionsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/instructions/improve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
