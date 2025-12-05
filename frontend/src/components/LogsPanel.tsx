import { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import { Terminal, Trash2, RefreshCw } from 'lucide-react';
import { getLogs, LogEntry } from '../utils/api';

// CSS to hide scrollbar
const hideScrollbarStyle = `
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
`;

interface LogsPanelProps {
  logs: string[];
  onClearLogs: () => void;
  sessionId?: string;
  onClearRef?: (clearFn: () => void) => void;
}

export function LogsPanel({ logs, onClearLogs, sessionId, onClearRef }: LogsPanelProps) {
  const scrollRef = useRef(null as HTMLDivElement | null);
  const [backendLogs, setBackendLogs] = useState<LogEntry[]>([]);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  // Expose clear function to parent for clearing backend logs
  useEffect(() => {
    if (onClearRef) {
      onClearRef(() => {
        setBackendLogs([]);
      });
    }
  }, [onClearRef]);

  // Fetch backend logs once when session changes
  useEffect(() => {
    if (sessionId) {
      fetchBackendLogs();
    }
  }, [sessionId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, backendLogs]);

  const fetchBackendLogs = async () => {
    if (!sessionId) return;

    setIsLoadingLogs(true);
    try {
      const response = await getLogs(sessionId);
      setBackendLogs(response.logs);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  // Format backend log entry as string
  const formatLogEntry = (entry: LogEntry): string => {
    const timestamp = new Date(entry.timestamp).toLocaleTimeString();
    
    // If entry has a message field (new format), use it directly
    if ('message' in entry && entry.message) {
      return `[${timestamp}] ${entry.message}`;
    }
    
    // Otherwise, format the old way for tool calls
    let logStr = `[${timestamp}] ${entry.event_type}`;
    
    if (entry.tool_name) {
      logStr += ` - ${entry.tool_name}`;
    }
    
    if (entry.duration_ms !== undefined) {
      logStr += ` (${entry.duration_ms}ms)`;
    }
    
    if (entry.success !== undefined) {
      logStr += entry.success ? ' ✓' : ' ✗';
    }
    
    if (entry.error) {
      logStr += ` ERROR: ${entry.error}`;
    }
    
    return logStr;
  };

  // Combine local and backend logs
  const allLogs = [
    ...logs,
    ...backendLogs.map(formatLogEntry)
  ];

  return (
    <div className="w-full border-l border-gray-800 bg-gray-950 flex flex-col h-full overflow-hidden">
      <style>{hideScrollbarStyle}</style>
      <div className="p-3 border-b border-gray-800 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-gray-400" />
          <h2 className="text-gray-100 text-sm font-medium">Logs</h2>
          <span className="text-xs text-gray-500">({allLogs.length})</span>
        </div>
        <div className="flex items-center gap-1">
          {sessionId && (
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchBackendLogs}
              disabled={isLoadingLogs}
              className="text-gray-500 hover:text-gray-300 h-7 w-7 p-0"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingLogs ? 'animate-spin' : ''}`} />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearLogs}
            className="text-gray-500 hover:text-gray-300 h-7 w-7 p-0"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 hide-scrollbar" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' } as React.CSSProperties} ref={scrollRef}>
        {allLogs.length === 0 ? (
          <div className="text-center text-gray-600 py-6">
            <Terminal className="w-6 h-6 mx-auto mb-2 opacity-50" />
            <p className="text-xs">No logs yet</p>
            <p className="text-xs mt-1 text-gray-700">Activity will appear here</p>
          </div>
        ) : (
          <div className="space-y-1 pb-4 w-full">
            {allLogs.map((log, index) => {
              const isError = log.includes('ERROR') || log.includes('✗');
              const isWarning = log.includes('WARNING') || log.includes('⚠');
              const isSuccess = log.includes('✓') || log.includes('✅');
              const isToolCall = log.includes('Tool calls:') || log.includes('tool_call') || log.startsWith('  ');
              const isStep = log.includes('STEP 1') || log.includes('STEP 2') || log.includes('STEP 3') || 
                            log.includes('STEP 4') || log.includes('STEP 5') || log.includes('STEP 6');
              const isExecution = log.includes('🚀') || log.includes('🔑') || log.includes('⚙️') || 
                                 log.includes('💬') || log.includes('🤖');
              
              return (
                <div
                  key={index}
                  className={`px-2 py-1.5 rounded text-xs overflow-hidden ${
                    isError
                      ? 'bg-red-950/50 border-l-2 border-red-500 text-red-300'
                      : isWarning
                      ? 'bg-yellow-950/50 border-l-2 border-yellow-500 text-yellow-300'
                      : isSuccess
                      ? 'bg-green-950/50 border-l-2 border-green-500 text-green-300'
                      : isStep || isExecution
                      ? 'bg-purple-950/50 border-l-2 border-purple-500 text-purple-300 font-medium'
                      : isToolCall
                      ? 'bg-blue-950/50 border-l-2 border-blue-500 text-blue-300'
                      : 'bg-gray-900/50 border-l-2 border-gray-700 text-gray-400'
                  }`}
                >
                  <div className="font-mono text-[10px] leading-snug break-all overflow-wrap-anywhere">
                    {log}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
