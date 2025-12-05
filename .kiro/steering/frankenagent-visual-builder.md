---
inclusion: fileMatch
fileMatchPattern: "**/frontend/**/*"
---

# Visual Builder Implementation Guide

## Overview

The FrankenAgent Lab Visual Builder is a React + TypeScript drag-and-drop interface for creating AI agent blueprints using the Frankenstein metaphor. It provides real-time validation, live preview, and seamless export functionality.

## Architecture

### Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Zustand** - State management
- **React DnD** - Drag and drop
- **Shadcn/ui** - Component library
- **Tailwind CSS** - Styling
- **Vite** - Build tool

### Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── canvas/           # Drag-and-drop canvas
│   │   ├── panels/           # Side panels (toolbox, properties)
│   │   ├── dialogs/          # Modal dialogs
│   │   ├── ui/               # Shadcn/ui components
│   │   └── layout/           # Layout components
│   ├── stores/
│   │   └── agentStore.ts     # Zustand state management
│   ├── utils/
│   │   ├── blueprintConverter.ts  # Convert to YAML/JSON
│   │   └── validator.ts      # Real-time validation
│   ├── types/
│   │   └── agent.ts          # TypeScript types
│   └── App.tsx               # Main application
├── ARCHITECTURE.md           # Architecture documentation
├── COMPONENT_CONFIG_FEATURES.md  # Component features
└── HTTP_TOOL_UI_GUIDE.md     # HTTP tool UI guide
```

## State Management with Zustand

### Agent Store Pattern

```typescript
import { create } from 'zustand';
import { AgentState, BodyPart } from '../types/agent';

interface AgentStore extends AgentState {
  // Actions
  updateHead: (head: Partial<HeadConfig>) => void;
  addArm: (arm: ArmConfig) => void;
  removeArm: (id: string) => void;
  updateArm: (id: string, arm: Partial<ArmConfig>) => void;
  updateLegs: (legs: Partial<LegsConfig>) => void;
  updateHeart: (heart: Partial<HeartConfig>) => void;
  updateSpine: (spine: Partial<SpineConfig>) => void;
  
  // Validation
  validate: () => ValidationResult;
  
  // Export
  exportBlueprint: (format: 'yaml' | 'json') => string;
  
  // Reset
  reset: () => void;
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  // Initial state
  name: '',
  description: '',
  version: '1.0',
  head: {
    model: 'gpt-4o-mini',
    provider: 'openai',
    system_prompt: '',
    temperature: 0.7,
  },
  arms: [],
  legs: {
    execution_mode: 'single_agent',
  },
  heart: {
    memory: {
      type: 'conversation',
      max_messages: 20,
    },
  },
  spine: {
    max_tool_calls: 10,
    timeout_seconds: 60,
  },
  
  // Actions implementation
  updateHead: (head) => set((state) => ({
    head: { ...state.head, ...head }
  })),
  
  addArm: (arm) => set((state) => ({
    arms: [...state.arms, { ...arm, id: generateId() }]
  })),
  
  // ... other actions
}));
```

### State Persistence

```typescript
import { persist } from 'zustand/middleware';

export const useAgentStore = create<AgentStore>()(
  persist(
    (set, get) => ({
      // Store implementation
    }),
    {
      name: 'frankenagent-builder',
      version: 1,
    }
  )
);
```

## Drag and Drop Implementation

### Canvas Component

```typescript
import { useDrop } from 'react-dnd';
import { BodyPart } from '../types/agent';

export function Canvas() {
  const { arms, addArm } = useAgentStore();
  
  const [{ isOver }, drop] = useDrop(() => ({
    accept: 'TOOL',
    drop: (item: { type: string; config: any }) => {
      addArm({
        type: item.type,
        config: item.config,
      });
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
    }),
  }));
  
  return (
    <div
      ref={drop}
      className={cn(
        "canvas-area",
        isOver && "canvas-area-hover"
      )}
    >
      {/* Render body parts */}
      <HeadComponent />
      <ArmsComponent arms={arms} />
      <LegsComponent />
      <HeartComponent />
      <SpineComponent />
    </div>
  );
}
```

### Draggable Tool

```typescript
import { useDrag } from 'react-dnd';

