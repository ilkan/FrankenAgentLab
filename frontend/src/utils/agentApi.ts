/**
 * API client for agent management against the FrankenAgent backend
 * 
 * This module implements the frontend API calls for:
 * - Requirements 8.1-8.5: Agent CRUD operations
 * - Requirements 8.6-8.7: Profile operations
 * - Requirements 8.8-8.9: Logs and usage operations
 */

import { API_BASE_URL } from '../config';

// ============================================================================
// Types
// ============================================================================

export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  blueprint_data: any;
  version: number;
  is_public: boolean;
  is_deleted: boolean;
  clone_count: number;
  rating_sum: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface AgentListItem {
  id: string;
  name: string;
  description?: string;
  version: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  token_quota: number;
  token_used: number;
  remaining_quota: number;
  created_at: string;
  updated_at: string;
}

export interface ExecutionLog {
  id: string;
  user_id: string;
  agent_id: string;
  session_id?: string;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  tool_calls: any[];
  latency_ms: number;
  status: 'success' | 'error' | 'timeout' | 'quota_exceeded';
  error_message?: string;
  created_at: string;
}

export interface UsageStats {
  daily_tokens: number;
  weekly_tokens: number;
  monthly_tokens: number;
  daily_executions: number;
  weekly_executions: number;
  monthly_executions: number;
}

export interface QuotaInfo {
  quota: number;
  used: number;
  remaining: number;
  has_quota: boolean;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Custom error class for API errors
 */
export class AgentApiError extends Error {
  code: string;
  details?: Record<string, any>;
  statusCode: number;

  constructor(message: string, code: string, statusCode: number, details?: Record<string, any>) {
    super(message);
    this.name = 'AgentApiError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

/**
 * Parse error response from API
 */
async function parseErrorResponse(response: Response): Promise<AgentApiError> {
  try {
    const data = await response.json();
    if (data.error) {
      return new AgentApiError(
        data.error.message || response.statusText,
        data.error.code || 'UNKNOWN_ERROR',
        response.status,
        data.error.details
      );
    }
    if (data.detail) {
      // Handle FastAPI default error format
      const detail = typeof data.detail === 'string' ? data.detail : data.detail.message || JSON.stringify(data.detail);
      return new AgentApiError(detail, 'API_ERROR', response.status);
    }
    return new AgentApiError(response.statusText, 'UNKNOWN_ERROR', response.status);
  } catch {
    return new AgentApiError(response.statusText, 'UNKNOWN_ERROR', response.status);
  }
}

// ============================================================================
// Agent API Functions (Requirements 8.1-8.5)
// ============================================================================

/**
 * Create a new agent
 * Requirements 8.1: POST /api/agents creates agent and returns it
 */
export async function createAgent(
  token: string,
  name: string,
  blueprintData: any,
  description?: string,
  isPublic: boolean = false
): Promise<Agent> {
  const response = await fetch(`${API_BASE_URL}/api/agents`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      name,
      description,
      blueprint_data: blueprintData,
      is_public: isPublic,
    }),
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  return data.agent;
}

/**
 * Get all agents for the current user
 * Requirements 8.2: GET /api/agents returns all user's agents
 */
export async function getUserAgents(token: string): Promise<Agent[]> {
  const response = await fetch(`${API_BASE_URL}/api/agents`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  // Backend returns 'blueprints' field, not 'agents'
  return data.blueprints || data.agents || [];
}

/**
 * Get a specific agent by ID
 * Requirements 8.3: GET /api/agents/{id} returns agent if accessible
 */
export async function getAgent(token: string, agentId: string): Promise<Agent> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  // Backend returns the agent directly (BlueprintResponse), not wrapped
  return data;
}

/**
 * Update an existing agent
 * Requirements 8.4: PUT /api/agents/{id} updates and returns agent
 */
export async function updateAgent(
  token: string,
  agentId: string,
  updates: {
    name?: string;
    description?: string;
    blueprint_data?: any;
    is_public?: boolean;
  }
): Promise<Agent> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  // Backend returns the agent directly (BlueprintResponse), not wrapped
  return data;
}

/**
 * Delete an agent (soft delete)
 * Requirements 8.5: DELETE /api/agents/{id} soft-deletes agent
 */
export async function deleteAgent(token: string, agentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }
}

/**
 * Clone a public agent
 */
export async function cloneAgent(token: string, agentId: string): Promise<Agent> {
  const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/clone`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  // Backend returns the agent directly (BlueprintResponse), not wrapped
  return data;
}

// ============================================================================
// Profile API Functions (Requirements 8.6-8.7)
// ============================================================================

/**
 * Get the current user's profile
 * Requirements 8.6: GET /api/profile returns user's profile
 */
export async function getProfile(token: string): Promise<Profile> {
  const response = await fetch(`${API_BASE_URL}/api/profile`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  return data.profile;
}

/**
 * Update the current user's profile
 * Requirements 8.7: PUT /api/profile updates and returns profile
 */
export async function updateProfile(
  token: string,
  updates: {
    full_name?: string;
    avatar_url?: string;
  }
): Promise<Profile> {
  const response = await fetch(`${API_BASE_URL}/api/profile`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  return data.profile;
}

// ============================================================================
// Logs and Usage API Functions (Requirements 8.8-8.9)
// ============================================================================

/**
 * Get execution logs with filtering
 * Requirements 8.8: GET /api/logs returns logs with filtering and pagination
 */
export async function getExecutionLogs(
  token: string,
  options?: {
    agentId?: string;
    sessionId?: string;
    startDate?: Date;
    endDate?: Date;
    limit?: number;
    offset?: number;
  }
): Promise<ExecutionLog[]> {
  const params = new URLSearchParams();
  
  if (options?.agentId) params.append('agent_id', options.agentId);
  if (options?.sessionId) params.append('session_id', options.sessionId);
  if (options?.startDate) params.append('start_date', options.startDate.toISOString());
  if (options?.endDate) params.append('end_date', options.endDate.toISOString());
  if (options?.limit) params.append('limit', options.limit.toString());
  if (options?.offset) params.append('offset', options.offset.toString());

  const url = `${API_BASE_URL}/api/logs${params.toString() ? `?${params.toString()}` : ''}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  return data.logs || [];
}

/**
 * Get usage statistics
 * Requirements 8.9: GET /api/usage returns token usage statistics
 */
export async function getUsageStats(token: string): Promise<{ usage: UsageStats; quota: QuotaInfo }> {
  const response = await fetch(`${API_BASE_URL}/api/usage`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return response.json();
}

// ============================================================================
// API Key Management Functions
// ============================================================================

export interface APIKey {
  id: string;
  provider: string;
  key_name: string;
  key_preview: string;
  created_at: string;
  last_used_at?: string;
}

export interface AddAPIKeyRequest {
  provider: string;
  api_key: string;
  key_name?: string;
}

/**
 * Add a new API key for an LLM provider
 */
export async function addAPIKey(
  token: string,
  request: AddAPIKeyRequest
): Promise<APIKey> {
  const response = await fetch(`${API_BASE_URL}/api/keys`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return response.json();
}

/**
 * Get all API keys for the current user
 */
export async function getAPIKeys(token: string): Promise<APIKey[]> {
  const response = await fetch(`${API_BASE_URL}/api/keys`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  const data = await response.json();
  return data.keys || [];
}

/**
 * Delete an API key
 */
export async function deleteAPIKey(
  token: string,
  keyId: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/keys/${keyId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }
}
