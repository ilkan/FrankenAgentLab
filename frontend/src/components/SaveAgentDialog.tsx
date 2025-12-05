import { useState, useEffect } from 'react';
import { AgentConfiguration } from '../types/agent-parts';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Save, Check, Minus, Loader2 } from 'lucide-react';

interface SaveAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: AgentConfiguration;
  onSave: (name: string, description: string) => Promise<void>;
  isSaving?: boolean;
}

export function SaveAgentDialog({
  open,
  onOpenChange,
  config,
  onSave,
  isSaving = false,
}: SaveAgentDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setName('');
      setDescription('');
    }
  }, [open]);

  const handleSave = async () => {
    if (!name.trim()) return;
    await onSave(name.trim(), description.trim());
  };

  // Calculate configuration summary
  const hasHead = !!config.head;
  const toolCount = config.arms.length;
  const hasMemory = !!config.heart;
  const hasExecution = !!config.leg;
  const hasGuardrails = !!config.spine;
  const totalParts =
    (hasHead ? 1 : 0) +
    toolCount +
    (hasMemory ? 1 : 0) +
    (hasExecution ? 1 : 0) +
    (hasGuardrails ? 1 : 0);

  const StatusIndicator = ({ active, label }: { active: boolean; label?: string }) => (
    <span className="flex items-center gap-1.5 text-sm text-gray-300">
      {active ? (
        <Check className="w-4 h-4 text-green-400" />
      ) : (
        <Minus className="w-4 h-4 text-gray-600" />
      )}
      {label}
    </span>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[440px] max-w-[calc(100vw-2rem)] bg-gray-950 border-gray-800 p-0 gap-0 overflow-hidden">
        {/* Header */}
        <DialogHeader className="p-6 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-green-500/20 flex-shrink-0">
              <Save className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <DialogTitle className="text-lg font-semibold text-gray-100">
                Save Your Agent
              </DialogTitle>
              <DialogDescription className="text-sm text-gray-400">
                Give your Frankenstein creation a name
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Form Content */}
        <div className="px-6 pb-6 space-y-4">
          {/* Agent Name */}
          <div className="space-y-2">
            <Label htmlFor="agent-name" className="text-sm font-medium text-gray-200">
              Agent Name
            </Label>
            <Input
              id="agent-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Customer Support Bot, Data Analyst"
              className="h-10 bg-gray-900 border-gray-700 text-gray-100 placeholder:text-gray-500 focus:border-green-500 focus:ring-green-500/20"
              disabled={isSaving}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="agent-description" className="text-sm text-gray-200">
              Description <span className="text-gray-500 font-normal">(optional)</span>
            </Label>
            <Textarea
              id="agent-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this agent do?"
              rows={3}
              className="bg-gray-900 border-gray-700 text-gray-100 placeholder:text-gray-500 resize-none focus:border-green-500 focus:ring-green-500/20"
              disabled={isSaving}
            />
          </div>

          {/* Configuration Summary */}
          <div className="p-4 bg-gray-900/70 border border-gray-800 rounded-lg">
            <h4 className="text-sm font-medium text-gray-200 mb-3">Agent Configuration</h4>
            <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-sm">
              {/* Row 1 */}
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Head (LLM):</span>
                <StatusIndicator active={hasHead} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400 flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-green-400" />
                  Tools:
                </span>
                <span className="text-gray-300">{toolCount}/6</span>
              </div>

              {/* Row 2 */}
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Memory:</span>
                <StatusIndicator active={hasMemory} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400 flex items-center gap-1.5">
                  <Minus className="w-4 h-4 text-gray-600" />
                  Execution:
                </span>
                <StatusIndicator active={hasExecution} />
              </div>

              {/* Row 3 */}
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Guardrails:</span>
                <StatusIndicator active={hasGuardrails} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400 flex items-center gap-1.5">
                  <Minus className="w-4 h-4 text-gray-600" />
                  Total Parts:
                </span>
                <span className="text-gray-300">{totalParts}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Buttons */}
        <div className="flex gap-3 px-6 pb-6">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="flex-1 h-10 bg-gray-900 border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100 hover:border-gray-600"
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!name.trim() || isSaving}
            className="flex-1 h-10 bg-green-500 hover:bg-green-600 text-white border-0 font-medium"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Agent'
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
