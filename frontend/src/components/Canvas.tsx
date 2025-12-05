import { useDrop } from 'react-dnd';
import { AgentConfiguration, BodyPart, NodeInstance, DEFAULT_CONFIGS } from '../types/agent-parts';
import { FrankensteinMonster } from './FrankensteinMonster';
import { CanvasNode } from './CanvasNode';
import React, { useState, useRef } from 'react';
import { NodeConfigDialog } from './NodeConfigDialog';
import { Users, ArrowRight, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';

interface CanvasProps {
  config: AgentConfiguration;
  onAddNode: (node: NodeInstance, type: 'head' | 'arm' | 'heart' | 'leg' | 'spine') => void;
  onRemoveNode: (type: 'head' | 'arm' | 'heart' | 'leg' | 'spine', index?: number) => void;
  onUpdateNode: (type: 'head' | 'arm' | 'heart' | 'leg' | 'spine', updates: Partial<NodeInstance>, index?: number) => void;
}

export function Canvas({ config, onAddNode, onRemoveNode, onUpdateNode }: CanvasProps) {
  const [editingNode, setEditingNode] = useState<{ node: NodeInstance; type: 'head' | 'arm' | 'heart' | 'leg' | 'spine'; index?: number } | null>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const isPanning = useRef(false);
  const lastPanPosition = useRef({ x: 0, y: 0 });
  
  // Team mode detection
  const isTeamMode = config.leg?.id === 'team';
  const teamMembers = config.teamMembers || [];
  
  // Calculate zoom based on team member count (decrease by 10% for each member)
  const calculateZoom = () => {
    if (!isTeamMode || teamMembers.length === 0) return 1;
    // First member: 90%, Second: 80%, Third: 70%, etc. Minimum 30%
    return Math.max(0.3, 1 - (teamMembers.length * 0.1));
  };
  
  const [zoom, setZoom] = useState(1);
  
  // Update zoom when team members change
  React.useEffect(() => {
    if (isTeamMode) {
      setZoom(calculateZoom());
    } else {
      setZoom(1);
    }
  }, [teamMembers.length, isTeamMode]);

  const [{ isOver, draggedItem }, drop] = useDrop(() => ({
    accept: 'BODY_PART',
    drop: (item: BodyPart) => {
      handleDrop(item);
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      draggedItem: monitor.getItem() as BodyPart | null,
    }),
  }));

  const handleDrop = (part: BodyPart) => {
    const instanceId = `${part.id}-${Date.now()}`;
    const nodeInstance: NodeInstance = {
      ...part,
      instanceId,
      position: { x: 0, y: 0 },
      config: DEFAULT_CONFIGS[part.id] || {},
    };

    onAddNode(nodeInstance, part.type);
  };

  const handleEditNode = (type: 'head' | 'arm' | 'heart' | 'leg' | 'spine', index?: number) => {
    let node: NodeInstance | undefined;
    
    if (type === 'arm' && index !== undefined) {
      node = config.arms[index];
    } else if (type === 'head') {
      node = config.head;
    } else if (type === 'heart') {
      node = config.heart;
    } else if (type === 'leg') {
      node = config.leg;
    } else if (type === 'spine') {
      node = config.spine;
    }
    
    if (node) {
      setEditingNode({ node, type, index });
    }
  };

  const handleSaveConfig = (newConfig: Record<string, unknown>) => {
    if (editingNode) {
      onUpdateNode(editingNode.type, { config: newConfig }, editingNode.index);
    }
  };

  const canAcceptDrop = (item: BodyPart | null): boolean => {
    if (!item) return false;
    
    // In team mode, only allow leg and spine drops on canvas
    if (isTeamMode) {
      return item.type === 'leg' || item.type === 'spine';
    }
    
    switch (item.type) {
      case 'head':
        return !config.head;
      case 'arm':
        return config.arms.length < 6;
      case 'heart':
        return !config.heart;
      case 'leg':
        return !config.leg;
      case 'spine':
        return !config.spine;
      default:
        return false;
    }
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.1, 2));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.1, 0.3));
  };

  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
      isPanning.current = true;
      lastPanPosition.current = { x: e.clientX, y: e.clientY };
      e.preventDefault();
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning.current) {
      const deltaX = e.clientX - lastPanPosition.current.x;
      const deltaY = e.clientY - lastPanPosition.current.y;
      setPan(prev => ({ x: prev.x + deltaX, y: prev.y + deltaY }));
      lastPanPosition.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseUp = () => {
    isPanning.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -0.05 : 0.05;
      setZoom(prev => Math.max(0.3, Math.min(2, prev + delta)));
    }
  };

  const isComplete = !!config.head && !!config.leg;

  // Calculate grid layout for team members
  const getTeamMemberPosition = (index: number, total: number) => {
    const cols = Math.ceil(Math.sqrt(total));
    const row = Math.floor(index / cols);
    const col = index % cols;
    const spacing = 600;
    const offsetX = -(cols - 1) * spacing / 2;
    const offsetY = -(Math.ceil(total / cols) - 1) * spacing / 2;
    
    return {
      x: offsetX + col * spacing,
      y: offsetY + row * spacing,
    };
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div
        id="canvas"
        ref={drop}
        className={`flex-1 relative overflow-hidden ${
          isOver ? 'bg-gradient-to-br from-gray-800 via-gray-900 to-black' : 'bg-gradient-to-br from-gray-900 via-gray-950 to-black'
        } transition-colors ${isPanning.current ? 'cursor-grabbing' : 'cursor-grab'}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        {/* Zoom Controls */}
        <div className="absolute top-4 left-4 flex flex-col gap-2 z-50">
          <Button
            size="sm"
            onClick={handleZoomIn}
            className="bg-gray-900 border border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100 w-10 h-10 p-0"
            title="Zoom In (Ctrl+Scroll)"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            size="sm"
            onClick={handleZoomOut}
            className="bg-gray-900 border border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100 w-10 h-10 p-0"
            title="Zoom Out (Ctrl+Scroll)"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <Button
            size="sm"
            onClick={handleResetZoom}
            className="bg-gray-900 border border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100 w-10 h-10 p-0"
            title="Reset View"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
          <div className="bg-gray-900 border border-gray-700 text-gray-300 text-xs px-2 py-1 rounded text-center">
            {Math.round(zoom * 100)}%
          </div>
        </div>

        {/* Grid background */}
        <div className="absolute inset-0 opacity-5">
          <div
            className="w-full h-full"
            style={{
              backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)',
              backgroundSize: '30px 30px',
            }}
          />
        </div>

        {/* Drop zone hint when dragging */}
        {isOver && draggedItem && canAcceptDrop(draggedItem) && !isTeamMode && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none z-50">
            <div className="w-[300px] h-[100px] border-2 border-dashed border-green-500 rounded-lg bg-green-950 bg-opacity-20 animate-pulse flex items-center justify-center">
              <span className="text-green-400">Drop to add {draggedItem.category}</span>
            </div>
          </div>
        )}

        {/* Zoomable and Pannable Container */}
        <div
          className="absolute inset-0"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isPanning.current ? 'none' : 'transform 0.1s ease-out',
          }}
        >
          {isTeamMode ? (
            /* Team Mode: Multiple Frankenstein Monsters */
            <>
              {teamMembers.length === 0 ? (
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-40 pointer-events-none">
                  <Card className="p-12 bg-gradient-to-br from-purple-950/90 to-pink-950/90 border-purple-700 backdrop-blur-sm shadow-2xl max-w-2xl">
                    <div className="text-center space-y-6">
                      <div className="w-24 h-24 bg-purple-900/50 rounded-full flex items-center justify-center mx-auto">
                        <Users className="w-12 h-12 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="text-3xl font-bold text-gray-100 mb-3">Team Mode Activated</h3>
                        <p className="text-base text-gray-300 mb-6">
                          Click "Add Team Member" in the right panel to create agents
                        </p>
                      </div>
                      <div className="flex items-center justify-center gap-3 text-purple-400">
                        <span className="text-base font-medium">Configure team in right panel</span>
                        <ArrowRight className="w-5 h-5 animate-pulse" />
                      </div>
                      <Badge variant="outline" className="border-purple-600 text-purple-400 bg-purple-950/30 text-sm px-4 py-2">
                        Each team member is a separate agent
                      </Badge>
                    </div>
                  </Card>
                </div>
              ) : (
                teamMembers.map((member, index) => {
                  const position = getTeamMemberPosition(index, teamMembers.length);
                  const memberConfig: AgentConfiguration = {
                    head: member.head,
                    arms: member.arms,
                    heart: member.heart,
                    leg: config.leg,
                    spine: config.spine,
                  };
                  const isLeader = index === 0;

                  return (
                    <div
                      key={member.id}
                      className="absolute"
                      style={{
                        left: '50%',
                        top: '50%',
                        transform: `translate(calc(-50% + ${position.x}px), calc(-50% + ${position.y}px))`,
                      }}
                    >
                      {/* Team Member Card */}
                      <div className="relative">
                        {/* Spotlight/Glow effect */}
                        <div className="absolute inset-0 bg-gradient-radial from-purple-950/30 via-transparent to-transparent blur-3xl scale-150 pointer-events-none" />
                        
                        {/* Monster container with border */}
                        <div className="relative p-4 border-2 border-dashed border-purple-700/50 rounded-lg bg-purple-950/10">
                          {/* Agent Name and Role - Top Center */}
                          <div className="absolute -top-14 left-1/2 transform -translate-x-1/2 z-50 text-center">
                            <div className="bg-gray-900/95 border border-purple-700 rounded-lg px-4 py-2 shadow-xl">
                              <div className="flex items-center gap-1 justify-center mb-1">
                                <h3 className="text-sm text-purple-300 font-medium">
                                  {member.name}
                                </h3>
                              </div>
                              <p className="text-xs text-gray-400">{member.role}</p>
                            </div>
                          </div>
                          
                          <FrankensteinMonster config={memberConfig} />
                          
                          {/* Completion status */}
                          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
                            <Badge 
                              variant="outline" 
                              className={`${
                                member.head 
                                  ? 'border-green-600 text-green-400 bg-green-950/30' 
                                  : 'border-red-600 text-red-400 bg-red-950/30'
                              }`}
                            >
                              {member.head ? '✓ Ready' : '⚠ Needs Head'}
                            </Badge>
                          </div>
                        </div>

                        {/* Team Member Info Panel - Top Left */}
                        <div className="absolute -top-2 -left-2 w-64">
                          <Card className="p-3 bg-gray-900/95 border-purple-800 shadow-xl">
                            <div className="text-xs text-gray-400 space-y-1">
                              <div className="flex items-center justify-between">
                                <span>Head (LLM):</span>
                                <span className={member.head ? 'text-green-400' : 'text-red-400'}>
                                  {member.head ? '✓' : '✗ Required'}
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span>Tools:</span>
                                <span className="text-purple-400">{member.arms.length}/6</span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span>Memory:</span>
                                <span className="text-gray-400">{member.heart ? '✓' : '○'} Optional</span>
                              </div>
                            </div>
                          </Card>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}

              {/* Shared Spine/Guardrails for Team */}
              {config.spine && teamMembers.length > 0 && (
                <div className="absolute top-[10%] left-1/2 transform -translate-x-1/2 z-30">
                  <Card className="p-3 bg-gray-900/95 border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className="text-xs bg-gray-700">Shared Guardrails</Badge>
                    </div>
                    <CanvasNode
                      node={config.spine}
                      onEdit={() => handleEditNode('spine')}
                      onRemove={() => onRemoveNode('spine')}
                      isConnected={true}
                    />
                  </Card>
                </div>
              )}
            </>
          ) : (
            /* Single Agent Mode: Original Frankenstein */
            <>
              {/* Central Frankenstein Monster with spotlight effect */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
                {/* Spotlight/Glow effect */}
                <div className="absolute inset-0 bg-gradient-radial from-green-950/30 via-transparent to-transparent blur-3xl scale-150 pointer-events-none" />
                
                {/* Monster container */}
                <div className="relative">
                  <FrankensteinMonster config={config} />
                </div>
              </div>

              {/* Head Node */}
              {config.head && (
                <div className="absolute top-[15%] left-1/2 transform -translate-x-1/2 z-20">
                  <CanvasNode
                    node={config.head}
                    onEdit={() => handleEditNode('head')}
                    onRemove={() => onRemoveNode('head')}
                    isConnected={true}
                  />
                </div>
              )}

              {/* Tools/Arms - displayed as a horizontal collection */}
              {config.arms.length > 0 && (
                <div className="absolute top-[45%] left-1/2 transform -translate-x-1/2 z-20 flex gap-3">
                  {config.arms.map((arm, index) => (
                    <CanvasNode
                      key={arm.instanceId}
                      node={arm}
                      onEdit={() => handleEditNode('arm', index)}
                      onRemove={() => onRemoveNode('arm', index)}
                      isConnected={true}
                    />
                  ))}
                </div>
              )}

              {/* Heart Node */}
              {config.heart && (
                <div className="absolute top-[35%] left-[20%] z-20">
                  <CanvasNode
                    node={config.heart}
                    onEdit={() => handleEditNode('heart')}
                    onRemove={() => onRemoveNode('heart')}
                    isConnected={true}
                  />
                </div>
              )}

              {/* Leg Node - Execution Mode */}
              {config.leg && (
                <div className="absolute bottom-[15%] left-1/2 transform -translate-x-1/2 z-20">
                  <CanvasNode
                    node={config.leg}
                    onEdit={() => handleEditNode('leg')}
                    onRemove={() => onRemoveNode('leg')}
                    isConnected={true}
                  />
                </div>
              )}

              {/* Spine Node - Guardrails */}
              {config.spine && (
                <div className="absolute top-[35%] right-[20%] z-20">
                  <CanvasNode
                    node={config.spine}
                    onEdit={() => handleEditNode('spine')}
                    onRemove={() => onRemoveNode('spine')}
                    isConnected={true}
                  />
                </div>
              )}
            </>
          )}

          {/* Instructions */}
          {!config.head && !config.leg && config.arms.length === 0 && !isTeamMode && (
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none z-0">
              <div className="text-gray-600 text-lg mb-2">Drag body parts from the left sidebar</div>
              <div className="text-gray-700 text-sm">Start with a Head (LLM) and Execution Mode</div>
            </div>
          )}
        </div>

        {/* Agent status indicator - Fixed position */}
        {!isTeamMode && (
          <div className="absolute top-8 right-8 p-4 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-30">
            <div className="flex items-center gap-2 mb-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  isComplete ? 'bg-green-500 animate-pulse' : 'bg-gray-600'
                }`}
              />
              <span className="text-sm text-gray-300">Agent Status</span>
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              <div className="flex items-center justify-between">
                <span>Head (LLM):</span>
                <span className={config.head ? 'text-green-400' : 'text-red-400'}>
                  {config.head ? '✓ Required' : '✗ Required'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Tools:</span>
                <span className="text-gray-400">{config.arms.length}/6</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Memory:</span>
                <span className="text-gray-400">{config.heart ? '✓' : '○'} Optional</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Execution:</span>
                <span className={config.leg ? 'text-green-400' : 'text-red-400'}>
                  {config.leg ? '✓ Required' : '✗ Required'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Guardrails:</span>
                <span className="text-gray-400">{config.spine ? '✓' : '○'} Optional</span>
              </div>
            </div>
          </div>
        )}

        {/* Team Status Indicator */}
        {isTeamMode && teamMembers.length > 0 && (
          <div className="absolute top-8 right-8 p-4 bg-gradient-to-br from-purple-950 to-pink-950 border border-purple-700 rounded-lg shadow-xl z-30">
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-gray-300">Team Status</span>
            </div>
            <div className="text-xs text-gray-400 space-y-1">
              <div className="flex items-center justify-between">
                <span>Total Agents:</span>
                <span className="text-purple-400">{teamMembers.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Ready:</span>
                <span className="text-green-400">
                  {teamMembers.filter(m => m.head).length}/{teamMembers.length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Total Tools:</span>
                <span className="text-gray-400">
                  {teamMembers.reduce((sum, m) => sum + m.arms.length, 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Guardrails:</span>
                <span className="text-gray-400">{config.spine ? '✓ Shared' : '○ None'}</span>
              </div>
            </div>
          </div>
        )}

        {/* Zoom Instructions - Bottom Center */}
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-gray-900/90 border border-gray-700 rounded-lg px-4 py-2 text-xs text-gray-300 z-30 shadow-xl">
          <div className="flex items-center gap-4">
            <span>🖱️ Shift+Drag or Middle Click to pan</span>
            <span className="text-gray-600">|</span>
            <span>⌨️ Ctrl+Scroll to zoom</span>
          </div>
        </div>
      </div>

      <NodeConfigDialog
        node={editingNode?.node || null}
        open={editingNode !== null}
        onOpenChange={(open) => !open && setEditingNode(null)}
        onSave={handleSaveConfig}
      />
    </div>
  );
}
