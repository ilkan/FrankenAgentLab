import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Trash2, Eye, EyeOff } from 'lucide-react';
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
} from '../ui/alert-dialog';

import { API_BASE_URL } from '../../config';

interface APIKey {
  id: string;
  provider: string;
  key_preview: string;
  created_at: string;
}

interface APIKeyListProps {
  refreshTrigger?: number;
}

export function APIKeyList({ refreshTrigger }: APIKeyListProps) {
  const { token } = useAuth();
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteKeyId, setDeleteKeyId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchKeys = async () => {
    if (!token) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/keys`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setKeys(data.keys || []);
      } else {
        toast.error('Failed to load API keys');
      }
    } catch (error) {
      console.error('Failed to fetch keys:', error);
      toast.error('Failed to load API keys');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, [token, refreshTrigger]);

  const handleDelete = async () => {
    if (!deleteKeyId || !token) return;

    setIsDeleting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/keys/${deleteKeyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        toast.success('API key deleted');
        setKeys(keys.filter(k => k.id !== deleteKeyId));
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete API key');
      }
    } catch (error) {
      console.error('Failed to delete key:', error);
      toast.error('Failed to delete API key');
    } finally {
      setIsDeleting(false);
      setDeleteKeyId(null);
    }
  };

  if (isLoading) {
    return <div className="text-gray-400 text-sm">Loading API keys...</div>;
  }

  if (keys.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <p className="text-sm">No API keys configured</p>
        <p className="text-xs mt-2">Add your first API key to start using agents</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {keys.map((key) => (
          <Card key={key.id} className="p-4 bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-200 capitalize">
                    {key.provider}
                  </span>
                </div>
                <div className="text-xs text-gray-400 font-mono mt-1">
                  {key.key_preview}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Added {new Date(key.created_at).toLocaleDateString()}
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDeleteKeyId(key.id)}
                className="text-red-400 hover:text-red-300 hover:bg-red-950"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <AlertDialog open={!!deleteKeyId} onOpenChange={(open) => !open && setDeleteKeyId(null)}>
        <AlertDialogContent className="bg-gray-900 border-gray-800">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-gray-100">Delete API Key</AlertDialogTitle>
            <AlertDialogDescription className="text-gray-400">
              Are you sure you want to delete this API key? This action cannot be undone.
              Any agents using this key will stop working.
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
