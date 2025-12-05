/**
 * Blueprint Converter - Transforms frontend AgentConfiguration to FrankenAgent Blueprint format
 * 
 * This bridges the visual drag-and-drop UI with the backend blueprint schema.
 */

import { AgentConfiguration, NodeInstance } from '../types/agent-parts';

export interface BlueprintFormat {
  name: string;
  description: string;
  version: string;
  head: {
    model: string;
    provider: string;
    system_prompt: string;
    temperature: number;
    max_tokens: number;
  };
  arms: Array<{
    name: string;
    type: string;
    config: Record<string, any>;
  }>;
  legs: {
    execution_mode: 'single_agent' | 'workflow' | 'team';
    workflow_steps?: string[];
    team_members?: any[];
  };
  heart?: {
    memory: {
      type: string;
      max_messages: number;
    };
    knowledge: {
      enabled: boolean;
    };
  };
  spine?: {
    max_tool_calls: number;
    timeout_seconds: number;
    allowed_domains: string[];
  };
}

/**
 * Maps frontend node IDs to backend provider/model identifiers
 */
const HEAD_MAPPING: Record<string, { provider: string; model: string }> = {
  'gpt4o-mini': { provider: 'openai', model: 'gpt-4o-mini' },
  'claude-haiku': { provider: 'anthropic', model: 'claude-3-haiku-20240307' },
  'groq-llama': { provider: 'groq', model: 'llama-3.1-70b-versatile' },
  'gemini-pro': { provider: 'google', model: 'gemini-pro' },
};

/**
 * Maps frontend tool IDs to backend tool types
 */
const ARM_MAPPING: Record<string, string> = {
  'tavily-search': 'tavily_search',
  'http-tool': 'http_tool',
  'file-loader': 'file_tools',
  'rag-knowledge': 'rag_knowledge',
  'python-executor': 'python_eval',
  'web-scraper': 'duckduckgo_search',
};

/**
 * Maps frontend execution mode IDs to backend execution modes
 */
const LEG_MAPPING: Record<string, 'single_agent' | 'workflow' | 'team'> = {
  'single-agent': 'single_agent',
  'workflow': 'workflow',
  'team': 'team',
};

/**
 * Converts frontend AgentConfiguration to backend Blueprint format
 */
export function convertToBlueprint(
  config: AgentConfiguration,
  agentName: string = 'Untitled Agent',
  agentDescription: string = 'Agent created with Frankenstein Builder'
): BlueprintFormat {
  // Validate required fields
  if (!config.head) {
    throw new Error('Head (LLM) is required to generate a blueprint');
  }
  if (!config.leg) {
    throw new Error('Execution mode (Leg) is required to generate a blueprint');
  }

  // Convert head
  const headMapping = HEAD_MAPPING[config.head.id];
  if (!headMapping) {
    throw new Error(`Unknown head type: ${config.head.id}`);
  }

  const blueprint: BlueprintFormat = {
    name: agentName,
    description: agentDescription,
    version: '1.0',
    head: {
      model: headMapping.model,
      provider: headMapping.provider,
      system_prompt: config.head.config?.systemPrompt || 'You are a helpful AI assistant.',
      temperature: config.head.config?.temperature || 0.7,
      max_tokens: config.head.config?.maxTokens || 2000,
    },
    arms: config.arms.map((arm) => {
      const toolType = ARM_MAPPING[arm.id];
      if (!toolType) {
        throw new Error(`Unknown tool type: ${arm.id}`);
      }
      return {
        name: arm.name.toLowerCase().replace(/\s+/g, '_'),
        type: toolType,
        config: arm.config || {},
      };
    }),
    legs: {
      execution_mode: LEG_MAPPING[config.leg.id] || 'single_agent',
      workflow_steps: config.leg.config?.steps || [],
      team_members: config.leg.config?.specialists || [],
    },
  };

  // Add optional heart (memory)
  if (config.heart) {
    blueprint.heart = {
      memory: {
        type: config.heart.config?.storageType || 'conversation',
        max_messages: config.heart.config?.maxMessages || 20,
      },
      knowledge: {
        enabled: config.heart.id === 'kb-embeddings',
      },
    };
  }

  // Add optional spine (guardrails)
  if (config.spine) {
    blueprint.spine = {
      max_tool_calls: config.spine.config?.maxCalls || 10,
      timeout_seconds: config.spine.config?.duration || 60,
      allowed_domains: config.spine.config?.domains || [],
    };
  }

  return blueprint;
}

