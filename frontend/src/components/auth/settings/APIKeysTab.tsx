import { useState } from 'react';
import { Button } from '../../ui/button';
import { Card } from '../../ui/card';
import { ScrollArea } from '../../ui/scroll-area';
import { Input } from '../../ui/input';
import {
  Key,
  Shield,
  CheckCircle,
  Loader2,
  Eye,
  EyeOff,
  Search,
} from 'lucide-react';
import { toast } from 'sonner';
import { addAPIKey, deleteAPIKey, APIKey, AddAPIKeyRequest } from '../../../utils/agentApi';

interface APIKeysTabProps {
  apiKeys: APIKey[];
  isLoading: boolean;
  token: string | null;
  onKeysUpdate: (keys: APIKey[]) => void;
}

export function APIKeysTab({ apiKeys, isLoading, token, onKeysUpdate }: APIKeysTabProps) {
  const [showAddKeyDialog, setShowAddKeyDialog] = useState(false);
  const [newKeyProvider, setNewKeyProvider] = useState('openai');
  const [newKeyValue, setNewKeyValue] = useState('');
  const [newKeyName, setNewKeyName] = useState('');
  const [isAddingKey, setIsAddingKey] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleAddAPIKey = async () => {
    if (!token) return;
    if (!newKeyValue.trim()) {
      toast.error('Please enter an API key');
      return;
    }

    setIsAddingKey(true);
    try {
      const request: AddAPIKeyRequest = {
        provider: newKeyProvider,
        api_key: newKeyValue.trim(),
        key_name: newKeyName.trim() || undefined,
      };

      const newKey = await addAPIKey(token, request);
      onKeysUpdate([...apiKeys, newKey]);
      
      setNewKeyValue('');
      setNewKeyName('');
      setNewKeyProvider('openai');
      setShowAddKeyDialog(false);
      
      toast.success('API key added successfully');
    } catch (error) {
      console.error('Failed to add API key:', error);
      const message = error instanceof Error ? error.message : 'Failed to add API key';
      toast.error(message);
    } finally {
      setIsAddingKey(false);
    }
  };

  const handleDeleteAPIKey = async (keyId: string) => {
    if (!token) return;
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteAPIKey(token, keyId);
      onKeysUpdate(apiKeys.filter(key => key.id !== keyId));
      toast.success('API key deleted successfully');
    } catch (error) {
      console.error('Failed to delete API key:', error);
      const message = error instanceof Error ? error.message : 'Failed to delete API key';
      toast.error(message);
    }
  };

  return (
    <>
      <div className="max-w-5xl mx-auto" style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: '24px' }}>
        {/* Left Column - Security Info */}
        <div className="flex flex-col gap-4">
          {/* Security Notice Card */}
          <Card className="p-4 bg-gray-900 border-gray-800">
            <Card className="p-4 bg-gradient-to-br from-green-900/20 to-blue-900/20 border-green-800/50">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-green-900/50 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-100">Enterprise Security</p>
                  <p className="text-xs text-gray-400">Google Cloud KMS</p>
                </div>
              </div>
              <div className="space-y-2 text-xs text-gray-400">
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  <span>AES-256 Encryption</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  <span>Envelope Encryption</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  <span>Zero-Knowledge</span>
                </div>
              </div>
            </Card>
          </Card>

          {/* Supported Providers */}
          <Card className="p-4 bg-gray-900 border-gray-800">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Supported Providers</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2 p-2 bg-gray-800/50 rounded">
                <div className="w-8 h-8 rounded bg-green-900/50 flex items-center justify-center">
                  <Key className="w-4 h-4 text-green-400" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-200">OpenAI</p>
                  <p className="text-xs text-gray-500">GPT-4, GPT-3.5</p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-2 bg-gray-800/50 rounded">
                <div className="w-8 h-8 rounded bg-orange-900/50 flex items-center justify-center">
                  <Key className="w-4 h-4 !text-orange-400" style={{ color: '#fb923c' }} />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-200">Anthropic</p>
                  <p className="text-xs text-gray-500">Claude 3</p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-2 bg-gray-800/50 rounded">
                <div className="w-8 h-8 rounded bg-blue-900/50 flex items-center justify-center">
                  <Key className="w-4 h-4 !text-blue-400" style={{ color: '#60a5fa' }} />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-200">Groq</p>
                  <p className="text-xs text-gray-500">Fast inference</p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-2 bg-gray-800/50 rounded">
                <div className="w-8 h-8 rounded bg-purple-900/50 flex items-center justify-center">
                  <Key className="w-4 h-4 !text-purple-400" style={{ color: '#c084fc' }} />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-200">Gemini</p>
                  <p className="text-xs text-gray-500">Google AI</p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-2 bg-gray-800/50 rounded">
                <div className="w-8 h-8 rounded bg-cyan-900/50 flex items-center justify-center">
                  <Search className="w-4 h-4 !text-cyan-400" style={{ color: '#22d3ee' }} />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-200">Tavily</p>
                  <p className="text-xs text-gray-500">Web Search</p>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column - API Keys Management */}
        <Card className="bg-gray-900 border-gray-800 flex flex-col">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <div>
              <h3 className="text-gray-100 font-medium">Your API Keys</h3>
              <p className="text-sm text-gray-400 mt-1">Manage API keys for LLM providers</p>
            </div>
            <Button 
              onClick={() => setShowAddKeyDialog(true)}
              className="gap-2 text-white shadow-lg shadow-green-900/30"
              style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
            >
              <Key className="w-4 h-4" />
              Add API Key
            </Button>
          </div>

          <ScrollArea className="flex-1 h-[500px] scrollbar-hide">
            <div className="p-4 space-y-3">
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
                </div>
              ) : apiKeys.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Key className="w-10 h-10 mx-auto mb-3 text-gray-700" />
                  <p className="text-sm">No API keys configured</p>
                  <p className="text-xs mt-1">Add your first API key to start using agents</p>
                </div>
              ) : (
                apiKeys.map((key) => (
                  <div 
                    key={key.id} 
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50 flex items-center justify-between hover:border-gray-600 transition-colors"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        key.provider === 'openai' ? 'bg-green-900/50' :
                        key.provider === 'anthropic' ? 'bg-orange-900/50' :
                        key.provider === 'groq' ? 'bg-blue-900/50' :
                        key.provider === 'gemini' ? 'bg-purple-900/50' :
                        key.provider === 'tavily' ? 'bg-cyan-900/50' :
                        'bg-gray-700/50'
                      }`}>
                        {key.provider === 'tavily' ? (
                          <Search className="w-6 h-6 !text-cyan-400" style={{ color: '#22d3ee' }} />
                        ) : (
                          <Key className={`w-6 h-6 ${
                            key.provider === 'openai' ? '!text-green-400' :
                            key.provider === 'anthropic' ? '!text-orange-400' :
                            key.provider === 'groq' ? '!text-blue-400' :
                            key.provider === 'gemini' ? '!text-purple-400' :
                            'text-gray-400'
                          }`} style={{ 
                            color: key.provider === 'openai' ? '#4ade80' :
                                   key.provider === 'anthropic' ? '#fb923c' :
                                   key.provider === 'groq' ? '#60a5fa' :
                                   key.provider === 'gemini' ? '#c084fc' :
                                   undefined
                          }} />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-gray-100 font-medium capitalize">{key.provider}</span>
                          {key.key_name && (
                            <>
                              <span className="text-gray-600">·</span>
                              <span className="text-gray-400 text-sm">{key.key_name}</span>
                            </>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-500">
                          <code className="px-2 py-0.5 bg-gray-900 rounded text-xs font-mono">
                            {key.key_preview}
                          </code>
                          <span className="text-gray-600">·</span>
                          <span>Added {new Date(key.created_at).toLocaleDateString()}</span>
                          {key.last_used_at && (
                            <>
                              <span className="text-gray-600">·</span>
                              <span>Last used {new Date(key.last_used_at).toLocaleDateString()}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteAPIKey(key.id)}
                      className="gap-2 bg-gray-900 border-red-900/50 text-red-400 hover:bg-red-950/30"
                    >
                      Delete
                    </Button>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </Card>
      </div>

      {/* Add API Key Dialog */}
      {showAddKeyDialog && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl bg-gray-900 border-gray-800 shadow-2xl">
            <div className="p-6 border-b border-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-900/50 flex items-center justify-center">
                    <Key className="w-5 h-5 text-green-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-100">Add API Key</h3>
                    <p className="text-sm text-gray-400 mt-0.5">Securely store your LLM provider API key</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowAddKeyDialog(false)}
                  disabled={isAddingKey}
                  className="text-gray-400 hover:text-gray-200 transition-colors p-2 hover:bg-gray-800 rounded-lg"
                >
                  <span className="text-xl">✕</span>
                </button>
              </div>
            </div>

            <div className="p-6 space-y-5">
              <div className="p-4 bg-green-900/10 border border-green-800/30 rounded-lg">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-300">
                      Your API key will be encrypted using <strong className="text-green-400">Google Cloud KMS</strong> with 
                      AES-256 encryption before storage. The plaintext key is never stored or logged.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-300 mb-2 block">
                    Provider <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <select
                      value={newKeyProvider}
                      onChange={(e) => setNewKeyProvider(e.target.value)}
                      className="w-full h-10 px-3 py-2 pr-10 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 transition-colors appearance-none cursor-pointer"
                      disabled={isAddingKey}
                    >
                      <option value="openai">🟢 OpenAI - GPT-4, GPT-3.5</option>
                      <option value="anthropic">🟠 Anthropic - Claude 3</option>
                      <option value="groq">🔵 Groq - Fast Inference</option>
                      <option value="gemini">🟣 Gemini - Google AI</option>
                      <option value="tavily">🔍 Tavily - Web Search</option>
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-300 mb-2 block">
                    Key Name <span className="text-gray-500 font-normal">(optional)</span>
                  </label>
                  <Input
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="e.g., Production Key"
                    className="h-10 bg-gray-800 border-gray-700 text-gray-100 focus:border-green-500 focus:ring-1 focus:ring-green-500"
                    disabled={isAddingKey}
                    autoComplete="new-password"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-300 mb-2 block">
                  API Key <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <Input
                    type={showPassword ? "text" : "password"}
                    value={newKeyValue}
                    onChange={(e) => setNewKeyValue(e.target.value)}
                    placeholder={
                      newKeyProvider === 'openai' ? 'sk-...' :
                      newKeyProvider === 'anthropic' ? 'sk-ant-...' :
                      newKeyProvider === 'groq' ? 'gsk_...' :
                      newKeyProvider === 'gemini' ? 'AIza...' :
                      newKeyProvider === 'tavily' ? 'tvly-...' :
                      'Enter your API key'
                    }
                    className="h-10 bg-gray-800 border-gray-700 text-gray-100 font-mono focus:border-green-500 focus:ring-1 focus:ring-green-500 pr-14"
                    disabled={isAddingKey}
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-100 transition-colors"
                    disabled={isAddingKey}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2 flex items-center gap-1.5">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  Encrypted with envelope encryption before storage
                </p>
              </div>
            </div>

            <div className="p-6 border-t border-gray-800 bg-gray-900/50">
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowAddKeyDialog(false)}
                  disabled={isAddingKey}
                  className="flex-1 bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700 hover:text-gray-100"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleAddAPIKey}
                  disabled={isAddingKey || !newKeyValue.trim()}
                  className="flex-1 text-white shadow-lg shadow-green-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ background: isAddingKey || !newKeyValue.trim() ? '#374151' : 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
                >
                  {isAddingKey ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Adding Key...
                    </>
                  ) : (
                    <>
                      <Key className="w-4 h-4 mr-2" />
                      Add API Key
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </>
  );
}
