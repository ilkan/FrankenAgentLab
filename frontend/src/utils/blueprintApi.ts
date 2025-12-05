/**
 * API client for blueprint management
 * 
 * This module provides backward-compatible functions that map to the unified
 * backend agent API endpoints. The "blueprint" terminology is maintained
 * for frontend compatibility while using the new /api/agents endpoints.
 * 
 * Requirements 8.1-8.5: Agent CRUD operations
 */

import {
  Agent,
  getUserAgents,
  getAgent,
  createAgent,
  updateAgent,
  deleteAgent,
  cloneAgent,
  AgentApiError,
} from './agentApi';

// Re-export types with Blueprint naming for backward compatibility
export interface Blueprint {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  blueprint_data: any;
  version: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface BlueprintListItem {
  id: string;
  name: string;
  description?: string;
  version: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// Re-export error class
export { AgentApiError };

/**
 * Convert Agent to Blueprint format for backward compatibility
 */
function agentToBlueprint(agent: Agent): Blueprint {
  return {
    id: agent.id,
    user_id: agent.user_id,
    name: agent.name,
    description: agent.description,
    blueprint_data: agent.blueprint_data,
    version: agent.version,
    is_public: agent.is_public,
    created_at: agent.created_at,
    updated_at: agent.updated_at,
  };
}

/**
 * Get all blueprints for the current user
 * Requirements 8.2: GET /api/agents returns all user's agents
 */
export async function getUserBlueprints(token: string): Promise<BlueprintListItem[]> {
  const agents = await getUserAgents(token);
  return agents.map(agent => ({
    id: agent.id,
    name: agent.name,
    description: agent.description,
    version: agent.version,
    is_public: agent.is_public,
    created_at: agent.created_at,
    updated_at: agent.updated_at,
  }));
}

/**
 * Get a specific blueprint by ID
 * Requirements 8.3: GET /api/agents/{id} returns agent if accessible
 */
export async function getBlueprint(token: string, blueprintId: string): Promise<Blueprint> {
  const agent = await getAgent(token, blueprintId);
  return agentToBlueprint(agent);
}

/**
 * Create a new blueprint
 * Requirements 8.1: POST /api/agents creates agent and returns it
 */
export async function createBlueprint(
  token: string,
  name: string,
  blueprintData: any,
  description?: string,
  isPublic: boolean = false
): Promise<Blueprint> {
  const agent = await createAgent(token, name, blueprintData, description, isPublic);
  return agentToBlueprint(agent);
}

/**
 * Update an existing blueprint
 * Requirements 8.4: PUT /api/agents/{id} updates and returns agent
 */
export async function updateBlueprint(
  token: string,
  blueprintId: string,
  updates: {
    name?: string;
    description?: string;
    blueprint_data?: any;
    is_public?: boolean;
  }
): Promise<Blueprint> {
  const agent = await updateAgent(token, blueprintId, updates);
  return agentToBlueprint(agent);
}

/**
 * Delete a blueprint (soft delete)
 * Requirements 8.5: DELETE /api/agents/{id} soft-deletes agent
 */
export async function deleteBlueprint(token: string, blueprintId: string): Promise<void> {
  await deleteAgent(token, blueprintId);
}

/**
 * Clone a public blueprint
 */
export async function cloneBlueprint(token: string, blueprintId: string): Promise<Blueprint> {
  const agent = await cloneAgent(token, blueprintId);
  return agentToBlueprint(agent);
}
