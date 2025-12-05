import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Loader2, Sparkles, CheckCircle, XCircle } from 'lucide-react';
import { improveInstructions, ImproveInstructionsRequest } from '../utils/api';
import { toast } from 'sonner@2.0.3';
import { Alert, AlertDescription } from './ui/alert';

interface InstructionImprovementDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentInstructions: string;
  onAccept: (improvedInstructions: string) => void;
  context?: {
    agent_purpose?: string;
    tools_available?: string[];
  };
}

export function InstructionImprovementDialog({
  open,
  onOpenChange,
  currentInstructions,
  onAccept,
  context,
}: InstructionImprovementDialogProps) {
  const [improvementGoal, setImprovementGoal] = useState('');
  const [isImproving, setIsImproving] = useState(false);
  const [improvedInstructions, setImprovedInstructions] = useState('');
  const [explanation, setExplanation] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [hasImproved, setHasImproved] = useState(false);

  const handleImprove = async () => {
    if (!improvementGoal.trim()) {
      toast.error('Please enter an improvement goal');
      return;
    }

    setIsImproving(true);
    setHasImproved(false);

    try {
      const request: ImproveInstructionsRequest = {
        current_instructions: currentInstructions,
        improvement_goal: improvementGoal,
        context,
      };

      const response = await improveInstructions(request);
      
      setImprovedInstructions(response.improved_instructions);
      setExplanation(response.explanation);
      setSuggestions(response.suggestions || []);
      setHasImproved(true);
      
      toast.success('Instructions improved successfully!');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to improve instructions';
      toast.error(errorMessage);
      console.error('Failed to improve instructions:', error);
    } finally {
      setIsImproving(false);
    }
  };

  const handleAccept = () => {
    onAccept(improvedInstructions);
    handleClose();
    toast.success('Improved instructions applied!');
  };

  const handleReject = () => {
    setHasImproved(false);
    setImprovedInstructions('');
    setExplanation('');
    setSuggestions([]);
    toast.info('Keeping original instructions');
  };

  const handleClose = () => {
    setImprovementGoal('');
    setHasImproved(false);
    setImprovedInstructions('');
    setExplanation('');
    setSuggestions([]);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-yellow-500" />
            Improve Instructions with AI
          </DialogTitle>
          <DialogDescription>
            Use AI to enhance your agent's system prompt for better clarity and effectiveness
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Current Instructions */}
          <div className="space-y-2">
            <Label>Current Instructions</Label>
            <Textarea
              value={currentInstructions}
              readOnly
              rows={4}
              className="bg-gray-950 border-gray-800 text-gray-400"
            />
          </div>

          {/* Improvement Goal */}
          <div className="space-y-2">
            <Label htmlFor="improvement-goal">
              What would you like to improve?
            </Label>
            <Textarea
              id="improvement-goal"
              value={improvementGoal}
              onChange={(e) => setImprovementGoal(e.target.value)}
              placeholder="E.g., Make it more specific for customer support, add tone guidelines, improve clarity..."
              rows={3}
              disabled={isImproving || hasImproved}
            />
          </div>

          {/* Improve Button */}
          {!hasImproved && (
            <Button
              onClick={handleImprove}
              disabled={isImproving || !improvementGoal.trim()}
              className="w-full gap-2"
            >
              {isImproving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Improving Instructions...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Improve Instructions
                </>
              )}
            </Button>
          )}

          {/* Improved Instructions */}
          {hasImproved && (
            <>
              <div className="space-y-2">
                <Label>Improved Instructions</Label>
                <Textarea
                  value={improvedInstructions}
                  onChange={(e) => setImprovedInstructions(e.target.value)}
                  rows={6}
                  className="bg-green-950/20 border-green-800"
                />
              </div>

              {/* Explanation */}
              {explanation && (
                <Alert className="bg-blue-950/20 border-blue-800">
                  <AlertDescription>
                    <div className="font-semibold mb-1">What Changed:</div>
                    <div className="text-sm text-gray-300">{explanation}</div>
                  </AlertDescription>
                </Alert>
              )}

              {/* Suggestions */}
              {suggestions.length > 0 && (
                <Alert className="bg-purple-950/20 border-purple-800">
                  <AlertDescription>
                    <div className="font-semibold mb-2">Additional Suggestions:</div>
                    <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                      {suggestions.map((suggestion, index) => (
                        <li key={index}>{suggestion}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
            </>
          )}
        </div>

        <DialogFooter>
          {hasImproved ? (
            <>
              <Button variant="outline" onClick={handleReject} className="gap-2">
                <XCircle className="w-4 h-4" />
                Reject
              </Button>
              <Button onClick={handleAccept} className="gap-2">
                <CheckCircle className="w-4 h-4" />
                Accept & Apply
              </Button>
            </>
          ) : (
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