/**
 * Exports blueprint as YAML string
 */
export function exportAsYAML(blueprint: BlueprintFormat): string {
  // Simple YAML serialization (for production, use a proper YAML library)
  const yaml: string[] = [];
  
  yaml.push(`name: "${blueprint.name}"`);
  yaml.push(`description: "${blueprint.description}"`);
  yaml.push(`version: "${blueprint.version}"`);
  yaml.push('');
  
  yaml.push('head:');
  yaml.push(`  model: "${blueprint.head.model}"`);
  yaml.push(`  provider: "${blueprint.head.provider}"`);
  yaml.push(`  system_prompt: "${blueprint.head.system_prompt}"`);
  yaml.push(`  temperature: ${blueprint.head.temperature}`);
  yaml.push(`  max_tokens: ${blueprint.head.max_tokens}`);
  yaml.push('');
  
  if (blueprint.arms.length > 0) {
    yaml.push('arms:');
    blueprint.arms.forEach((arm) => {
      yaml.push(`  - name: "${arm.name}"`);
      yaml.push(`    type: "${arm.type}"`);
      yaml.push(`    config:`);
      Object.entries(arm.config).forEach(([key, value]) => {
        yaml.push(`      ${key}: ${JSON.stringify(value)}`);
      });
    });
    yaml.push('');
  }
  
  yaml.push('legs:');
  yaml.push(`  execution_mode: "${blueprint.legs.execution_mode}"`);
  if (blueprint.legs.workflow_steps && blueprint.legs.workflow_steps.length > 0) {
    yaml.push('  workflow_steps:');
    blueprint.legs.workflow_steps.forEach((step) => {
      yaml.push(`    - "${step}"`);
    });
  }
  yaml.push('');
  
  if (blueprint.heart) {
    yaml.push('heart:');
    yaml.push('  memory:');
    yaml.push(`    type: "${blueprint.heart.memory.type}"`);
    yaml.push(`    max_messages: ${blueprint.heart.memory.max_messages}`);
    yaml.push('  knowledge:');
    yaml.push(`    enabled: ${blueprint.heart.knowledge.enabled}`);
    yaml.push('');
  }
  
  if (blueprint.spine) {
    yaml.push('spine:');
    yaml.push(`  max_tool_calls: ${blueprint.spine.max_tool_calls}`);
    yaml.push(`  timeout_seconds: ${blueprint.spine.timeout_seconds}`);
    if (blueprint.spine.allowed_domains.length > 0) {
      yaml.push('  allowed_domains:');
      blueprint.spine.allowed_domains.forEach((domain) => {
        yaml.push(`    - "${domain}"`);
      });
    }
  }
  
  return yaml.join('\n');
}

/**
 * Exports blueprint as JSON string
 */
export function exportAsJSON(blueprint: BlueprintFormat): string {
  return JSON.stringify(blueprint, null, 2);
}

/**
 * Downloads blueprint as a file
 */
export function downloadBlueprint(
  blueprint: BlueprintFormat,
  format: 'yaml' | 'json' = 'yaml'
): void {
  const content = format === 'yaml' ? exportAsYAML(blueprint) : exportAsJSON(blueprint);
  const filename = `${blueprint.name.toLowerCase().replace(/\s+/g, '_')}.${format}`;
  const mimeType = format === 'yaml' ? 'text/yaml' : 'application/json';
  
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Validates blueprint before export
 */
export function validateBlueprint(config: AgentConfiguration): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (!config.head) {
    errors.push('Head (LLM) is required');
  }
  
  if (!config.leg) {
    errors.push('Execution mode (Leg) is required');
  }
  
  if (config.arms.length > 6) {
    errors.push('Maximum 6 tools allowed');
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}
