import { NodeInstance } from '../types/agent-parts';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Settings, X } from 'lucide-react';
import { Badge } from './ui/badge';

interface CanvasNodeProps {
  node: NodeInstance;
  onEdit: () => void;
  onRemove: () => void;
  isConnected?: boolean;
  compact?: boolean;
}

export function CanvasNode({ node, onEdit, onRemove, isConnected = true, compact = false }: CanvasNodeProps) {
  if (compact) {
    return (
      <div
        className="flex items-center justify-between gap-2 p-2 rounded bg-gray-800/80 border border-gray-700"
        style={{ borderLeftColor: node.color, borderLeftWidth: 3 }}
      >
        <div className="flex-1 min-w-0">
          <span className="text-xs text-gray-200 truncate block">{node.name}</span>
        </div>
        <div className="flex gap-1 flex-shrink-0">
          <Button
            size="icon"
            variant="ghost"
            className="h-5 w-5"
            onClick={onEdit}
          >
            <Settings className="w-2.5 h-2.5 text-gray-400" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-5 w-5 text-red-400 hover:text-red-300"
            onClick={onRemove}
          >
            <X className="w-2.5 h-2.5" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <Card
      className="bg-gray-900/95 backdrop-blur-sm border-gray-700 p-3 w-[200px] shadow-xl hover:shadow-2xl transition-all"
      style={{
        borderColor: isConnected ? node.color : '#374151',
        boxShadow: isConnected ? `0 0 20px ${node.color}40` : undefined,
      }}
    >
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <Badge
              className="text-xs mb-1"
              style={{ backgroundColor: node.color, borderColor: node.color }}
            >
              {node.category}
            </Badge>
            <h3 className="text-xs text-gray-200 truncate leading-tight">
              {node.name}
            </h3>
          </div>
          <div className="flex gap-1 flex-shrink-0">
            <Button
              size="icon"
              variant="ghost"
              className="h-6 w-6"
              onClick={onEdit}
            >
              <Settings className="w-3 h-3 text-white" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-6 w-6 text-red-400 hover:text-red-300"
              onClick={onRemove}
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
        </div>

        {/* Connection indicator */}
        <div className="flex items-center gap-2">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-600'
            }`}
          />
          <span className="text-xs text-gray-500">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </Card>
  );
}
