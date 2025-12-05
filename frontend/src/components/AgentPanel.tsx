import { AgentConfiguration, TeamMember, NodeInstance, BodyPart, DEFAULT_CONFIGS } from '../types/agent-parts';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { X, Download, Play, Trash2, CheckCircle, Loader2, Save, Users } from 'lucide-react';
import { Badge } from './ui/badge';
import { TeamAgentPanel } from './TeamAgentPanel';
import { useDrop } from 'react-dnd';
import { toast } from 'sonner';

// CSS to hide scrollbar
const hideScrollbarStyle = `
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
`;

interface AgentPanelProps {
  config: AgentConfiguration;
  onRemovePart: (type: 'head' | 'arm' | 'heart' | 'leg' | 'spine', index?: number) => void;
  onAddNode?: (node: NodeInstance, type: 'head' | 'arm' | 'heart' | 'leg' | 'spine') => void;
  onClearAll: () => void;
  onValidate: () => void;
  onExport: () => void;
  onDeploy: () => void;
  onSaveAgent: () => void;
  onImport?: () => void;
  isValidating?: boolean;
  isDeploying?: boolean;
  isSaving?: boolean;
  // Team mode props
  onAddTeamMember?: () => void;
  onRemoveTeamMember?: (memberId: string) => void;
  onUpdateTeamMember?: (memberId: string, updates: Partial<TeamMember>) => void;
  onAddNodeToTeamMember?: (memberId: string, node: NodeInstance, type: 'head' | 'arm' | 'heart') => void;
  onRemoveNodeFromTeamMember?: (memberId: string, type: 'head' | 'arm' | 'heart', index?: number) => void;
  onUpdateNodeInTeamMember?: (memberId: string, type: 'head' | 'arm' | 'heart', updates: Partial<NodeInstance>, index?: number) => void;
}

