import { Button } from '../../ui/button';
import { Card } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { ScrollArea } from '../../ui/scroll-area';
import {
  Activity,
  Clock,
  Zap,
  TrendingUp,
  Download,
} from 'lucide-react';
import { ExecutionLog } from '../../../utils/agentApi';

interface UsageTabProps {
  executionLogs: ExecutionLog[];
  isLoading: boolean;
}

export function UsageTab({ executionLogs, isLoading }: UsageTabProps) {
  // Calculate statistics from logs
  const totalExecutions = executionLogs.length;
  const successfulExecutions = executionLogs.filter(log => log.status === 'success').length;
  const successRate = totalExecutions > 0 ? ((successfulExecutions / totalExecutions) * 100).toFixed(1) : '0.0';
  const avgResponseTime = totalExecutions > 0 
    ? (executionLogs.reduce((sum, log) => sum + log.latency_ms, 0) / totalExecutions / 1000).toFixed(1)
    : '0.0';

  return (
    <div className="max-w-5xl mx-auto">
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 3fr', gap: '24px' }}>
        {/* Left Column - Usage Statistics */}
        <div className="space-y-4">
          {/* Total Executions */}
          <Card className="p-6 bg-gray-900 border-gray-800">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-blue-900/50 flex items-center justify-center">
                <Activity className="w-5 h-5 !text-blue-400" style={{ color: '#60a5fa' }} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Total Executions</p>
                <p className="text-2xl font-bold text-gray-100">{totalExecutions}</p>
              </div>
            </div>
            <div className="flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 !text-green-400" style={{ color: '#4ade80' }} />
              <span className="text-green-400">+12%</span>
              <span className="text-gray-500">vs last week</span>
            </div>
          </Card>

          {/* Success Rate */}
          <Card className="p-6 bg-gray-900 border-gray-800">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-green-900/50 flex items-center justify-center">
                <Zap className="w-5 h-5 !text-green-400" style={{ color: '#4ade80' }} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Success Rate</p>
                <p className="text-2xl font-bold text-gray-100">{successRate}%</p>
              </div>
            </div>
            <div className="flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 !text-green-400" style={{ color: '#4ade80' }} />
              <span className="text-green-400">+2.3%</span>
              <span className="text-gray-500">vs last week</span>
            </div>
          </Card>

          {/* Average Response Time */}
          <Card className="p-6 bg-gray-900 border-gray-800">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-purple-900/50 flex items-center justify-center">
                <Clock className="w-5 h-5 !text-purple-400" style={{ color: '#c084fc' }} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Avg Response Time</p>
                <p className="text-2xl font-bold text-gray-100">{avgResponseTime}s</p>
              </div>
            </div>
            <div className="flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 !text-red-400 rotate-180" style={{ color: '#f87171' }} />
              <span className="text-red-400">+0.1s</span>
              <span className="text-gray-500">vs last week</span>
            </div>
          </Card>
        </div>

        {/* Right Column - Recent Activity */}
        <Card className="bg-gray-900 border-gray-800">
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-100">Recent Activity</h3>
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-2 bg-gray-950 border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100"
          >
            <Download className="w-4 h-4" />
            Export Logs
          </Button>
        </div>
        
        <ScrollArea className="h-[400px] scrollbar-hide">
          <div className="p-4 space-y-3">
            {isLoading ? (
              <div className="text-center py-12 text-gray-500">
                <Activity className="w-10 h-10 mx-auto mb-3 !text-gray-700 animate-pulse" style={{ color: '#374151' }} />
                <p className="text-sm">Loading activity...</p>
              </div>
            ) : executionLogs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Activity className="w-10 h-10 mx-auto mb-3 !text-gray-700" style={{ color: '#374151' }} />
                <p className="text-sm">No activity yet</p>
                <p className="text-xs mt-1 text-gray-600">Your agent executions will appear here</p>
              </div>
            ) : (
              executionLogs.map((log) => (
                <div 
                  key={log.id} 
                  className="p-4 bg-gray-950 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <div 
                        className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                          log.status === 'success' ? 'bg-green-400' : 'bg-red-400'
                        }`} 
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-gray-100">Agent Execution</span>
                          <span className="text-gray-600">•</span>
                          <span className="text-sm text-gray-400">{log.model}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Clock className="w-3 h-3 !text-gray-500" style={{ color: '#6b7280' }} />
                          <span>{new Date(log.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${
                          log.status === 'success' 
                            ? 'border-green-700 text-green-400' 
                            : 'border-red-700 text-red-400'
                        }`}
                      >
                        {log.status}
                      </Badge>
                      <span className="text-sm text-gray-400">{log.total_tokens} credits</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </Card>
      </div>
    </div>
  );
}
