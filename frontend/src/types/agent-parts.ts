export interface BodyPart {
  id: string;
  type: 'head' | 'arm' | 'leg' | 'heart' | 'spine';
  name: string;
  category: string;
  icon?: string;
  color: string;
  config?: Record<string, any>;
  comingSoon?: boolean;
}

export interface NodeInstance extends BodyPart {
  instanceId: string;
  position: { x: number; y: number };
  config: Record<string, any>;
}

export interface TeamMember {
  id: string;
  name: string;
  role: string;
  head?: NodeInstance;
  arms: NodeInstance[];
  heart?: NodeInstance;
}

export interface AgentConfiguration {
  head?: NodeInstance;
  arms: NodeInstance[]; // 0-6 tools supported
  heart?: NodeInstance; // 0-1 optional
  leg?: NodeInstance; // 1 required - execution mode
  spine?: NodeInstance; // 0-1 optional - guardrails
  teamMembers?: TeamMember[]; // For team execution mode
}

export const DEFAULT_CONFIGS: Record<string, any> = {
  'gpt4o-mini': {
    model: 'gpt-4o-mini',
    provider: 'openai',
    temperature: 0.7,
    maxTokens: 1000,
    systemPrompt: 'You are a helpful AI assistant.',
  },
  'claude-haiku': {
    model: 'claude-3-5-haiku-20241022',
    provider: 'anthropic',
    temperature: 0.7,
    maxTokens: 1000,
    systemPrompt: 'You are a helpful AI assistant.',
  },
  'groq-llama': {
    model: 'llama-3.1-8b-instant',
    provider: 'groq',
    temperature: 0.7,
    maxTokens: 1000,
    systemPrompt: 'You are a helpful AI assistant.',
  },
  'gemini-pro': {
    model: 'gemini-2.0-flash-exp',
    provider: 'google',
    temperature: 0.7,
    maxTokens: 1000,
    systemPrompt: 'You are a helpful AI assistant.',
  },
  'tavily-search': {
    maxResults: 5,
    searchDepth: 'basic',
  },
  'http-tool': {
    name: 'HTTP Request',
    description: 'Make HTTP requests to external APIs',
    baseUrl: '',
    defaultHeaders: {},
    timeout: 30,
  },
  'mcp-tool': {
    transportType: 'http',
    serverLabel: '',
    serverUrl: '',
    allowedTools: [],
    requireApproval: 'never',
    apiToken: '',
    authHeader: 'Authorization',
  },
  'file-loader': {
    supportedFormats: ['pdf', 'txt', 'docx'],
    maxFileSize: '10MB',
  },
  'rag-knowledge': {
    embeddingModel: 'text-embedding-ada-002',
    chunkSize: 1000,
    chunkOverlap: 200,
  },
  'python-executor': {
    timeout: 30,
    allowedLibraries: ['numpy', 'pandas', 'matplotlib'],
  },
  'web-scraper': {
    timeout: 10,
    userAgent: 'AI-Agent-Bot',
  },
  'single-agent': {
    autonomous: true,
    maxIterations: 10,
  },
  'workflow': {
    steps: [],
    errorHandling: 'continue',
  },
  'team': {
    leaderModel: 'gpt-4',
    specialists: [],
  },
  'convo-memory': {
    maxMessages: 10,
    summaryThreshold: 20,
  },
  'longterm-memory': {
    storageType: 'vector',
    retrievalLimit: 5,
  },
  'kb-embeddings': {
    embeddingModel: 'text-embedding-ada-002',
    dimension: 1536,
  },
  'max-tool-calls': {
    maxCalls: 5,
    timeWindow: '1m',
  },
  'timeout': {
    duration: 30,
    unit: 'seconds',
  },
  'allowed-domains': {
    domains: [],
    blockByDefault: false,
  },
};

export const BODY_PARTS_LIBRARY: Record<string, BodyPart[]> = {
  heads: [
    { id: 'gpt4o-mini', type: 'head', name: 'OpenAI GPT', category: 'Head', color: '#10a37f' },
    { id: 'claude-haiku', type: 'head', name: 'Claude', category: 'Head', color: '#d97757', comingSoon: true },
    //{ id: 'groq-llama', type: 'head', name: 'Groq', category: 'Head', color: '#f55036', comingSoon: true },
    { id: 'gemini-pro', type: 'head', name: 'Gemini', category: 'Head', color: '#4285f4', comingSoon: true },
  ],
  arms: [
    { id: 'tavily-search', type: 'arm', name: 'Tavily Search', category: 'Tool', color: '#8b5cf6' },
    { id: 'http-tool', type: 'arm', name: 'HTTP Tool', category: 'Tool', color: '#06b6d4' },
    { id: 'mcp-tool', type: 'arm', name: 'MCP Tool', category: 'Tool', color: '#14b8a6' },
    { id: 'file-loader', type: 'arm', name: 'File Loader', category: 'Tool', color: '#f59e0b', comingSoon: true  },
    { id: 'rag-knowledge', type: 'arm', name: 'RAG Knowledge', category: 'Tool', color: '#ec4899', comingSoon: true },
    { id: 'python-executor', type: 'arm', name: 'Python Executor', category: 'Tool', color: '#3b82f6', comingSoon: true },
    { id: 'web-scraper', type: 'arm', name: 'Web Scraper', category: 'Tool', color: '#10b981', comingSoon: true },
  ],
  legs: [
    { id: 'single-agent', type: 'leg', name: 'Single Agent', category: 'Execution', color: '#6366f1' },
    { id: 'team', type: 'leg', name: 'Team', category: 'Execution', color: '#a855f7'},
    { id: 'workflow', type: 'leg', name: 'Workflow', category: 'Execution', color: '#8b5cf6', comingSoon: true },
  ],
  hearts: [
    { id: 'convo-memory', type: 'heart', name: 'Convo Memory', category: 'Memory', color: '#ef4444' },
    { id: 'longterm-memory', type: 'heart', name: 'Long-term Memory', category: 'Memory', color: '#dc2626', comingSoon: true },
    { id: 'kb-embeddings', type: 'heart', name: 'KB Embeddings', category: 'Memory', color: '#f87171', comingSoon:true },
  ],
  spines: [
    { id: 'max-tool-calls', type: 'spine', name: 'Max Tool Calls', category: 'Guardrail', color: '#78716c' },
    { id: 'timeout', type: 'spine', name: 'Timeout', category: 'Guardrail', color: '#57534e' },
    { id: 'allowed-domains', type: 'spine', name: 'Allowed Domains', category: 'Guardrail', color: '#44403c' },
  ],
};
