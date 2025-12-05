import { useState, useRef, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Send, Loader2, User, Bot } from 'lucide-react';
import { Badge } from './ui/badge';
import { runAgent, ToolCallLog } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';
import { AuthDialog } from './auth/AuthDialog';

// CSS to hide scrollbar
const hideScrollbarStyle = `
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
`;

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCallLog[];
  totalDuration?: number;
  error?: boolean;
}

interface ChatPanelProps {
  blueprint?: any;
  blueprintName?: string;
  onLogUpdate?: (log: string) => void;
  onSessionIdChange?: (sessionId: string) => void;
  onClearRef?: (clearFn: () => void) => void;
}

export function ChatPanel({ blueprint, blueprintName, onLogUpdate, onSessionIdChange, onClearRef }: ChatPanelProps) {
  const { token, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState([] as Message[]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const scrollRef = useRef(null as HTMLDivElement | null);

  // Expose clear function to parent
  useEffect(() => {
    if (onClearRef) {
      onClearRef(() => {
        setMessages([]);
        setSessionId(undefined);
        setInput('');
      });
    }
  }, [onClearRef]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || !blueprint || isLoading) return;

    // Check if user is authenticated before sending message
    if (!isAuthenticated) {
      setShowAuthDialog(true);
      return;
    }

    const currentInput = input;
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: currentInput,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    onLogUpdate?.(`[${new Date().toISOString()}] Sending message to ${blueprintName || 'agent'}`);

    try {
      const data = await runAgent(blueprint, currentInput, sessionId, token || undefined);

      // Store session ID for conversation continuity
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
        onSessionIdChange?.(data.session_id);
        onLogUpdate?.(`[${new Date().toISOString()}] Session started: ${data.session_id}`);
      }

      onLogUpdate?.(`[${new Date().toISOString()}] Received response (${data.total_latency_ms}ms)`);
      
      if (data.tool_calls && data.tool_calls.length > 0) {
        onLogUpdate?.(`[${new Date().toISOString()}] Tool calls: ${data.tool_calls.length}`);
        data.tool_calls.forEach((call) => {
          const status = call.success ? '✓' : '✗';
          onLogUpdate?.(`  ${status} ${call.tool} (${call.duration_ms}ms)`);
        });
      }

      if (data.guardrails_triggered && data.guardrails_triggered.length > 0) {
        onLogUpdate?.(`[${new Date().toISOString()}] ⚠ Guardrails triggered: ${data.guardrails_triggered.join(', ')}`);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || data.error || 'No response',
        timestamp: new Date(),
        toolCalls: data.tool_calls,
        totalDuration: data.total_latency_ms,
        error: !!data.error,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      onLogUpdate?.(`[${new Date().toISOString()}] ERROR: ${errorMessage}`);
      
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date(),
        error: true,
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: any) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!blueprint) {
    return (
      <div className="w-full border-l border-gray-800 bg-gray-950 flex flex-col h-full">
        <div className="p-3 border-b border-gray-800">
          <div className="flex items-center gap-2 mb-1">
            <Bot className="w-4 h-4 text-gray-400" />
            <h2 className="text-gray-100 text-sm font-medium">Test Agent</h2>
          </div>
          <p className="text-gray-400 text-xs">Chat interface</p>
        </div>
        <div className="flex-1 flex items-center justify-center p-8 text-center">
          <div className="text-gray-600">
            <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Deploy an agent to start testing</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full border-l border-gray-800 bg-gray-950 flex flex-col h-full">
      <style>{hideScrollbarStyle}</style>
      <div className="p-3 border-b border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2 mb-1">
          <Bot className="w-4 h-4 text-green-400" />
          <h2 className="text-gray-100 text-sm font-medium">Test Agent</h2>
        </div>
        <p className="text-gray-400 text-xs truncate">{blueprintName || 'Agent'}</p>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 hide-scrollbar" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' } as React.CSSProperties} ref={scrollRef}>
        <div className="space-y-4 w-full overflow-hidden">
          {messages.length === 0 && (
            <div className="text-center text-gray-600 py-8">
              <Bot className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Start a conversation</p>
            </div>
          )}
          
          {messages.map((message) => (
            <div key={message.id} className="space-y-2 w-full overflow-hidden">
              <div className={`flex gap-3 w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                
                <div className={`flex-1 min-w-0 max-w-[85%] ${message.role === 'user' ? 'order-first' : ''}`}>
                  <Card className={`p-3 overflow-hidden ${
                    message.role === 'user' 
                      ? 'bg-blue-950 border-blue-800' 
                      : message.error
                      ? 'bg-red-950 border-red-800'
                      : 'bg-gray-900 border-gray-700'
                  }`}>
                    <div className="text-sm text-gray-200 break-all overflow-wrap-anywhere whitespace-normal">
                      {message.content}
                    </div>
                  </Card>
                  
                  {message.toolCalls && message.toolCalls.length > 0 && (
                    <div className="mt-2 text-xs text-gray-500">
                      <Badge variant="outline" className="text-xs">
                        {message.toolCalls.length} tool call{message.toolCalls.length !== 1 ? 's' : ''} • {message.totalDuration?.toFixed(0)}ms
                      </Badge>
                    </div>
                  )}
                  
                  <div className="mt-1 text-xs text-gray-600">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <Card className="p-3 bg-gray-900 border-gray-700">
                <div className="flex items-center gap-2 text-gray-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Thinking...</span>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>

      <div className="p-3 border-t border-gray-800 flex-shrink-0">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            disabled={isLoading}
            className="flex-1 bg-gray-900 border-gray-700 text-gray-200"
          />
          <Button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            size="icon"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Auth Dialog - shown when user tries to send message without being logged in */}
      <AuthDialog
        open={showAuthDialog}
        onOpenChange={setShowAuthDialog}
        defaultMode="login"
      />
    </div>
  );
}
