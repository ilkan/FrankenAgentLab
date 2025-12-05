import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

// CSS to hide scrollbar
const hideScrollbarStyle = `
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
`;

import {
  getUserBlueprints,
  getBlueprint,
  deleteBlueprint,
  cloneBlueprint,
  BlueprintListItem,
  Blueprint,
} from '../utils/blueprintApi';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import {
  Folder,
  Search,
  Download,
  Copy,
  Trash2,
  Brain,
  Wrench,
  Calendar,
  Footprints,
  Heart,
  Shield,
  FileText,
  Loader2,
  X,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';

interface MyAgentsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLoad?: (blueprintId: string) => void;
  onUseBlueprint?: (config: any) => void;
}

export function MyAgentsDialog({ open, onOpenChange, onLoad, onUseBlueprint }: MyAgentsDialogProps) {
  const { token } = useAuth();
  const [blueprints, setBlueprints] = useState<BlueprintListItem[]>([]);
  const [selectedBlueprint, setSelectedBlueprint] = useState<Blueprint | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchBlueprints = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await getUserBlueprints(token);
      setBlueprints(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch blueprints:', error);
      toast.error('Failed to load agents');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchBlueprintDetails = async (id: string) => {
    if (!token) return;
    setIsLoadingDetails(true);
    try {
      const data = await getBlueprint(token, id);
      setSelectedBlueprint(data);
    } catch (error) {
      console.error('Failed to fetch blueprint details:', error);
    } finally {
      setIsLoadingDetails(false);
    }
  };

  useEffect(() => {
    if (open) {
      fetchBlueprints();
    }
  }, [open, token]);

  useEffect(() => {
    if (selectedId && token) {
      fetchBlueprintDetails(selectedId);
    }
  }, [selectedId, token]);

  const handleDelete = async () => {
    if (!deleteId || !token) return;
    setIsDeleting(true);
    try {
      await deleteBlueprint(token, deleteId);
      toast.success('Agent deleted');
      setBlueprints(blueprints.filter((b) => b.id !== deleteId));
      if (selectedId === deleteId) {
        setSelectedId(null);
        setSelectedBlueprint(null);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete agent';
      toast.error(message);
    } finally {
      setIsDeleting(false);
      setDeleteId(null);
    }
  };

  const handleLoad = () => {
    if (selectedBlueprint && onUseBlueprint) {
      // Convert blueprint data to AgentConfiguration format and load it
      onUseBlueprint(selectedBlueprint.blueprint_data);
      toast.success(`Loaded "${selectedBlueprint.name}" agent`);
      onOpenChange(false);
    } else if (selectedId && onLoad) {
      // Fallback to old behavior
      onLoad(selectedId);
      onOpenChange(false);
    }
  };

  const filteredBlueprints = blueprints.filter((b) =>
    b.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getPartsInfo = (blueprintData: any) => {
    if (!blueprintData)
      return { head: null, tools: [], execution: null, memory: null, guardrails: null };
    return {
      head: blueprintData.head || null,
      tools: blueprintData.arms || [],
      execution: blueprintData.legs || blueprintData.leg || null,
      memory: blueprintData.heart || null,
      guardrails: blueprintData.spine || null,
    };
  };

  // Get parts info for a blueprint list item (fetches from cache or calculates)
  const getBlueprintPartsCount = (bp: BlueprintListItem) => {
    // If this is the selected blueprint, use the detailed data
    if (selectedBlueprint && selectedBlueprint.id === bp.id) {
      const parts = getPartsInfo(selectedBlueprint.blueprint_data);
      const totalParts = [
        parts.head,
        ...(parts.tools || []),
        parts.memory,
        parts.execution,
        parts.guardrails,
      ].filter(Boolean).length;
      return {
        totalParts,
        hasHead: !!parts.head,
        toolCount: parts.tools?.length || 0,
        hasMemory: !!parts.memory,
        hasExecution: !!parts.execution,
        hasGuardrails: !!parts.guardrails,
      };
    }
    // Default values for non-selected items
    return { totalParts: 0, hasHead: false, toolCount: 0, hasMemory: false, hasExecution: false, hasGuardrails: false };
  };

  const partsInfo = selectedBlueprint ? getPartsInfo(selectedBlueprint.blueprint_data) : null;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  // Agent Card Component - Compact style with all body parts
  const AgentCard = ({ bp, partsData }: { bp: BlueprintListItem; partsData?: { totalParts: number; hasHead: boolean; toolCount: number; hasMemory: boolean; hasExecution: boolean; hasGuardrails: boolean } }) => {
    const isSelected = selectedId === bp.id;
    const parts = partsData || { totalParts: 0, hasHead: false, toolCount: 0, hasMemory: false, hasExecution: false, hasGuardrails: false };
    const hasPartsData = parts.totalParts > 0;
    
    return (
      <Card
        onClick={() => setSelectedId(bp.id)}
        className={`cursor-pointer transition-colors p-4 ${
          isSelected
            ? 'bg-green-950/20 border-green-500'
            : 'bg-gray-900/50 border-gray-800 hover:border-gray-700'
        }`}
      >
        <div className="flex items-start gap-3 mb-2">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
            isSelected
              ? 'bg-gradient-to-br from-green-600 to-lime-600 text-white shadow-lg shadow-green-500/20'
              : 'bg-gray-700 text-gray-300'
          }`}>
            <Brain className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            {/* Agent Name */}
            <h3 className="text-base font-medium text-gray-100 mb-0.5 truncate">{bp.name}</h3>
            {/* Parts Count - only show for selected, otherwise show description hint */}
            <p className="text-xs text-gray-500">
              {hasPartsData ? `${parts.totalParts} parts` : (isSelected ? 'Loading...' : 'Click to view details')}
            </p>
          </div>
        </div>
        
        {/* Description (if available) */}
        {bp.description && (
          <p className="text-xs text-gray-400 mb-2 line-clamp-2">{bp.description}</p>
        )}
        
        {/* Badges - only show for selected item with data */}
        {hasPartsData && (
        <div className="flex gap-1 flex-wrap">
          {parts.hasHead && (
            <Badge
              variant="outline"
              className="text-[9px] px-1.5 py-0"
              style={{ borderRadius: '4px', borderColor: 'rgba(34, 197, 94, 0.5)', color: '#4ade80', backgroundColor: 'rgba(20, 83, 45, 0.3)' }}
            >
              Head
            </Badge>
          )}
          {parts.toolCount > 0 && (
            <Badge
              variant="outline"
              className="text-[9px] px-1.5 py-0"
              style={{ borderRadius: '4px', borderColor: 'rgba(37, 99, 235, 0.5)', color: '#60a5fa', backgroundColor: 'rgba(30, 58, 138, 0.3)' }}
            >
              {parts.toolCount} Tool{parts.toolCount !== 1 ? 's' : ''}
            </Badge>
          )}
          {parts.hasMemory && (
            <Badge
              variant="outline"
              className="text-[9px] px-1.5 py-0"
              style={{ borderRadius: '4px', borderColor: 'rgba(236, 72, 153, 0.5)', color: '#f472b6', backgroundColor: 'rgba(131, 24, 67, 0.3)' }}
            >
              Memory
            </Badge>
          )}
          {parts.hasExecution && (
            <Badge
              variant="outline"
              className="text-[9px] px-1.5 py-0"
              style={{ borderRadius: '4px', borderColor: 'rgba(249, 115, 22, 0.5)', color: '#fb923c', backgroundColor: 'rgba(124, 45, 18, 0.3)' }}
            >
              Execution
            </Badge>
          )}
          {parts.hasGuardrails && (
            <Badge
              variant="outline"
              className="text-[9px] px-1.5 py-0"
              style={{ borderRadius: '4px', borderColor: 'rgba(6, 182, 212, 0.5)', color: '#22d3ee', backgroundColor: 'rgba(21, 94, 117, 0.3)' }}
            >
              Guardrails
            </Badge>
          )}
        </div>
        )}
      </Card>
    );
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <style>{hideScrollbarStyle}</style>
        <DialogContent className="bg-gray-950 border-gray-800 p-0 overflow-hidden flex flex-col" style={{ width: '45vw', maxWidth: '65vw', height: '75vh' }}>
          {/* Header with Close Button */}
          <DialogHeader className="px-6 pt-6 pb-5 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-gradient-to-br from-green-600 to-lime-600 rounded-lg flex items-center justify-center shadow-lg shadow-green-500/30">
                  <Folder className="w-5 h-5 text-white" />
                </div>
                <div>
                  <DialogTitle className="text-xl text-gray-100">My Agents</DialogTitle>
                  <DialogDescription className="text-sm text-gray-400">
                    {blueprints.length} saved agent{blueprints.length !== 1 ? 's' : ''}
                  </DialogDescription>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onOpenChange(false)}
                className="h-9 w-9 text-gray-400 hover:text-gray-100 hover:bg-gray-800"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </DialogHeader>

          {/* Search Bar */}
          <div className="px-4 sm:px-6 py-4 border-b border-gray-800 flex-shrink-0">
            <div className="relative">
              <Search className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
              <Input
                type="text"
                placeholder="Search agents..."
                value={searchQuery}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
                className="h-10 bg-gray-900 border-gray-800 text-gray-100 text-sm placeholder:text-gray-500 rounded-lg"
                style={{ paddingLeft: '44px' }}
              />
            </div>
          </div>

          {/* Main Content */}
          <div className="flex flex-1 overflow-hidden">
            {/* Left - Agent Cards */}
            <div className="flex-1 border-r border-gray-800 overflow-y-auto hide-scrollbar">
              <div className="p-3 space-y-2">
                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
                  </div>
                ) : filteredBlueprints.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FileText className="w-10 h-10 mx-auto mb-3 text-gray-700" />
                    <p className="text-sm">{searchQuery ? 'No agents found' : 'No agents yet'}</p>
                    <p className="text-xs mt-1">Create your first agent to get started</p>
                  </div>
                ) : (
                  filteredBlueprints.map((bp) => (
                    <AgentCard 
                      key={bp.id} 
                      bp={bp} 
                      partsData={getBlueprintPartsCount(bp)}
                    />
                  ))
                )}
              </div>
            </div>

            {/* Right - Agent Details */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
              {isLoadingDetails ? (
                <div className="flex-1 flex items-center justify-center">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
                </div>
              ) : selectedBlueprint ? (
                <>
                  <div className="flex-1 overflow-y-auto hide-scrollbar">
                    <div className="p-4 sm:p-6 space-y-5">
                      {/* Name & Date */}
                      <div>
                        <h3 className="text-xl font-medium text-gray-100 break-words">
                          {selectedBlueprint.name}
                        </h3>
                        <div className="flex items-center gap-2 mt-3 text-xs text-gray-500 px-1">
                          <Calendar className="w-3.5 h-3.5" />
                          <span>Created {formatDate(selectedBlueprint.created_at)}</span>
                        </div>
                        {selectedBlueprint.description && (
                          <p className="text-sm text-gray-400 mt-4 break-words px-1 leading-relaxed">
                            {selectedBlueprint.description}
                          </p>
                        )}
                      </div>

                      {/* Configuration */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-400 mb-3">Configuration</h4>
                        <div className="space-y-2">
                          {partsInfo?.head && (
                            <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                              <div
                                className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                                style={{ backgroundColor: 'rgba(147, 51, 234, 0.3)' }}
                              >
                                <Brain className="w-5 h-5" style={{ color: '#c084fc' }} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-200 break-words">
                                  {partsInfo.head.name || 'OpenAI GPT-4o-mini'}
                                </div>
                                <div className="text-xs text-gray-500">Head (LLM)</div>
                              </div>
                            </div>
                          )}

                          {partsInfo?.tools && partsInfo.tools.length > 0 && (
                            <div className="flex items-start gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                              <div
                                className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                                style={{ backgroundColor: 'rgba(37, 99, 235, 0.3)' }}
                              >
                                <Wrench className="w-5 h-5" style={{ color: '#60a5fa' }} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-200">
                                  {partsInfo.tools.length} Tool
                                  {partsInfo.tools.length !== 1 ? 's' : ''}
                                </div>
                                <div className="space-y-0.5 mt-1">
                                  {partsInfo.tools.map((tool: any, idx: number) => (
                                    <div key={idx} className="text-xs text-gray-400 break-words">
                                      • {tool.name || tool.type || tool.id || 'Unknown Tool'}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {partsInfo?.memory && (
                            <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                              <div
                                className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                                style={{ backgroundColor: 'rgba(236, 72, 153, 0.3)' }}
                              >
                                <Heart className="w-5 h-5" style={{ color: '#f472b6' }} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-200">
                                  {partsInfo.memory.name || 'Memory'}
                                </div>
                                <div className="text-xs text-gray-500">Memory/Knowledge</div>
                              </div>
                            </div>
                          )}

                          {partsInfo?.execution && (
                            <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                              <div
                                className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                                style={{ backgroundColor: 'rgba(249, 115, 22, 0.3)' }}
                              >
                                <Footprints className="w-5 h-5" style={{ color: '#fb923c' }} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-200">
                                  {partsInfo.execution.name || 'Single Agent'}
                                </div>
                                <div className="text-xs text-gray-500">Execution Mode</div>
                              </div>
                            </div>
                          )}

                          {partsInfo?.guardrails && (
                            <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                              <div
                                className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                                style={{ backgroundColor: 'rgba(6, 182, 212, 0.3)' }}
                              >
                                <Shield className="w-5 h-5" style={{ color: '#22d3ee' }} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-gray-200">
                                  {partsInfo.guardrails.name || 'Guardrails'}
                                </div>
                                <div className="text-xs text-gray-500">Guardrails</div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions - Fixed at bottom */}
                  <div className="p-4 sm:p-5 border-t border-gray-800 flex gap-2 flex-shrink-0 bg-gray-950">
                    <Button
                      onClick={handleLoad}
                      className="flex-1 h-10 text-white font-medium border-0"
                      style={{
                        background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)',
                      }}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Load Agent
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={async () => {
                        if (!selectedBlueprint || !token) return;
                        try {
                          const cloned = await cloneBlueprint(token, selectedBlueprint.id);
                          toast.success(`Cloned "${selectedBlueprint.name}"`);
                          fetchBlueprints();
                        } catch (error) {
                          const message = error instanceof Error ? error.message : 'Failed to clone agent';
                          toast.error(message);
                        }
                      }}
                      className="h-10 w-10 bg-gray-900 border-gray-700 text-gray-400 hover:bg-gray-800"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setDeleteId(selectedBlueprint.id)}
                      className="h-10 w-10 bg-gray-900 border-gray-700 text-red-400 hover:bg-red-950/30"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <FileText className="w-12 h-12 mx-auto mb-3 text-gray-700" />
                    <p className="text-sm">Select an agent to view details</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteId} onOpenChange={(openState: boolean) => !openState && setDeleteId(null)}>
        <AlertDialogContent className="bg-gray-900 border-gray-800">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-gray-100">Delete Agent</AlertDialogTitle>
            <AlertDialogDescription className="text-gray-400">
              Are you sure you want to delete this agent? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-gray-800 text-gray-300 hover:bg-gray-700">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
