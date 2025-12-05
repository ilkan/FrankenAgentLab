import { useState, useEffect } from 'react';
import { NodeInstance, DEFAULT_CONFIGS } from '../types/agent-parts';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Sparkles, AlertCircle, Plus, X, RefreshCw } from 'lucide-react';
import { InstructionImprovementDialog } from './InstructionImprovementDialog';
import { useSchemaStore } from '../stores/schemaStore';
import { Alert, AlertDescription } from './ui/alert';
import { API_BASE_URL } from '../config';

// Dark mode input styling to match auth forms
const inputBaseClasses =
  'h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25';

const textareaBaseClasses =
  'rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25';

// Available models with provider mapping
const AVAILABLE_MODELS = [
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Cheapest)', provider: 'openai' },
  { value: 'gpt-4o', label: 'GPT-4o', provider: 'openai' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo', provider: 'openai' },
  { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku (Cheapest)', provider: 'anthropic' },
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet', provider: 'anthropic' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus', provider: 'anthropic' },
  { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B', provider: 'groq' },
  { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B (Cheapest)', provider: 'groq' },
  { value: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash (Cheapest)', provider: 'google' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro', provider: 'google' },
];

// Map head node IDs to their provider
const HEAD_TO_PROVIDER: Record<string, string> = {
  'gpt4o-mini': 'openai',
  'claude-haiku': 'anthropic',
  'groq-llama': 'groq',
  'gemini-pro': 'google',
};

interface NodeConfigDialogProps {
  node: NodeInstance | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (config: Record<string, any>) => void;
}

export function NodeConfigDialog({ node, open, onOpenChange, onSave }: NodeConfigDialogProps) {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [showInstructionImprovement, setShowInstructionImprovement] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [mcpConnecting, setMcpConnecting] = useState(false);
  const [mcpConnectionStatus, setMcpConnectionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [mcpAvailableTools, setMcpAvailableTools] = useState<Array<{name: string; description: string}>>([]);
  const [mcpSelectedTools, setMcpSelectedTools] = useState<string[]>([]);
  
  const { schemas } = useSchemaStore();

  useEffect(() => {
    if (node) {
      const defaultConfig = DEFAULT_CONFIGS[node.id] || {};
      const nodeConfig = node.config || {};
      
      // For head nodes, set default model if not present
      if (node.type === 'head' && !nodeConfig.model) {
        nodeConfig.model = 'gpt-4o-mini'; // Default to cheapest model
        nodeConfig.provider = 'openai';
      }
      
      setConfig({ ...defaultConfig, ...nodeConfig });
      setValidationErrors({});
      
      // For MCP tools, initialize selected tools from config
      if (node.id === 'mcp-tool' && nodeConfig.allowedTools) {
        setMcpSelectedTools(Array.isArray(nodeConfig.allowedTools) ? nodeConfig.allowedTools : []);
      } else {
        setMcpSelectedTools([]);
      }
      setMcpAvailableTools([]);
      setMcpConnectionStatus('idle');
    }
  }, [node]);

  if (!node) return null;
  
  const isHeadNode = node.type === 'head';

  const validateConfig = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!schemas) return true; // Skip validation if schemas not loaded
    
    // Validate head configuration
    if (isHeadNode && schemas.head) {
      const headParams = schemas.head.parameters;
      
      if (config.systemPrompt && headParams.system_prompt) {
        const maxLength = headParams.system_prompt.max_length;
        if (maxLength && config.systemPrompt.length > maxLength) {
          errors.systemPrompt = `System prompt must be ${maxLength} characters or less`;
        }
      }
      
      if (config.temperature !== undefined && headParams.temperature) {
        const min = headParams.temperature.min || 0;
        const max = headParams.temperature.max || 2;
        if (config.temperature < min || config.temperature > max) {
          errors.temperature = `Temperature must be between ${min} and ${max}`;
        }
      }
      
      if (config.maxTokens !== undefined && headParams.max_tokens) {
        const min = headParams.max_tokens.min || 1;
        if (config.maxTokens < min) {
          errors.maxTokens = `Max tokens must be at least ${min}`;
        }
      }
    }
    
    // Validate heart configuration
    if (node.type === 'heart' && schemas.heart) {
      if (config.maxMessages !== undefined) {
        const historyLength = schemas.heart.history_length;
        const min = historyLength.min || 1;
        const max = historyLength.max || 100;
        if (config.maxMessages < min || config.maxMessages > max) {
          errors.maxMessages = `History length must be between ${min} and ${max}`;
        }
      }
    }
    
    // Validate spine configuration
    if (node.type === 'spine' && schemas.spine) {
      if (config.maxCalls !== undefined) {
        const maxToolCalls = schemas.spine.max_tool_calls;
        const min = maxToolCalls.min || 1;
        const max = maxToolCalls.max || 100;
        if (config.maxCalls < min || config.maxCalls > max) {
          errors.maxCalls = `Max tool calls must be between ${min} and ${max}`;
        }
      }
      
      if (config.duration !== undefined) {
        const timeout = schemas.spine.timeout_seconds;
        const min = timeout.min || 1;
        const max = timeout.max || 300;
        if (config.duration < min || config.duration > max) {
          errors.duration = `Timeout must be between ${min} and ${max} seconds`;
        }
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleConnectMCP = async () => {
    if (!config.serverUrl) {
      setValidationErrors({ ...validationErrors, serverUrl: 'Server URL is required to connect' });
      return;
    }

    setMcpConnecting(true);
    setMcpConnectionStatus('idle');
    setMcpAvailableTools([]);

    try {
      // Call our backend API to test the MCP connection
      const response = await fetch(`${API_BASE_URL}/api/mcp/test-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          server_url: config.serverUrl,
          transport_type: config.transportType || 'sse',
          api_token: config.apiToken || null,
          auth_header: config.authHeader || 'Authorization',
          timeout: 10,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success && data.tools && data.tools.length > 0) {
        // Connection successful with tools
        setMcpConnectionStatus('success');
        setMcpAvailableTools(data.tools);
        
        // If no tools are selected yet, select all by default
        if (!mcpSelectedTools || mcpSelectedTools.length === 0) {
          const allToolNames = data.tools.map((t: any) => t.name);
          setMcpSelectedTools(allToolNames);
          setConfig({
            ...config,
            allowedTools: allToolNames,
          });
        }
        
        setValidationErrors({ ...validationErrors, serverUrl: '' });
      } else if (data.success && (!data.tools || data.tools.length === 0)) {
        // Connection successful but no tools found
        setMcpConnectionStatus('success');
        setValidationErrors({ 
          ...validationErrors, 
          serverUrl: 'Connected but no tools found on this server' 
        });
      } else {
        // Connection failed
        setMcpConnectionStatus('error');
        setValidationErrors({ 
          ...validationErrors, 
          serverUrl: data.error || 'Connection failed' 
        });
      }
    } catch (error) {
      setMcpConnectionStatus('error');
      
      let errorMessage = 'Connection failed';
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      setValidationErrors({ 
        ...validationErrors, 
        serverUrl: errorMessage
      });
    } finally {
      setMcpConnecting(false);
    }
  };

  const handleSave = () => {
    if (!validateConfig()) {
      return;
    }
    
    // Clean up temporary keys and empty entries from defaultHeaders
    const cleanedConfig = { ...config };
    if (cleanedConfig.defaultHeaders && typeof cleanedConfig.defaultHeaders === 'object') {
      const cleanedHeaders: Record<string, string> = {};
      Object.entries(cleanedConfig.defaultHeaders).forEach(([k, v]) => {
        // Skip temporary keys and entries with empty keys
        if (!k.startsWith('__new_') && k.trim() !== '' && typeof v === 'string') {
          cleanedHeaders[k] = v;
        }
      });
      cleanedConfig.defaultHeaders = cleanedHeaders;
    }
    
    onSave(cleanedConfig);
    onOpenChange(false);
  };

  const handleImprovedInstructions = (improvedInstructions: string) => {
    setConfig({ ...config, systemPrompt: improvedInstructions });
  };
  
  const getParameterDescription = (key: string): string | undefined => {
    if (!schemas) return undefined;
    
    if (isHeadNode && schemas.head.parameters[key]) {
      return schemas.head.parameters[key].description;
    }
    
    if (node.type === 'heart') {
      if (key === 'maxMessages' && schemas.heart.history_length) {
        return schemas.heart.history_length.description;
      }
    }
    
    if (node.type === 'spine') {
      if (key === 'maxCalls' && schemas.spine.max_tool_calls) {
        return schemas.spine.max_tool_calls.description;
      }
      if (key === 'duration' && schemas.spine.timeout_seconds) {
        return schemas.spine.timeout_seconds.description;
      }
    }
    
    return undefined;
  };

  const renderKeyValueEditor = (key: string, value: Record<string, string>, description?: string) => {
    const entries = Object.entries(value);
    
    const addEntry = () => {
      // Generate a unique temporary key for new entries
      const tempKey = `__new_${Date.now()}`;
      setConfig({ ...config, [key]: { ...value, [tempKey]: '' } });
    };
    
    const updateKey = (oldKey: string, newKey: string) => {
      const newValue = { ...value };
      if (oldKey !== newKey) {
        // If the new key already exists and it's not a temp key, don't overwrite
        if (newValue[newKey] !== undefined && !newKey.startsWith('__new_')) {
          return;
        }
        newValue[newKey] = newValue[oldKey];
        delete newValue[oldKey];
      }
      setConfig({ ...config, [key]: newValue });
    };
    
    const updateValue = (entryKey: string, newValue: string) => {
      setConfig({ ...config, [key]: { ...value, [entryKey]: newValue } });
    };
    
    const removeEntry = (entryKey: string) => {
      const newValue = { ...value };
      delete newValue[entryKey];
      setConfig({ ...config, [key]: newValue });
    };
    
    return (
      <div key={key} className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="capitalize text-gray-200">
            {key.replace(/([A-Z])/g, ' $1').trim()}
          </Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addEntry}
            className="gap-1 h-7 text-xs bg-[#0c1426] border-gray-800 text-gray-200 hover:bg-[#111c31] hover:text-white"
          >
            <Plus className="w-3 h-3" />
            Add Header
          </Button>
        </div>
        {description && (
          <p className="text-xs text-gray-500">{description}</p>
        )}
        <div className="space-y-2 max-h-[200px] overflow-y-auto pr-2 border border-gray-700 rounded-md p-2">
          {entries.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-2">No headers configured</p>
          ) : (
            entries.map(([entryKey, entryValue], index) => {
              const isTemporaryKey = entryKey.startsWith('__new_');
              const displayKey = isTemporaryKey ? '' : entryKey;
              
              return (
                <div key={index} className="flex gap-2 items-center">
                  <Input
                    placeholder="Header name (e.g., Authorization)"
                    value={displayKey}
                    onChange={(e) => updateKey(entryKey, e.target.value)}
                    className={`flex-1 h-8 text-sm ${inputBaseClasses}`}
                  />
                  <Input
                    placeholder="Header value (e.g., Bearer token)"
                    value={entryValue}
                    onChange={(e) => updateValue(entryKey, e.target.value)}
                    className={`flex-1 h-8 text-sm ${inputBaseClasses}`}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeEntry(entryKey)}
                    className="h-8 w-8 text-red-400 hover:text-red-300"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  };

  const renderMCPField = (key: string, value: any) => {
    const error = validationErrors[key];
    
    if (key === 'serverLabel') {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-gray-200">Server Label</Label>
          <p className="text-xs text-gray-500">
            Unique identifier for this MCP server (e.g., "aws-docs", "cats")
          </p>
          <Input
            id={key}
            value={value || ''}
            onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
            placeholder="e.g., aws-docs"
            autoComplete="off"
            data-form-type="other"
            data-lpignore="true"
            className={inputBaseClasses}
          />
        </div>
      );
    }
    
    if (key === 'serverUrlRow') {
      return (
        <div key={key} className="space-y-2">
          <Label className="text-gray-200">Server Connection</Label>
          <p className="text-xs text-gray-500 mb-2">
            Configure the MCP server endpoint and protocol
          </p>
          
          {/* Protocol + URL + Connect Button in same row */}
          <div className="flex gap-3 items-start">
            {/* Protocol Selector */}
            <div className="w-32">
              <Select
                value={config.transportType || 'sse'}
                onValueChange={(newValue) => setConfig({ ...config, transportType: newValue })}
              >
                <SelectTrigger className={inputBaseClasses}>
                  <SelectValue placeholder="Protocol" />
                </SelectTrigger>
                <SelectContent 
                  className="border-gray-800 z-50"
                  style={{ backgroundColor: '#0c1426' }}
                >
                  <SelectItem 
                    value="sse" 
                    className="text-gray-200 focus:bg-[#111c31] focus:text-white"
                    style={{ backgroundColor: '#0c1426' }}
                  >
                    SSE
                  </SelectItem>
                  <SelectItem 
                    value="http" 
                    className="text-gray-200 focus:bg-[#111c31] focus:text-white"
                    style={{ backgroundColor: '#0c1426' }}
                  >
                    HTTP
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Server URL */}
            <div className="flex-1">
              <Input
                id="serverUrl"
                value={config.serverUrl || ''}
                onChange={(e) => {
                  setConfig({ ...config, serverUrl: e.target.value });
                  setMcpConnectionStatus('idle');
                  setValidationErrors({ ...validationErrors, serverUrl: '' });
                }}
                placeholder="https://example.com/sse/"
                autoComplete="off"
                data-form-type="other"
                data-lpignore="true"
                className={inputBaseClasses}
              />
            </div>
            
            {/* Connect Button */}
            <Button
              type="button"
              variant="outline"
              onClick={handleConnectMCP}
              disabled={mcpConnecting || !config.serverUrl}
              className="gap-2 h-12 px-4 bg-[#0c1426] border-gray-800 text-gray-200 hover:bg-[#111c31] hover:text-white whitespace-nowrap"
            >
              <RefreshCw className={`w-4 h-4 ${mcpConnecting ? 'animate-spin' : ''}`} />
              {mcpConnecting ? 'Connecting...' : 'Connect'}
            </Button>
          </div>
          
          {/* Connection Status Messages */}
          {mcpConnectionStatus === 'success' && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-green-500/10 border border-green-500/50 mt-2">
              <AlertCircle className="w-4 h-4 text-green-400 mt-0.5" />
              <p className="text-sm font-medium text-green-400">
                ✓ Connected successfully! Tools populated below.
              </p>
            </div>
          )}
          {mcpConnectionStatus === 'error' && validationErrors.serverUrl && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-red-950/20 border border-red-800 mt-2">
              <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />
              <div className="text-sm text-red-300" style={{ color: '#fca5a5' }}>
                {validationErrors.serverUrl}
                <br />
                <span className="text-xs opacity-70 mt-1 block">
                  Note: CORS may block browser requests. The server will work when deployed.
                </span>
              </div>
            </div>
          )}
        </div>
      );
    }
    
    if (key === 'allowedTools') {
      return (
        <div key={key} className="space-y-3">
          <Label className="text-gray-200">Available Tools</Label>
          <p className="text-xs text-gray-500 mb-2">
            {mcpAvailableTools.length > 0 
              ? `Select the tools you want to enable (${mcpSelectedTools.length} of ${mcpAvailableTools.length} selected)`
              : 'Connect to the MCP server above to see available tools'}
          </p>
          
          {mcpAvailableTools.length > 0 ? (
            <div className="space-y-2 max-h-[400px] overflow-y-auto border border-gray-700 rounded-lg p-3 bg-[#0c1426] hide-scrollbar" style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {/* Select All / Deselect All */}
              <div className="flex items-center justify-between pb-2 border-b border-gray-700 mb-2 sticky top-0 bg-[#0c1426] z-10">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="select-all-tools"
                    checked={mcpSelectedTools.length === mcpAvailableTools.length}
                    onChange={(e) => {
                      if (e.target.checked) {
                        const allTools = mcpAvailableTools.map(t => t.name);
                        setMcpSelectedTools(allTools);
                        setConfig({ ...config, allowedTools: allTools });
                      } else {
                        setMcpSelectedTools([]);
                        setConfig({ ...config, allowedTools: [] });
                      }
                    }}
                    className="w-4 h-4 rounded border-gray-600 bg-[#0c1426] text-green-500 focus:ring-green-500 focus:ring-offset-0"
                  />
                  <Label htmlFor="select-all-tools" className="text-sm font-semibold text-gray-300 cursor-pointer">
                    Select All
                  </Label>
                </div>
                <span className="text-xs text-gray-500">
                  {mcpSelectedTools.length} selected
                </span>
              </div>
              
              {/* Individual tool checkboxes - 4 column grid */}
              <div className="grid grid-cols-4 gap-2">
                {mcpAvailableTools.map((tool, index) => {
                  const isSelected = mcpSelectedTools.includes(tool.name);
                  return (
                    <div key={index} className="flex items-start gap-2 p-2 rounded hover:bg-[#111c31] transition-colors border border-gray-700/50">
                      <input
                        type="checkbox"
                        id={`tool-${index}`}
                        checked={isSelected}
                        onChange={(e) => {
                          let newSelected: string[];
                          if (e.target.checked) {
                            newSelected = [...mcpSelectedTools, tool.name];
                          } else {
                            newSelected = mcpSelectedTools.filter(t => t !== tool.name);
                          }
                          setMcpSelectedTools(newSelected);
                          setConfig({ ...config, allowedTools: newSelected });
                        }}
                        className="w-4 h-4 mt-0.5 flex-shrink-0 rounded border-gray-600 bg-[#0c1426] text-green-500 focus:ring-green-500 focus:ring-offset-0"
                      />
                      <div className="flex-1 min-w-0">
                        <Label htmlFor={`tool-${index}`} className="text-xs font-medium text-gray-200 cursor-pointer block truncate" title={tool.name}>
                          {tool.name}
                        </Label>
                        {tool.description && (
                          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                            {tool.description}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="border border-gray-700 rounded-lg p-4 bg-[#0c1426] text-center">
              <p className="text-sm text-gray-500">
                No tools available. Click "Connect" above to fetch tools from the MCP server.
              </p>
            </div>
          )}
        </div>
      );
    }
    
    if (key === 'requireApproval') {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-gray-200">Require Approval</Label>
          <div className="w-32">
            <Select
              value={value || 'never'}
              onValueChange={(newValue) => setConfig({ ...config, [key]: newValue })}
            >
              <SelectTrigger className={inputBaseClasses}>
                <SelectValue placeholder="Select approval" />
              </SelectTrigger>
              <SelectContent 
                className="border-gray-800 z-50"
                style={{ backgroundColor: '#0c1426' }}
              >
                <SelectItem 
                  value="never" 
                  className="text-gray-200 focus:bg-[#111c31] focus:text-white" 
                  style={{ backgroundColor: '#0c1426' }}
                >
                  Never
                </SelectItem>
                <SelectItem 
                  value="once" 
                  className="text-gray-200 focus:bg-[#111c31] focus:text-white" 
                  style={{ backgroundColor: '#0c1426' }}
                >
                  Once
                </SelectItem>
                <SelectItem 
                  value="always" 
                  className="text-gray-200 focus:bg-[#111c31] focus:text-white" 
                  style={{ backgroundColor: '#0c1426' }}
                >
                  Always
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      );
    }
    
    if (key === 'apiToken') {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-gray-200">API Token (Optional)</Label>
          <p className="text-xs text-gray-500">
            Bearer token or API key for authenticated MCP servers (e.g., GitHub Copilot)
          </p>
          <Input
            id={key}
            type="password"
            value={value || ''}
            onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
            placeholder="ghp_xxxxxxxxxxxx or Bearer token"
            autoComplete="new-password"
            data-form-type="other"
            data-lpignore="true"
            className={inputBaseClasses}
          />
        </div>
      );
    }
    
    return null;
  };

  const renderConfigField = (key: string, value: any) => {
    const description = getParameterDescription(key);
    const error = validationErrors[key];
    
    // Skip apiKey field for head nodes (managed by backend)
    if (key === 'apiKey' && isHeadNode) {
      return null;
    }
    
    // Skip apiKey field for Tavily search (managed by backend)
    if (key === 'apiKey' && node.id === 'tavily-search') {
      return null;
    }
    
    // Special handling for model selection in head nodes
    if (key === 'model' && isHeadNode) {
      // Get the provider for this head type
      const headProvider = HEAD_TO_PROVIDER[node.id] || 'openai';
      
      // Filter models to only show those matching the head's provider
      const filteredModels = AVAILABLE_MODELS.filter(m => m.provider === headProvider);
      
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-gray-200">Model</Label>
          <p className="text-xs text-gray-500">
            Select the AI model for this agent. API keys are managed in Settings.
          </p>
          <Select
            value={value || filteredModels[0]?.value}
            onValueChange={(newModel) => {
              const modelInfo = AVAILABLE_MODELS.find(m => m.value === newModel);
              setConfig({ 
                ...config, 
                model: newModel,
                provider: modelInfo?.provider || headProvider
              });
            }}
          >
            <SelectTrigger className={inputBaseClasses}>
              <SelectValue placeholder="Select a model" />
            </SelectTrigger>
            <SelectContent 
              className="border-gray-800 z-50"
              style={{ backgroundColor: '#0c1426' }}
            >
              {filteredModels.map((model) => (
                <SelectItem 
                  key={model.value} 
                  value={model.value}
                  className="text-gray-200 focus:bg-[#111c31] focus:text-white"
                  style={{ backgroundColor: '#0c1426' }}
                >
                  {model.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      );
    }
    
    // Skip provider field (auto-set based on model)
    if (key === 'provider' && isHeadNode) {
      return null;
    }
    
    // Special handling for MCP tool fields - render as 2-column layout
    const isMCPTool = node.id === 'mcp-tool';
    
    // Skip MCP fields - they're rendered in custom layout
    const mcpFields = ['serverLabel', 'serverUrl', 'serverUrlRow', 'transportType', 'requireApproval', 'apiToken', 'allowedTools', 'authHeader'];
    if (isMCPTool && mcpFields.includes(key)) {
      return null;
    }
    
    // Special handling for object types (like defaultHeaders)
    if (typeof value === 'object' && value !== null && !Array.isArray(value) && key === 'defaultHeaders') {
      return renderKeyValueEditor(key, value, description);
    }
    
    // Special handling for systemPrompt in head nodes
    if (key === 'systemPrompt' && isHeadNode) {
      return (
        <div key={key} className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor={key} className="text-gray-200">System Prompt</Label>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowInstructionImprovement(true)}
              className="gap-2 bg-[#0c1426] border-gray-800 text-gray-200 hover:bg-[#111c31] hover:text-white"
            >
              <Sparkles className="w-3 h-3" />
              Improve with AI
            </Button>
          </div>
          {description && (
            <p className="text-xs text-gray-500">{description}</p>
          )}
          <Textarea
            id={key}
            value={value}
            onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
            rows={6}
            placeholder="Enter instructions for your agent..."
            className={`${textareaBaseClasses} ${error ? 'border-red-500' : ''}`}
          />
          {error && (
            <p className="text-xs text-red-500 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          )}
        </div>
      );
    }
    
    if (typeof value === 'boolean') {
      return (
        <div key={key} className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor={key} className="capitalize text-gray-200">
              {key.replace(/([A-Z])/g, ' $1').trim()}
            </Label>
            <Switch
              id={key}
              checked={value}
              onCheckedChange={(checked) => setConfig({ ...config, [key]: checked })}
            />
          </div>
          {description && (
            <p className="text-xs text-gray-500">{description}</p>
          )}
        </div>
      );
    }

    if (typeof value === 'number') {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="capitalize text-gray-200">
            {key.replace(/([A-Z])/g, ' $1').trim()}
          </Label>
          {description && (
            <p className="text-xs text-gray-500">{description}</p>
          )}
          <Input
            id={key}
            type="number"
            value={value}
            onChange={(e) => setConfig({ ...config, [key]: parseFloat(e.target.value) })}
            className={`${inputBaseClasses} ${error ? 'border-red-500' : ''}`}
          />
          {error && (
            <p className="text-xs text-red-500 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          )}
        </div>
      );
    }

    if (typeof value === 'string' && value.length > 50) {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="capitalize text-gray-200">
            {key.replace(/([A-Z])/g, ' $1').trim()}
          </Label>
          {description && (
            <p className="text-xs text-gray-500">{description}</p>
          )}
          <Textarea
            id={key}
            value={value}
            onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
            rows={4}
            className={`${textareaBaseClasses} ${error ? 'border-red-500' : ''}`}
          />
          {error && (
            <p className="text-xs text-red-500 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          )}
        </div>
      );
    }

    if (Array.isArray(value)) {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="capitalize text-gray-200">
            {key.replace(/([A-Z])/g, ' $1').trim()}
          </Label>
          {description && (
            <p className="text-xs text-gray-500">{description}</p>
          )}
          <Textarea
            id={key}
            value={value.join('\n')}
            onChange={(e) => setConfig({ ...config, [key]: e.target.value.split('\n').filter(Boolean) })}
            placeholder="One item per line"
            rows={4}
            className={`${textareaBaseClasses} ${error ? 'border-red-500' : ''}`}
          />
          {error && (
            <p className="text-xs text-red-500 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          )}
        </div>
      );
    }

    return (
      <div key={key} className="space-y-2">
        <Label htmlFor={key} className="capitalize text-gray-200">
          {key.replace(/([A-Z])/g, ' $1').trim()}
        </Label>
        {description && (
          <p className="text-xs text-gray-500">{description}</p>
        )}
        <Input
          id={key}
          value={value}
          onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
          className={`${inputBaseClasses} ${error ? 'border-red-500' : ''}`}
        />
        {error && (
          <p className="text-xs text-red-500 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {error}
          </p>
        )}
      </div>
    );
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent 
          className="w-[70vw] max-w-[70vw] !bg-[#0b1324] border-2 border-gray-800 rounded-xl shadow-[0_20px_80px_rgba(0,0,0,0.45)] px-7 py-6 max-h-[85vh] flex flex-col"
          style={{ backgroundColor: '#0b1324', borderColor: '#1f2937' }}
        >
          <DialogHeader className="space-y-2 flex-shrink-0">
            <DialogTitle className="text-2xl text-gray-100 font-semibold">
              Configure {node.name}
            </DialogTitle>
            <DialogDescription className="text-gray-400">
              Adjust the settings for this {node.category.toLowerCase()} component
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4 overflow-y-auto flex-1 min-h-0">
            {Object.keys(validationErrors).length > 0 && (
              <Alert className="bg-red-950/20 border-red-800">
                <AlertCircle className="w-4 h-4" />
                <AlertDescription>
                  Please fix the validation errors before saving.
                </AlertDescription>
              </Alert>
            )}
            
            {node.id === 'mcp-tool' ? (
              // MCP Tool: Custom layout with rows
              <div className="space-y-4">
                {/* Row 1: Server Label */}
                {renderMCPField('serverLabel', config.serverLabel)}
                
                {/* Row 2: Protocol + Server URL + Connect Button */}
                {renderMCPField('serverUrlRow', config.serverUrl)}
                
                {/* Row 3: Require Approval */}
                {renderMCPField('requireApproval', config.requireApproval)}
                
                {/* Row 4: API Token */}
                {renderMCPField('apiToken', config.apiToken)}
                
                {/* Row 5: Allowed Tools */}
                {renderMCPField('allowedTools', config.allowedTools)}
              </div>
            ) : (
              // Other nodes: single column layout
              Object.entries(config).map(([key, value]) => renderConfigField(key, value))
            )}
          </div>

          <DialogFooter className="flex-shrink-0 pt-4 border-t border-gray-800 mt-4">
            <Button 
              variant="outline" 
              onClick={() => onOpenChange(false)}
              className="bg-[#0c1426] border-gray-800 text-gray-200 hover:bg-[#111c31] hover:text-white"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSave}
              className="!bg-gradient-to-r !from-[#00b140] !via-[#12a72f] !to-[#55a100] hover:saturate-125 text-white font-semibold shadow-lg shadow-green-900/30 border-0"
              style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
            >
              Save Configuration
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Instruction Improvement Dialog */}
      {isHeadNode && (
        <InstructionImprovementDialog
          open={showInstructionImprovement}
          onOpenChange={setShowInstructionImprovement}
          currentInstructions={config.systemPrompt || ''}
          onAccept={handleImprovedInstructions}
          context={{
            agent_purpose: node.name,
          }}
        />
      )}
    </>
  );
}
