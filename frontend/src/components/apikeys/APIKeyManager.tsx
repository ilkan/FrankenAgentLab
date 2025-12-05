import React, { useState } from 'react';
import { APIKeyList } from './APIKeyList';
import { AddAPIKeyDialog } from './AddAPIKeyDialog';
import { Button } from '../ui/button';
import { Plus } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';

interface APIKeyManagerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function APIKeyManager({ open, onOpenChange }: APIKeyManagerProps) {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Refresh keys when dialog opens
  React.useEffect(() => {
    if (open) {
      setRefreshKey(prev => prev + 1);
    }
  }, [open]);

  const handleAddSuccess = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-2xl bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-gray-100">API Key Management</DialogTitle>
            <DialogDescription className="text-gray-400">
              Manage your LLM provider API keys. Keys are encrypted and only used for your agents.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="flex justify-end">
              <Button
                onClick={() => setShowAddDialog(true)}
                size="sm"
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                Add API Key
              </Button>
            </div>

            <APIKeyList refreshTrigger={refreshKey} />
          </div>
        </DialogContent>
      </Dialog>

      <AddAPIKeyDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        onSuccess={handleAddSuccess}
      />
    </>
  );
}