export function ToolCard({ tool }: { tool: ToolDefinition }) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'TOOL',
    item: {
      type: tool.type,
      config: tool.defaultConfig,
    },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));
  
  return (
    <div
      ref={drag}
      className={cn(
        "tool-card",
        isDragging && "tool-card-dragging"
      )}
    >
      <h3>{tool.name}</h3>
      <p>{tool.description}</p>
    </div>
  );
}
```

## Real-time Validation

### Validation Rules

```typescript
export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning';
}

export function validateBlueprint(state: AgentState): ValidationResult {
  const errors: ValidationError[] = [];
  
  // Validate head
  if (!state.head.system_prompt) {
    errors.push({
      field: 'head.system_prompt',
      message: 'System prompt is required',
      severity: 'error',
    });
  }
  
  // Validate provider/model combination
  if (!isValidModelForProvider(state.head.model, state.head.provider)) {
    errors.push({
      field: 'head.model',
      message: `Model ${state.head.model} not supported by ${state.head.provider}`,
      severity: 'error',
    });
  }
  
  // Validate arms
  state.arms.forEach((arm, index) => {
    if (!arm.type) {
      errors.push({
        field: `arms[${index}].type`,
        message: 'Tool type is required',
        severity: 'error',
      });
    }
    
    // Validate tool-specific config
    const toolErrors = validateToolConfig(arm.type, arm.config);
    errors.push(...toolErrors);
  });
  
  // Validate guardrails
  if (state.spine.max_tool_calls < 1) {
    errors.push({
      field: 'spine.max_tool_calls',
      message: 'Max tool calls must be at least 1',
      severity: 'error',
    });
  }
  
  return {
    valid: errors.filter(e => e.severity === 'error').length === 0,
    errors,
    warnings: errors.filter(e => e.severity === 'warning'),
  };
}
```

### Live Validation Display

```typescript
export function ValidationPanel() {
  const state = useAgentStore();
  const validation = useMemo(() => validateBlueprint(state), [state]);
  
  if (validation.valid) {
    return (
      <div className="validation-success">
        ✅ Blueprint is valid
      </div>
    );
  }
  
  return (
    <div className="validation-errors">
      <h3>Validation Errors</h3>
      {validation.errors.map((error, i) => (
        <div key={i} className="validation-error">
          <span className="error-field">{error.field}</span>
          <span className="error-message">{error.message}</span>
        </div>
      ))}
    </div>
  );
}
```

## Blueprint Export

### YAML/JSON Conversion

```typescript
import yaml from 'js-yaml';

export function exportBlueprint(
  state: AgentState,
  format: 'yaml' | 'json'
): string {
  // Convert internal state to blueprint format
  const blueprint = {
    name: state.name,
    description: state.description,
    version: state.version,
    head: {
      model: state.head.model,
      provider: state.head.provider,
      system_prompt: state.head.system_prompt,
      temperature: state.head.temperature,
      max_tokens: state.head.max_tokens,
    },
    arms: state.arms.map(arm => ({
      type: arm.type,
      config: arm.config,
    })),
    legs: {
      execution_mode: state.legs.execution_mode,
      workflow_steps: state.legs.workflow_steps,
      team_members: state.legs.team_members,
    },
    heart: state.heart,
    spine: state.spine,
  };
  
  // Remove undefined/null values
  const cleaned = removeEmpty(blueprint);
  
  // Convert to format
  if (format === 'yaml') {
    return yaml.dump(cleaned, {
      indent: 2,
      lineWidth: 80,
      noRefs: true,
    });
  } else {
    return JSON.stringify(cleaned, null, 2);
  }
}

