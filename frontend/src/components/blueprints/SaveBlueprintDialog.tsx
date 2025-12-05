import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { createBlueprint, updateBlueprint } from '../../utils/blueprintApi';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../ui/dialog';
import { toast } from 'sonner';

interface SaveBlueprintDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  blueprintData: any;
  existingBlueprintId?: string;
  existingName?: string;
  existingDescription?: string;
  onSuccess?: () => void;
}

export function SaveBlueprintDialog({
  open,
  onOpenChange,
  blueprintData,
  existingBlueprintId,
  existingName,
  existingDescription,
  onSuccess,
}: SaveBlueprintDialogProps) {
  const { token } = useAuth();
  const [name, setName] = useState(existingName || '');
  const [description, setDescription] = useState(existingDescription || '');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast.error('Please enter a name for your blueprint');
      return;
    }

    if (!token) {
      toast.error('You must be logged in to save blueprints');
      return;
    }

    setIsLoading(true);
    try {
      if (existingBlueprintId) {
        // Update existing blueprint
        await updateBlueprint(token, existingBlueprintId, {
          name: name.trim(),
          description: description.trim() || undefined,
          blueprint_data: blueprintData,
        });
        toast.success('Blueprint updated successfully');
      } else {
        // Create new blueprint
        await createBlueprint(
          token,
          name.trim(),
          blueprintData,
          description.trim() || undefined
        );
        toast.success('Blueprint saved successfully');
      }
      
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save blueprint';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-gray-900 border-gray-800">
        <DialogHeader>
          <DialogTitle className="text-gray-100">
            {existingBlueprintId ? 'Update Blueprint' : 'Save Blueprint'}
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            {existingBlueprintId
              ? 'Update your blueprint with the current configuration'
              : 'Save your agent configuration as a blueprint'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              type="text"
              placeholder="My Research Agent"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
              className="bg-gray-800 border-gray-700"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Textarea
              id="description"
              placeholder="Describe what this agent does..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isLoading}
              className="bg-gray-800 border-gray-700 min-h-[80px]"
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : existingBlueprintId ? 'Update' : 'Save'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