export function AgentPanel({ 
  config, 
  onRemovePart,
  onAddNode, 
  onClearAll, 
  onValidate, 
  onExport, 
  onDeploy,
  onSaveAgent,
  onImport,
  isValidating = false,
  isDeploying = false,
  isSaving = false,
  // Team mode props
  onAddTeamMember,
  onRemoveTeamMember,
  onUpdateTeamMember,
  onAddNodeToTeamMember,
  onRemoveNodeFromTeamMember,
  onUpdateNodeInTeamMember,
}: AgentPanelProps) {
  const isTeamMode = config.leg?.id === 'team';
  const teamMembers = config.teamMembers || [];
  
  // For team mode, check if at least one team member has a head
  const isTeamComplete = isTeamMode && teamMembers.length > 0 && teamMembers.some(m => m.head) && !!config.leg;
  const isComplete = isTeamMode ? isTeamComplete : (!!config.head && !!config.leg);

  // Drop zone for shared guardrails in team mode
  const [{ isOverSpine }, dropSpine] = useDrop(() => ({
    accept: 'BODY_PART',
    drop: (item: BodyPart) => {
      if (item.type === 'spine' && !config.spine && onAddNode) {
        const nodeInstance: NodeInstance = {
          ...item,
          instanceId: `${item.id}-${Date.now()}`,
          position: { x: 0, y: 0 },
          config: DEFAULT_CONFIGS[item.id] || {},
        };
        onAddNode(nodeInstance, 'spine');
      } else if (item.type === 'spine' && config.spine) {
        toast.error('Guardrails already exist. Remove them first.');
      } else {
        toast.error('Only guardrails can be dropped here');
      }
    },
    collect: (monitor) => ({
      isOverSpine: monitor.isOver() && monitor.getItem()?.type === 'spine',
    }),
  }), [config.spine, onAddNode]);

  // If in team mode, show TeamAgentPanel
  if (isTeamMode && onAddTeamMember && onRemoveTeamMember && onUpdateTeamMember && 
      onAddNodeToTeamMember && onRemoveNodeFromTeamMember && onUpdateNodeInTeamMember) {
    return (
      <div className="w-full border-l border-gray-800 bg-gray-950 flex flex-col h-full">
        <style>{hideScrollbarStyle}</style>
        
        {/* Team Mode Header */}
        <div className="p-4 border-b border-gray-800 flex-shrink-0">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg text-gray-100">Team Mode</h2>
          </div>
          <p className="text-gray-200 text-sm mb-3">Configure multiple agents</p>
          
          {/* Execution Mode Card */}
          <Card className="mt-3 p-3 bg-purple-950/30 border-purple-700">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className="text-xs text-purple-400">Execution Mode</div>
                  <Badge variant="outline" className="text-xs text-purple-400 border-purple-700">Team</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: config.leg?.color }}
                  />
                  <span className="text-sm text-gray-200 truncate">{config.leg?.name}</span>
                </div>
              </div>
              <button
                onClick={() => onRemovePart('leg')}
                className="text-gray-500 hover:text-red-400 transition-colors p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </Card>
          
          {/* Shared Guardrails */}
          <Card 
            ref={dropSpine}
            className={`mt-2 p-3 transition-colors ${
              isOverSpine 
                ? 'bg-yellow-950/50 border-yellow-600' 
                : config.spine 
                  ? 'bg-gray-900 border-gray-700' 
                  : 'bg-gray-950 border-gray-800 border-dashed'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className="text-xs text-gray-500">Shared Guardrails</div>
                  <Badge variant="outline" className="text-xs text-gray-500 border-gray-700">Optional</Badge>
                </div>
                {config.spine ? (
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: config.spine.color }}
                    />
                    <span className="text-sm text-gray-200 truncate">{config.spine.name}</span>
                  </div>
                ) : (
                  <span className="text-sm text-gray-600">{isOverSpine ? 'Release to add guardrails' : 'Drop guardrails here'}</span>
                )}
              </div>
              {config.spine && (
                <button
                  onClick={() => onRemovePart('spine')}
                  className="text-gray-500 hover:text-red-400 transition-colors p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </Card>
        </div>
        
        {/* Team Members Panel */}
        <div className="flex-1 overflow-hidden">
          <TeamAgentPanel
            teamMembers={teamMembers}
            onAddMember={onAddTeamMember}
            onRemoveMember={onRemoveTeamMember}
            onUpdateMember={onUpdateTeamMember}
            onAddNodeToMember={onAddNodeToTeamMember}
            onRemoveNodeFromMember={onRemoveNodeFromTeamMember}
            onUpdateNodeInMember={onUpdateNodeInTeamMember}
          />
        </div>
        
        {/* Action Buttons */}
        <div className="p-4 border-t border-gray-800 space-y-2 flex-shrink-0">
          {isComplete && (
            <div className="mb-2 p-3 bg-purple-950 border border-purple-800 rounded-lg">
              <div className="flex items-center gap-2 text-purple-400 text-sm">
                <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
                Team is ready to deploy!
              </div>
            </div>
          )}
          
          <button 
            className="w-full h-9 px-4 py-2 gap-2 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-purple-950 text-purple-400 border border-purple-700 hover:bg-purple-900 hover:text-purple-300"
            onClick={onAddTeamMember}
          >
            <Users className="w-4 h-4" />
            Add Agent
          </button>
          
          <button 
            className="w-full h-9 px-4 py-2 gap-2 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-800 disabled:opacity-50 disabled:pointer-events-none"
            disabled={!isComplete || isValidating}
            onClick={onValidate}
          >
            {isValidating ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            Validate Team
          </button>
          
          <button 
            className={`w-full h-9 px-4 py-2 gap-2 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none ${isComplete 
              ? 'text-white border-0 shadow-lg shadow-purple-900/30' 
              : 'bg-gray-800 text-gray-400 border border-gray-700'}`}
            style={isComplete ? { background: 'linear-gradient(to right, #7c3aed, #a855f7, #c026d3)' } : undefined}
            disabled={!isComplete || isDeploying}
            onClick={onDeploy}
          >
            {isDeploying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Deploy Team
          </button>
          
          <button 
            className="w-full h-9 px-4 py-2 gap-2 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-800 disabled:opacity-50 disabled:pointer-events-none"
            disabled={!isComplete || isSaving}
            onClick={onSaveAgent}
          >
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Team
          </button>
          
          <button 
            className="w-full h-9 px-4 py-2 gap-2 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-800"
            onClick={onExport}
          >
            <Download className="w-4 h-4" />
            Export Config
          </button>
          
          {onImport && (
            <button 
              className="w-full h-9 px-4 py-2 gap-2 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-800"
              onClick={onImport}
            >
              <Download className="w-4 h-4 rotate-180" />
              Import Config
            </button>
          )}
          
          <button 
            className="w-full h-9 px-4 py-2 gap-2 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-gray-900 text-gray-400 border border-gray-700 hover:bg-gray-800"
            onClick={onClearAll}
          >
            <Trash2 className="w-4 h-4" />
            Clear All
          </button>
        </div>
      </div>
    );
  }

  // Single Agent Mode (original)
  return (
    <div className="w-full border-l border-gray-800 bg-gray-950 flex flex-col h-full">
      <style>{hideScrollbarStyle}</style>
      <div className="p-6 border-b border-gray-800 flex-shrink-0">
        <h2 className="text-gray-100 mb-1">Agent Configuration</h2>
        <p className="text-gray-400 text-sm">Your Frankenstein AI Agent</p>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden hide-scrollbar" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' } as React.CSSProperties}>
        <div className="p-4 space-y-3 pb-8">
          {/* Head - Required */}
          <Card className={`p-3 ${config.head ? 'bg-gray-900 border-gray-700' : 'bg-gray-950 border-red-900 border-dashed'}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className="text-xs text-gray-500">Head (LLM)</div>
                  <Badge variant="outline" className="text-xs text-red-400 border-red-900">Required</Badge>
                </div>
                {config.head ? (
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: config.head.color }}
                    />
                    <span className="text-sm text-gray-200 truncate">{config.head.name}</span>
                  </div>
                ) : (
                  <span className="text-sm text-gray-600">Empty slot</span>
                )}
              </div>
              {config.head && (
                <button
                  onClick={() => onRemovePart('head')}
                  className="text-gray-500 hover:text-red-400 transition-colors p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </Card>

          {/* Tools/Arms - 0-6 */}
          <Card className="p-3 bg-gray-950 border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs text-gray-500">Tools (Arms)</div>
              <Badge variant="outline" className="text-xs text-gray-500 border-gray-700">
                {config.arms.length}/6
              </Badge>
            </div>
            {config.arms.length > 0 ? (
              <div className="space-y-2">
                {config.arms.map((arm, index) => (
                  <div key={arm.instanceId} className="flex items-center gap-2 bg-gray-900 p-2 rounded border border-gray-800">
                    <div
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: arm.color }}
                    />
                    <span className="text-xs text-gray-300 truncate flex-1">{arm.name}</span>
                    <button
                      onClick={() => onRemovePart('arm', index)}
                      className="text-gray-500 hover:text-red-400 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-sm text-gray-600">No tools added</span>
            )}
          </Card>

          {/* Heart - Optional */}
          <Card className={`p-3 ${config.heart ? 'bg-gray-900 border-gray-700' : 'bg-gray-950 border-gray-800 border-dashed'}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className="text-xs text-gray-500">Heart (Memory)</div>
                  <Badge variant="outline" className="text-xs text-gray-500 border-gray-700">Optional</Badge>
                </div>
                {config.heart ? (
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: config.heart.color }}
                    />
                    <span className="text-sm text-gray-200 truncate">{config.heart.name}</span>
                  </div>
                ) : (
                  <span className="text-sm text-gray-600">Empty slot</span>
                )}
              </div>
              {config.heart && (
                <button
                  onClick={() => onRemovePart('heart')}
                  className="text-gray-500 hover:text-red-400 transition-colors p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </Card>

          {/* Leg - Required */}
          <Card className={`p-3 ${config.leg ? 'bg-gray-900 border-gray-700' : 'bg-gray-950 border-red-900 border-dashed'}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className="text-xs text-gray-500">Execution Mode</div>
                  <Badge variant="outline" className="text-xs text-red-400 border-red-900">Required</Badge>
                </div>
                {config.leg ? (
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: config.leg.color }}
                    />
                    <span className="text-sm text-gray-200 truncate">{config.leg.name}</span>
                  </div>
                ) : (
                  <span className="text-sm text-gray-600">Empty slot</span>
                )}
              </div>
              {config.leg && (
                <button
                  onClick={() => onRemovePart('leg')}
                  className="text-gray-500 hover:text-red-400 transition-colors p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </Card>

          {/* Spine - Optional */}
          <Card className={`p-3 ${config.spine ? 'bg-gray-900 border-gray-700' : 'bg-gray-950 border-gray-800 border-dashed'}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className="text-xs text-gray-500">Guardrails (Spine)</div>
                  <Badge variant="outline" className="text-xs text-gray-500 border-gray-700">Optional</Badge>
                </div>
                {config.spine ? (
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: config.spine.color }}
                    />
                    <span className="text-sm text-gray-200 truncate">{config.spine.name}</span>
                  </div>
                ) : (
                  <span className="text-sm text-gray-600">Empty slot</span>
                )}
              </div>
              {config.spine && (
                <button
                  onClick={() => onRemovePart('spine')}
                  className="text-gray-500 hover:text-red-400 transition-colors p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </Card>
        </div>
      </div>

      <div className="p-4 border-t border-gray-800 space-y-2 flex-shrink-0">
        {isComplete && (
          <div className="mb-2 p-3 bg-green-950 border border-green-800 rounded-lg">
            <div className="flex items-center gap-2 text-green-400 text-sm">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              Agent is ready to deploy!
            </div>
          </div>
        )}
        
        <Button 
          className="w-full gap-2 transition-colors"
          variant="outline"
          style={{ backgroundColor: '#111827', color: '#9ca3af', borderColor: '#374151' }}
          disabled={!isComplete || isValidating}
          onClick={onValidate}
        >
          {isValidating ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <CheckCircle className="w-4 h-4" />
          )}
          Validate Blueprint
        </Button>
        
        <Button 
          className="w-full gap-2"
          style={isComplete 
            ? { background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)', color: 'white', border: 'none' } 
            : { backgroundColor: '#1f2937', color: '#9ca3af', borderColor: '#374151' }}
          disabled={!isComplete || isDeploying}
          onClick={onDeploy}
        >
          {isDeploying ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          Deploy Agent
        </Button>
        
        <Button 
          className="w-full gap-2 transition-colors"
          variant="outline"
          style={{ backgroundColor: '#111827', color: '#9ca3af', borderColor: '#374151' }}
          disabled={!isComplete || isSaving}
          onClick={onSaveAgent}
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Agent
        </Button>
        
        <Button 
          className="w-full gap-2 transition-colors"
          variant="outline"
          style={{ backgroundColor: '#111827', color: '#9ca3af', borderColor: '#374151' }}
          onClick={onExport}
        >
          <Download className="w-4 h-4" />
          Export Config
        </Button>
        
        {onImport && (
          <Button 
            className="w-full gap-2 transition-colors"
            variant="outline"
            style={{ backgroundColor: '#111827', color: '#9ca3af', borderColor: '#374151' }}
            onClick={onImport}
          >
            <Download className="w-4 h-4 rotate-180" />
            Import Config
          </Button>
        )}
        
        <Button 
          className="w-full gap-2 transition-colors"
          variant="outline"
          style={{ backgroundColor: '#111827', color: '#9ca3af', borderColor: '#374151' }}
          onClick={onClearAll}
        >
          <Trash2 className="w-4 h-4" />
          Clear All
        </Button>
      </div>
    </div>
  );
}
