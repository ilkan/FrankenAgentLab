import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { toast } from 'sonner';

import { API_BASE_URL } from '../../config';

interface AddAPIKeyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', placeholder: 'sk-...' },
  { value: 'anthropic', label: 'Anthropic', placeholder: 'sk-ant-...' },
  { value: 'groq', label: 'Groq', placeholder: 'gsk_...' },
  { value: 'gemini', label: 'Google Gemini', placeholder: 'AI...' },
];

export function AddAPIKeyDialog({ open, onOpenChange, onSuccess }: AddAPIKeyDialogProps) {
  const { token } = useAuth();
  const [provider, setProvider] = useState<string>('');
  const [apiKey, setApiKey] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!provider || !apiKey) {
      toast.error('Please select a provider and enter an API key');
      return;
    }

    if (!token) {
      toast.error('You must be logged in to add API keys');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          provider,
          api_key: apiKey,
        }),
      });

      if (response.ok) {
        toast.success('API key added successfully');
        setProvider('');
        setApiKey('');
        onOpenChange(false);
        onSuccess?.();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to add API key');
      }
    } catch (error) {
      console.error('Failed to add key:', error);
      toast.error('Failed to add API key');
    } finally {
      setIsLoading(false);
    }
  };

  const selectedProvider = PROVIDERS.find(p => p.value === provider);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-gray-900 border-gray-800">
        <DialogHeader>
          <DialogTitle className="text-gray-100">Add API Key</DialogTitle>
          <DialogDescription className="text-gray-400">
            Add your LLM provider API key to use with your agents. Keys are encrypted and stored securely.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="provider">Provider</Label>
            <Select value={provider} onValueChange={setProvider} disabled={isLoading}>
              <SelectTrigger id="provider" className="bg-gray-800 border-gray-700">
                <SelectValue placeholder="Select a provider" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                {PROVIDERS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="apiKey">API Key</Label>
            <Input
              id="apiKey"
              type="password"
              placeholder={selectedProvider?.placeholder || 'Enter your API key'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              disabled={isLoading}
              className="bg-gray-800 border-gray-700 font-mono"
              required
            />
            <p className="text-xs text-gray-500">
              Your API key will be encrypted before storage
            </p>
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
              {isLoading ? 'Adding...' : 'Add Key'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