function removeEmpty(obj: any): any {
  return Object.entries(obj)
    .filter(([_, v]) => v != null)
    .reduce((acc, [k, v]) => ({
      ...acc,
      [k]: typeof v === 'object' ? removeEmpty(v) : v
    }), {});
}
```

### Download Handler

```typescript
export function downloadBlueprint(
  blueprint: string,
  filename: string,
  format: 'yaml' | 'json'
) {
  const blob = new Blob([blueprint], {
    type: format === 'yaml' ? 'text/yaml' : 'application/json',
  });
  
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
```

## Component Configuration

### HTTP Tool Configuration UI

```typescript
export function HttpToolConfig({ arm, onUpdate }: ConfigProps) {
  const [config, setConfig] = useState(arm.config);
  
  const handleUpdate = (field: string, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(arm.id, { config: updated });
  };
  
  return (
    <div className="tool-config">
      <Input
        label="Tool Name"
        value={config.name || ''}
        onChange={(e) => handleUpdate('name', e.target.value)}
        placeholder="API Client"
      />
      
      <Textarea
        label="Description"
        value={config.description || ''}
        onChange={(e) => handleUpdate('description', e.target.value)}
        placeholder="Make HTTP requests to external APIs"
      />
      
      <Input
        label="Base URL (optional)"
        value={config.base_url || ''}
        onChange={(e) => handleUpdate('base_url', e.target.value)}
        placeholder="https://api.example.com"
      />
      
      <div className="headers-section">
        <h4>Default Headers</h4>
        <KeyValueEditor
          value={config.default_headers || {}}
          onChange={(headers) => handleUpdate('default_headers', headers)}
        />
      </div>
      
      <Input
        type="number"
        label="Timeout (seconds)"
        value={config.timeout || 30}
        onChange={(e) => handleUpdate('timeout', parseInt(e.target.value))}
      />
    </div>
  );
}
```

### Tavily Search Configuration UI

```typescript
export function TavilySearchConfig({ arm, onUpdate }: ConfigProps) {
  const [config, setConfig] = useState(arm.config);
  
  return (
    <div className="tool-config">
      <Select
        label="Search Depth"
        value={config.search_depth || 'basic'}
        onChange={(value) => handleUpdate('search_depth', value)}
        options={[
          { value: 'basic', label: 'Basic' },
          { value: 'advanced', label: 'Advanced' },
        ]}
      />
      
      <Input
        type="number"
        label="Max Results"
        value={config.max_results || 5}
        onChange={(e) => handleUpdate('max_results', parseInt(e.target.value))}
        min={1}
        max={10}
      />
    </div>
  );
}
```

## Backend Integration

### API Client

```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Execute agent
export async function executeAgent(
  blueprintId: string,
  message: string
): Promise<ExecutionResult> {
  const response = await api.post('/execute', {
    blueprint_id: blueprintId,
    message,
  });
  return response.data;
}

// List blueprints
export async function listBlueprints(): Promise<BlueprintInfo[]> {
  const response = await api.get('/blueprints');
  return response.data.blueprints;
}

// Save blueprint
export async function saveBlueprint(
  blueprint: AgentState
): Promise<{ id: string }> {
  const response = await api.post('/blueprints', blueprint);
  return response.data;
}
```

### Testing Integration

```typescript
export function TestPanel() {
  const state = useAgentStore();
  const [message, setMessage] = useState('');
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [loading, setLoading] = useState(false);
  
  const handleTest = async () => {
    setLoading(true);
    try {
      // First, save the blueprint
      const { id } = await saveBlueprint(state);
      
      // Then execute it
      const result = await executeAgent(id, message);
      setResult(result);
    } catch (error) {
      console.error('Test failed:', error);
      // Show error toast
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="test-panel">
      <Textarea
        label="Test Message"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Enter a message to test your agent..."
      />
      
      <Button onClick={handleTest} disabled={loading}>
        {loading ? 'Testing...' : 'Test Agent'}
      </Button>
      
      {result && (
        <div className="test-result">
          <h3>Response</h3>
          <p>{result.response}</p>
          
          <h3>Execution Trace</h3>
          <ExecutionTrace trace={result.execution_trace} />
        </div>
      )}
    </div>
  );
}
```

## Styling and Theming

### Frankenstein Theme

```css
:root {
  /* Dark theme colors */
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  
  /* Frankenstein accent colors */
  --primary: 142 76% 36%;  /* Electric green */
  --secondary: 217 33% 17%;  /* Dark blue-gray */
  --accent: 47 96% 53%;  /* Lightning yellow */
  
  /* Body part colors */
  --head-color: 217 91% 60%;  /* Blue */
  --arms-color: 142 76% 36%;  /* Green */
  --legs-color: 280 65% 60%;  /* Purple */
  --heart-color: 0 84% 60%;  /* Red */
  --spine-color: 47 96% 53%;  /* Yellow */
}

.body-part {
  border: 2px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.2s;
}

.body-part:hover {
  border-color: var(--primary);
  box-shadow: 0 0 20px rgba(var(--primary-rgb), 0.3);
}

.body-part-head {
  border-color: var(--head-color);
}

.body-part-arms {
  border-color: var(--arms-color);
}

/* ... other body parts */
```

## Performance Optimization

### Memoization

```typescript
import { memo, useMemo } from 'react';

export const ArmCard = memo(({ arm, onUpdate, onRemove }: ArmCardProps) => {
  // Component implementation
});

export function Canvas() {
  const arms = useAgentStore(state => state.arms);
  
  const sortedArms = useMemo(() => {
    return [...arms].sort((a, b) => a.order - b.order);
  }, [arms]);
  
  return (
    <div className="canvas">
      {sortedArms.map(arm => (
        <ArmCard key={arm.id} arm={arm} />
      ))}
    </div>
  );
}
```

### Lazy Loading

```typescript
import { lazy, Suspense } from 'react';

const CodeEditor = lazy(() => import('./components/CodeEditor'));

export function BlueprintPreview() {
  return (
    <Suspense fallback={<div>Loading editor...</div>}>
      <CodeEditor />
    </Suspense>
  );
}
```

## Testing

### Component Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { HeadConfig } from './HeadConfig';

describe('HeadConfig', () => {
  it('updates system prompt', () => {
    const onUpdate = vi.fn();
    render(<HeadConfig onUpdate={onUpdate} />);
    
    const input = screen.getByLabelText('System Prompt');
    fireEvent.change(input, {
      target: { value: 'You are a helpful assistant' }
    });
    
    expect(onUpdate).toHaveBeenCalledWith({
      system_prompt: 'You are a helpful assistant'
    });
  });
});
```

### Integration Tests

```typescript
import { renderHook, act } from '@testing-library/react';
import { useAgentStore } from '../stores/agentStore';

describe('Agent Store', () => {
  it('adds and removes arms', () => {
    const { result } = renderHook(() => useAgentStore());
    
    act(() => {
      result.current.addArm({
        type: 'tavily_search',
        config: { max_results: 5 }
      });
    });
    
    expect(result.current.arms).toHaveLength(1);
    
    act(() => {
      result.current.removeArm(result.current.arms[0].id);
    });
    
    expect(result.current.arms).toHaveLength(0);
  });
});
```

## Common Patterns

### Error Boundaries

```typescript
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

### Toast Notifications

```typescript
import { toast } from 'sonner';

export function showSuccess(message: string) {
  toast.success(message);
}

export function showError(message: string) {
  toast.error(message);
}

export function showInfo(message: string) {
  toast.info(message);
}

// Usage
export function SaveButton() {
  const handleSave = async () => {
    try {
      await saveBlueprint(state);
      showSuccess('Blueprint saved successfully!');
    } catch (error) {
      showError('Failed to save blueprint');
    }
  };
  
  return <Button onClick={handleSave}>Save</Button>;
}
```

## Documentation

See also:
- [frontend/ARCHITECTURE.md](../../frontend/ARCHITECTURE.md) - Detailed architecture
- [frontend/COMPONENT_CONFIG_FEATURES.md](../../frontend/COMPONENT_CONFIG_FEATURES.md) - Component features
- [frontend/HTTP_TOOL_UI_GUIDE.md](../../frontend/HTTP_TOOL_UI_GUIDE.md) - HTTP tool UI guide
- [README_INTEGRATION.md](../../README_INTEGRATION.md) - Frontend-backend integration
