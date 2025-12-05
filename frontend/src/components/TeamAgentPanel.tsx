import { useState, useRef, useEffect } from 'react';
import { TeamMember, NodeInstance, BodyPart, DEFAULT_CONFIGS } from '../types/agent-parts';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { useDrop } from 'react-dnd';
import { CanvasNode } from './CanvasNode';
import { NodeConfigDialog } from './NodeConfigDialog';
import { 
  Users, 
  Trash2, 
  User, 
  Edit2,
  Brain,
  Wrench,
  Heart,
  CheckCircle2
} from 'lucide-react';
import { toast } from 'sonner@2.0.3';

interface TeamAgentPanelProps {
  teamMembers: TeamMember[];
  onAddMember: () => void;
  onRemoveMember: (memberId: string) => void;
  onUpdateMember: (memberId: string, updates: Partial<TeamMember>) => void;
  onAddNodeToMember: (memberId: string, node: NodeInstance, type: 'head' | 'arm' | 'heart') => void;
  onRemoveNodeFromMember: (memberId: string, type: 'head' | 'arm' | 'heart', index?: number) => void;
  onUpdateNodeInMember: (memberId: string, type: 'head' | 'arm' | 'heart', updates: Partial<NodeInstance>, index?: number) => void;
}

export function TeamAgentPanel({
  teamMembers,
  onAddMember,
  onRemoveMember,
  onUpdateMember,
  onAddNodeToMember,
  onRemoveNodeFromMember,
  onUpdateNodeInMember,
}: TeamAgentPanelProps) {
  const [editingMemberId, setEditingMemberId] = useState<string | null>(null);
  const [editingNode, setEditingNode] = useState<{ 
    memberId: string; 
    node: NodeInstance; 
    type: 'head' | 'arm' | 'heart'; 
    index?: number 
  } | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const prevMemberCountRef = useRef(teamMembers.length);

  // Auto-scroll to bottom when new member is added
  useEffect(() => {
    if (teamMembers.length > prevMemberCountRef.current && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
    prevMemberCountRef.current = teamMembers.length;
  }, [teamMembers.length]);

  const handleEditNode = (memberId: string, type: 'head' | 'arm' | 'heart', index?: number) => {
    const member = teamMembers.find(m => m.id === memberId);
    if (!member) return;

    let node: NodeInstance | undefined;
    if (type === 'arm' && index !== undefined) {
      node = member.arms[index];
    } else if (type === 'head') {
      node = member.head;
    } else if (type === 'heart') {
      node = member.heart;
    }

    if (node) {
      setEditingNode({ memberId, node, type, index });
    }
  };

  const handleSaveConfig = (newConfig: Record<string, unknown>) => {
    if (editingNode) {
      onUpdateNodeInMember(
        editingNode.memberId,
        editingNode.type,
        { config: newConfig },
        editingNode.index
      );
    }
  };

  return (
    <>
      <style>{`
        .hide-scrollbar::-webkit-scrollbar { display: none; }
        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
      <div className="h-full flex flex-col bg-gray-950">
        {/* Team Members Grid */}
        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto hide-scrollbar">
          <div className="p-4 grid grid-cols-1 gap-4">
            {teamMembers.length === 0 ? (
              <Card className="p-8 bg-gray-900/50 border-gray-800 border-dashed">
                <div className="text-center">
                  <Users className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400">No agents yet</p>
                  <p className="text-xs text-gray-500 mt-1">Click "Add Agent" below</p>
                </div>
              </Card>
            ) : (
              teamMembers.map((member, idx) => (
                <TeamMemberCard
                  key={member.id}
                  member={member}
                  index={idx}
                  isEditing={editingMemberId === member.id}
                  onStartEdit={() => setEditingMemberId(member.id)}
                  onFinishEdit={() => setEditingMemberId(null)}
                  onUpdate={(updates) => onUpdateMember(member.id, updates)}
                  onRemove={() => onRemoveMember(member.id)}
                  onAddNode={(node, type) => onAddNodeToMember(member.id, node, type)}
                  onRemoveNode={(type, index) => onRemoveNodeFromMember(member.id, type, index)}
                  onEditNode={(type, index) => handleEditNode(member.id, type, index)}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Node Config Dialog */}
      {editingNode && (
        <NodeConfigDialog
          node={editingNode.node}
          open={!!editingNode}
          onOpenChange={(open) => !open && setEditingNode(null)}
          onSave={handleSaveConfig}
        />
      )}
    </>
  );
}

interface TeamMemberCardProps {
  member: TeamMember;
  index: number;
  isEditing: boolean;
  onStartEdit: () => void;
  onFinishEdit: () => void;
  onUpdate: (updates: Partial<TeamMember>) => void;
  onRemove: () => void;
  onAddNode: (node: NodeInstance, type: 'head' | 'arm' | 'heart') => void;
  onRemoveNode: (type: 'head' | 'arm' | 'heart', index?: number) => void;
  onEditNode: (type: 'head' | 'arm' | 'heart', index?: number) => void;
}


function TeamMemberCard({
  member,
  index,
  isEditing,
  onStartEdit,
  onFinishEdit,
  onUpdate,
  onRemove,
  onAddNode,
  onRemoveNode,
  onEditNode,
}: TeamMemberCardProps) {
  const [tempName, setTempName] = useState(member.name);
  const [tempRole, setTempRole] = useState(member.role);

  const [{ isOver: isOverHead }, dropHead] = useDrop(() => ({
    accept: 'BODY_PART',
    drop: (item: BodyPart) => {
      if (item.type === 'head' && !member.head) {
        onAddNode({
          ...item,
          instanceId: `${item.id}-${Date.now()}`,
          position: { x: 0, y: 0 },
          config: DEFAULT_CONFIGS[item.id] || {},
        }, 'head');
      } else if (item.type === 'head') {
        toast.error('This agent already has a head');
      } else {
        toast.error('Can only drop heads in this zone');
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver() && monitor.getItem()?.type === 'head',
    }),
  }), [member.head, onAddNode]);

  const [{ isOver: isOverArm }, dropArm] = useDrop(() => ({
    accept: 'BODY_PART',
    drop: (item: BodyPart) => {
      if (item.type === 'arm' && member.arms.length < 6) {
        onAddNode({
          ...item,
          instanceId: `${item.id}-${Date.now()}`,
          position: { x: 0, y: 0 },
          config: DEFAULT_CONFIGS[item.id] || {},
        }, 'arm');
      } else if (item.type === 'arm') {
        toast.error('Maximum 6 tools per agent');
      } else {
        toast.error('Can only drop tools in this zone');
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver() && monitor.getItem()?.type === 'arm',
    }),
  }), [member.arms.length, onAddNode]);

  const [{ isOver: isOverHeart }, dropHeart] = useDrop(() => ({
    accept: 'BODY_PART',
    drop: (item: BodyPart) => {
      if (item.type === 'heart' && !member.heart) {
        onAddNode({
          ...item,
          instanceId: `${item.id}-${Date.now()}`,
          position: { x: 0, y: 0 },
          config: DEFAULT_CONFIGS[item.id] || {},
        }, 'heart');
      } else if (item.type === 'heart') {
        toast.error('This agent already has memory');
      } else {
        toast.error('Can only drop memory in this zone');
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver() && monitor.getItem()?.type === 'heart',
    }),
  }), [member.heart, onAddNode]);

  const handleSave = () => {
    if (!tempName.trim()) {
      toast.error('Agent name is required');
      return;
    }
    onUpdate({ name: tempName, role: tempRole });
    onFinishEdit();
  };

  const isComplete = !!member.head;

  return (
    <Card className={`p-4 bg-gray-900 border-gray-800 relative ${isComplete ? 'border-green-800/30' : ''}`}>
      {/* Completion indicator */}
      {/* Header */}
      <div className="mb-3">
        {isEditing ? (
          <div className="space-y-2">
            <div>
              <Label className="text-xs text-gray-400">Agent Name</Label>
              <Input
                value={tempName}
                onChange={(e) => setTempName(e.target.value)}
                className="bg-gray-950 border-gray-700 text-gray-100"
                placeholder="e.g., Research Specialist"
              />
            </div>
            <div>
              <Label className="text-xs text-gray-400">Role</Label>
              <Input
                value={tempRole}
                onChange={(e) => setTempRole(e.target.value)}
                className="bg-gray-950 border-gray-700 text-gray-100"
                placeholder="e.g., Finds and analyzes information"
              />
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={handleSave}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                Save
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setTempName(member.name);
                  setTempRole(member.role);
                  onFinishEdit();
                }}
                className="bg-gray-950 border-gray-700 text-gray-300"
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <User className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm text-gray-100">{member.name}</h3>
                {isComplete && (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                )}
              </div>
              <p className="text-xs text-gray-500">{member.role}</p>
            </div>
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="ghost"
                onClick={onStartEdit}
                className="h-7 w-7 p-0 text-gray-400 hover:text-gray-100"
              >
                <Edit2 className="w-3 h-3" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={onRemove}
                className="h-7 w-7 p-0 text-gray-400 hover:text-red-400"
              >
                <Trash2 className="w-3 h-3" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Body Parts Drop Zones */}
      <div className="space-y-2">
        {/* Head Zone */}
        <div
          ref={dropHead}
          className={`p-2 rounded-lg border-2 border-dashed transition-colors ${
            isOverHead
              ? 'border-green-500 bg-green-500/10'
              : member.head
              ? 'border-gray-700 bg-gray-800/50'
              : 'border-gray-700 bg-gray-900/50'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <Brain className="w-3 h-3 text-gray-400" />
            <span className="text-xs text-gray-400">LLM</span>
            {!member.head && <span className="text-xs text-red-400">*Required</span>}
          </div>
          {member.head ? (
            <CanvasNode
              node={member.head}
              onRemove={() => onRemoveNode('head')}
              onEdit={() => onEditNode('head')}
              compact
            />
          ) : (
            <p className="text-xs text-gray-500 text-center py-1">Drop head here</p>
          )}
        </div>

        {/* Tools Zone */}
        <div
          ref={dropArm}
          className={`p-2 rounded-lg border-2 border-dashed transition-colors ${
            isOverArm
              ? 'border-green-500 bg-green-500/10'
              : member.arms.length > 0
              ? 'border-gray-700 bg-gray-800/50'
              : 'border-gray-700 bg-gray-900/50'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <Wrench className="w-3 h-3 text-gray-400" />
            <span className="text-xs text-gray-400">Tools ({member.arms.length}/6)</span>
          </div>
          {member.arms.length > 0 ? (
            <div className="space-y-1">
              {member.arms.map((arm, idx) => (
                <CanvasNode
                  key={arm.instanceId}
                  node={arm}
                  onRemove={() => onRemoveNode('arm', idx)}
                  onEdit={() => onEditNode('arm', idx)}
                  compact
                />
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500 text-center py-1">Drop tools here</p>
          )}
        </div>

        {/* Memory Zone */}
        <div
          ref={dropHeart}
          className={`p-2 rounded-lg border-2 border-dashed transition-colors ${
            isOverHeart
              ? 'border-green-500 bg-green-500/10'
              : member.heart
              ? 'border-gray-700 bg-gray-800/50'
              : 'border-gray-700 bg-gray-900/50'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <Heart className="w-3 h-3 text-gray-400" />
            <span className="text-xs text-gray-400">Memory</span>
          </div>
          {member.heart ? (
            <CanvasNode
              node={member.heart}
              onRemove={() => onRemoveNode('heart')}
              onEdit={() => onEditNode('heart')}
              compact
            />
          ) : (
            <p className="text-xs text-gray-500 text-center py-1">Drop memory here (optional)</p>
          )}
        </div>
      </div>
    </Card>
  );
}
