import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getUserBlueprints, BlueprintListItem } from '../../utils/blueprintApi';
import { createSession } from '../../utils/sessionApi';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Bot, Plus } from 'lucide-react';
import { toast } from 'sonner';

interface AgentSelectorProps {
  selectedBlueprintId?: string;
  onAgentChange?: (blueprintId: string, sessionId: string) => void;
  onCreateNew?: () => void;
}

export function AgentSelector({ selectedBlueprintId, onAgentChange, onCreateNew }: AgentSelectorProps) {
  const { token, isAuthenticated } = useAuth();
  const [blueprints, setBlueprints] = useState<BlueprintListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  const fetchBlueprints = async () => {
    if (!token) return;

    setIsLoading(true);
    try {
      const data = await getUserBlueprints(token);
      setBlueprints(data);
    } catch (error) {
      console.error('Failed to fetch blueprints:', error);
      toast.error('Failed to load agents');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchBlueprints();
    }
  }, [token, isAuthenticated]);

  const handleAgentChange = async (blueprintId: string) => {
    if (blueprintId === 'create-new') {
      onCreateNew?.();
      return;
    }

    if (!token) {
      toast.error('Please log in to switch agents');
      return;
    }

    setIsCreatingSession(true);
    try {
      const session = await createSession(token, blueprintId);
      onAgentChange?.(blueprintId, session.id);
      toast.success('Switched to new agent');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to switch agent';
      toast.error(message);
    } finally {
      setIsCreatingSession(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex items-center gap-2">
      <Bot className="w-4 h-4 text-gray-400" />
      <Select
        value={selectedBlueprintId || ''}
        onValueChange={handleAgentChange}
        disabled={isLoading || isCreatingSession}
      >
        <SelectTrigger className="w-[200px] bg-gray-800 border-gray-700">
          <SelectValue placeholder="Select an agent" />
        </SelectTrigger>
        <SelectContent className="bg-gray-800 border-gray-700">
          {blueprints.length === 0 ? (
            <SelectItem value="create-new" className="text-green-400">
              <div className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Create your first agent
              </div>
            </SelectItem>
          ) : (
            <>
              {blueprints.map((blueprint) => (
                <SelectItem key={blueprint.id} value={blueprint.id}>
                  <div className="flex flex-col">
                    <span>{blueprint.name}</span>
                    {blueprint.updated_at && (
                      <span className="text-xs text-gray-500">
                        Updated {new Date(blueprint.updated_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))}
              <SelectItem value="create-new" className="text-green-400">
                <div className="flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Create new agent
                </div>
              </SelectItem>
            </>
          )}
        </SelectContent>
      </Select>
    </div>
  );
}
