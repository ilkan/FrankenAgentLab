import { useState, useEffect, useRef } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { BodyPartLibrary } from './components/BodyPartLibrary';
import { Canvas } from './components/Canvas';
import { AgentPanel } from './components/AgentPanel';
import { ChatPanel } from './components/ChatPanel';
import { LogsPanel } from './components/LogsPanel';
import { Footer } from './components/Footer';
import { AgentConfiguration, NodeInstance, TeamMember } from './types/agent-parts';
import { toast } from 'sonner@2.0.3';
import { Toaster } from './components/ui/sonner';
import { TopBar } from './components/TopBar';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from './components/ui/resizable';
import { convertToBlueprint, validateBlueprint } from './utils/api';
import { useSchemaStore } from './stores/schemaStore';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AuthDialog } from './components/auth/AuthDialog';
import { ResetPasswordDialog } from './components/auth/ResetPasswordDialog';
import { APIKeyManager } from './components/apikeys/APIKeyManager';
import { SettingsPage } from './components/auth/SettingsPage';
import { SaveBlueprintDialog } from './components/blueprints/SaveBlueprintDialog';
import { Marketplace } from './components/marketplace/Marketplace';
import { SaveAgentDialog } from './components/SaveAgentDialog';
import { MyAgentsDialog } from './components/MyAgentsDialog';
import { getBlueprint } from './utils/blueprintApi';
import { Button } from './components/ui/button';
import { API_BASE_URL } from './config';


function AppContent() {
  const { isAuthenticated, token, setUser, setToken } = useAuth();
  const [agentConfig, setAgentConfig] = useState<AgentConfiguration>({
    arms: [],
  });
  const [deployedBlueprint, setDeployedBlueprint] = useState<any | undefined>();
  const [logs, setLogs] = useState<string[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>();
  const [currentBlueprintId, setCurrentBlueprintId] = useState<string | undefined>();
  const [resetPasswordToken, setResetPasswordToken] = useState<string | null>(null);
  const [showResetPassword, setShowResetPassword] = useState(false);
  
  // Refs for clearing child component state
  const clearChatRef = useRef<(() => void) | null>(null);
  const clearLogsBackendRef = useRef<(() => void) | null>(null);
  
  // Handle OAuth callback and password reset on mount
  useEffect(() => {
    const handleOAuth = async () => {
      // Check for password reset token first
      const params = new URLSearchParams(window.location.search);
      const resetToken = params.get('reset_token');
      
      if (resetToken) {
        setResetPasswordToken(resetToken);
        setShowResetPassword(true);
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }
      
      // Check URL hash for OAuth callback data (from backend redirect)
      // Format: #oauth_callback?email=...&name=...
      const hash = window.location.hash;
      let email = null;
      let name = null;
      let picture = null;
      let provider = null;
      let provider_user_id = null;
      
      if (hash.includes('oauth_callback?')) {
        const queryString = hash.split('?')[1];
        const hashParams = new URLSearchParams(queryString);
        email = hashParams.get('email');
        name = hashParams.get('name');
        picture = hashParams.get('picture');
        provider = hashParams.get('provider');
        provider_user_id = hashParams.get('provider_user_id');
      }
      
      // Also check query params for traditional OAuth flow
      const code = params.get('code');
      const state = params.get('state');
      const error = params.get('error');

      // Handle OAuth errors
      if (error) {
        toast.error(`OAuth error: ${error}`);
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }

      // Handle backend redirect with user data in hash
      if (email && provider) {
        try {
          // Exchange user data for JWT token
          const response = await fetch(`${API_BASE_URL}/api/auth/oauth/exchange`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email,
              name,
              picture,
              provider,
              provider_user_id,
            }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to complete OAuth login');
          }

          const data = await response.json();
          localStorage.setItem('auth_token', data.access_token);
          setToken(data.access_token);

          // Fetch full user profile
          const userResponse = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${data.access_token}` },
          });

          if (userResponse.ok) {
            const userData = await userResponse.json();
            setUser(userData);
            toast.success('Logged in successfully!');
          }

          // Clean up URL
          window.history.replaceState({}, document.title, window.location.pathname);
        } catch (err) {
          const message = err instanceof Error ? err.message : 'OAuth login failed';
          toast.error(message);
          window.history.replaceState({}, document.title, window.location.pathname);
        }
        return;
      }

      // Handle traditional OAuth code flow (if backend sends code instead)
      if (!code) return;

      // Get stored state from localStorage (persists across redirects)
      const storedState = localStorage.getItem('oauth_state');
      const storedProvider = localStorage.getItem('oauth_provider') || 'google';
      const timestamp = localStorage.getItem('oauth_timestamp');
      
      // Check if state is expired (10 minutes)
      if (timestamp && Date.now() - parseInt(timestamp) > 600000) {
        toast.error('OAuth session expired. Please try again.');
        localStorage.removeItem('oauth_state');
        localStorage.removeItem('oauth_provider');
        localStorage.removeItem('oauth_timestamp');
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }
      
      if (state !== storedState) {
        toast.error('Invalid OAuth state. Please try again.');
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }

      // Clear stored state and provider
      localStorage.removeItem('oauth_state');
      localStorage.removeItem('oauth_provider');
      localStorage.removeItem('oauth_timestamp');

      try {
        const redirectUri = `${API_BASE_URL}/api/auth/callback`;
        
        const response = await fetch(`${API_BASE_URL}/api/auth/oauth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider: storedProvider,
            code,
            redirect_uri: redirectUri,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'OAuth login failed');
        }

        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        setToken(data.access_token);

        const userResponse = await fetch(`${API_BASE_URL}/api/auth/me`, {
          headers: { 'Authorization': `Bearer ${data.access_token}` },
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUser(userData);
        }

        toast.success('Logged in successfully!');
        window.history.replaceState({}, document.title, window.location.pathname);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'OAuth login failed';
        toast.error(message);
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    };

    handleOAuth();
  }, [setUser, setToken]);
  
  // Dialog states
  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [showApiKeyManager, setShowApiKeyManager] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showSaveAgentDialog, setShowSaveAgentDialog] = useState(false);
  const [isSavingAgent, setIsSavingAgent] = useState(false);
  const [showBlueprintList, setShowBlueprintList] = useState(false);
  const [showMarketplace, setShowMarketplace] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  // Fetch component schemas on app load
  const { fetchSchemas, error: schemaError } = useSchemaStore();
  
  useEffect(() => {
    fetchSchemas().catch((error) => {
      console.error('Failed to load component schemas:', error);
      toast.error('Failed to load component schemas. Some features may be limited.');
    });
  }, [fetchSchemas]);

  const handleAddNode = (node: NodeInstance, type: 'head' | 'arm' | 'heart' | 'leg' | 'spine') => {
    const isTeamMode = agentConfig.leg?.id === 'team';
    
    // In team mode, head/arm/heart should be added to team members, not main config
    if (isTeamMode && (type === 'head' || type === 'arm' || type === 'heart')) {
      toast.info('In Team mode, drag components to team member cards in the right panel');
      return;
    }
    
    if (type === 'arm') {
      if (agentConfig.arms.length >= 6) {
        toast.error('Maximum 6 tools allowed');
        return;
      }
      setAgentConfig(prev => ({
        ...prev,
        arms: [...prev.arms, node],
      }));
      toast.success(`Added ${node.name} to tools`);
    } else if (type === 'head') {
      if (agentConfig.head) {
        toast.error('Head already exists. Remove it first.');
        return;
      }
      setAgentConfig(prev => ({ ...prev, head: node }));
      toast.success(`Added ${node.name} as head`);
    } else if (type === 'heart') {
      if (agentConfig.heart) {
        toast.error('Heart already exists. Remove it first.');
        return;
      }
      setAgentConfig(prev => ({ ...prev, heart: node }));
      toast.success(`Added ${node.name} as memory`);
    } else if (type === 'leg') {
      if (agentConfig.leg) {
        toast.error('Execution mode already exists. Remove it first.');
        return;
      }
      // When switching to team mode, clear single-agent specific config
      if (node.id === 'team') {
        setAgentConfig(prev => ({ 
          ...prev, 
          leg: node,
          head: undefined,
          arms: [],
          heart: undefined,
          teamMembers: [],
        }));
        toast.success('Team mode activated! Add team members in the right panel.');
      } else {
        // When switching from team mode to single agent, clear team members
        setAgentConfig(prev => ({ 
          ...prev, 
          leg: node,
          teamMembers: undefined,
        }));
        toast.success(`Added ${node.name} as execution mode`);
      }
    } else if (type === 'spine') {
      if (agentConfig.spine) {
        toast.error('Guardrails already exist. Remove them first.');
        return;
      }
      setAgentConfig(prev => ({ ...prev, spine: node }));
      toast.success(`Added ${node.name} as guardrails`);
    }
  };

  const handleRemoveNode = (type: 'head' | 'arm' | 'heart' | 'leg' | 'spine', index?: number) => {
    if (type === 'arm' && index !== undefined) {
      setAgentConfig(prev => ({
        ...prev,
        arms: prev.arms.filter((_, i) => i !== index),
      }));
      toast.info('Tool removed');
    } else if (type === 'head') {
      setAgentConfig(prev => ({ ...prev, head: undefined }));
      toast.info('Head removed');
    } else if (type === 'heart') {
      setAgentConfig(prev => ({ ...prev, heart: undefined }));
      toast.info('Memory removed');
    } else if (type === 'leg') {
      // When removing execution mode, also clear team members if in team mode
      const wasTeamMode = agentConfig.leg?.id === 'team';
      setAgentConfig(prev => ({ 
        ...prev, 
        leg: undefined,
        teamMembers: wasTeamMode ? undefined : prev.teamMembers,
      }));
      toast.info('Execution mode removed');
    } else if (type === 'spine') {
      setAgentConfig(prev => ({ ...prev, spine: undefined }));
      toast.info('Guardrails removed');
    }
  };

  const handleUpdateNode = (
    type: 'head' | 'arm' | 'heart' | 'leg' | 'spine',
    updates: Partial<NodeInstance>,
    index?: number
  ) => {
    if (type === 'arm' && index !== undefined) {
      setAgentConfig(prev => ({
        ...prev,
        arms: prev.arms.map((arm, i) => (i === index ? { ...arm, ...updates } : arm)),
      }));
    } else if (type === 'head' && agentConfig.head) {
      setAgentConfig(prev => ({
        ...prev,
        head: { ...prev.head!, ...updates },
      }));
    } else if (type === 'heart' && agentConfig.heart) {
      setAgentConfig(prev => ({
        ...prev,
        heart: { ...prev.heart!, ...updates },
      }));
    } else if (type === 'leg' && agentConfig.leg) {
      setAgentConfig(prev => ({
        ...prev,
        leg: { ...prev.leg!, ...updates },
      }));
    } else if (type === 'spine' && agentConfig.spine) {
      setAgentConfig(prev => ({
        ...prev,
        spine: { ...prev.spine!, ...updates },
      }));
    }
    toast.success('Configuration updated');
  };

  const handleClearAll = () => {
    setAgentConfig({ arms: [] });
    // Clear logs and hide Test Agent/Logs panels
    setLogs([]);
    clearLogsBackendRef.current?.();
    clearChatRef.current?.();
    setCurrentSessionId(undefined);
    setDeployedBlueprint(undefined);
    toast.info('All cleared');
  };

  // Team member handlers
  const handleAddTeamMember = () => {
    const memberCount = (agentConfig.teamMembers?.length || 0) + 1;
    const isFirstMember = memberCount === 1;
    
    const newMember: TeamMember = {
      id: `member-${Date.now()}`,
      name: isFirstMember ? '👑 Leader' : `Agent ${memberCount}`,
      role: isFirstMember ? 'Team coordinator' : 'Specialist agent',
      arms: [],
    };
    setAgentConfig(prev => ({
      ...prev,
      teamMembers: [...(prev.teamMembers || []), newMember],
    }));
    toast.success('Team member added');
  };

  const handleRemoveTeamMember = (memberId: string) => {
    setAgentConfig(prev => {
      const currentMembers = prev.teamMembers || [];
      const removedIndex = currentMembers.findIndex(m => m.id === memberId);
      const filteredMembers = currentMembers.filter(m => m.id !== memberId);
      
      // If the leader (index 0) was removed and there are remaining members,
      // promote the new first member to leader
      if (removedIndex === 0 && filteredMembers.length > 0) {
        filteredMembers[0] = {
          ...filteredMembers[0],
          name: '👑 Leader',
          role: 'Team coordinator',
        };
      }
      
      return {
        ...prev,
        teamMembers: filteredMembers,
      };
    });
    toast.info('Team member removed');
  };

  const handleUpdateTeamMember = (memberId: string, updates: Partial<TeamMember>) => {
    setAgentConfig(prev => ({
      ...prev,
      teamMembers: (prev.teamMembers || []).map(m => 
        m.id === memberId ? { ...m, ...updates } : m
      ),
    }));
  };

  const handleAddNodeToTeamMember = (memberId: string, node: NodeInstance, type: 'head' | 'arm' | 'heart') => {
    setAgentConfig(prev => ({
      ...prev,
      teamMembers: (prev.teamMembers || []).map(m => {
        if (m.id !== memberId) return m;
        
        if (type === 'head') {
          return { ...m, head: node };
        } else if (type === 'arm') {
          if (m.arms.length >= 6) {
            toast.error('Maximum 6 tools per agent');
            return m;
          }
          return { ...m, arms: [...m.arms, node] };
        } else if (type === 'heart') {
          return { ...m, heart: node };
        }
        return m;
      }),
    }));
    toast.success(`Added ${node.name} to team member`);
  };

  const handleRemoveNodeFromTeamMember = (memberId: string, type: 'head' | 'arm' | 'heart', index?: number) => {
    setAgentConfig(prev => ({
      ...prev,
      teamMembers: (prev.teamMembers || []).map(m => {
        if (m.id !== memberId) return m;
        
        if (type === 'head') {
          return { ...m, head: undefined };
        } else if (type === 'arm' && index !== undefined) {
          return { ...m, arms: m.arms.filter((_, i) => i !== index) };
        } else if (type === 'heart') {
          return { ...m, heart: undefined };
        }
        return m;
      }),
    }));
    toast.info('Component removed from team member');
  };

  const handleUpdateNodeInTeamMember = (
    memberId: string, 
    type: 'head' | 'arm' | 'heart', 
    updates: Partial<NodeInstance>, 
    index?: number
  ) => {
    setAgentConfig(prev => ({
      ...prev,
      teamMembers: (prev.teamMembers || []).map(m => {
        if (m.id !== memberId) return m;
        
        if (type === 'head' && m.head) {
          return { ...m, head: { ...m.head, ...updates } };
        } else if (type === 'arm' && index !== undefined) {
          return { 
            ...m, 
            arms: m.arms.map((arm, i) => i === index ? { ...arm, ...updates } : arm) 
          };
        } else if (type === 'heart' && m.heart) {
          return { ...m, heart: { ...m.heart, ...updates } };
        }
        return m;
      }),
    }));
    toast.success('Configuration updated');
  };

  const handleValidate = async () => {
    const isTeamMode = agentConfig.leg?.id === 'team';
    
    // Different validation for team mode vs single agent mode
    if (isTeamMode) {
      // Team mode: need leg and at least one team member with a head
      const teamMembers = agentConfig.teamMembers || [];
      const hasReadyMember = teamMembers.some(m => m.head);
      
      if (!agentConfig.leg) {
        toast.error('Execution Mode is required');
        return;
      }
      if (teamMembers.length === 0) {
        toast.error('At least one team member is required');
        return;
      }
      if (!hasReadyMember) {
        toast.error('At least one team member needs a Head (LLM)');
        return;
      }
    } else {
      if (!agentConfig.head || !agentConfig.leg) {
        toast.error('Head and Execution Mode are required');
        return;
      }
    }

    setIsValidating(true);
    addLog(`[${new Date().toISOString()}] Validating ${isTeamMode ? 'team' : 'blueprint'}...`);

    try {
      const blueprint = convertToBlueprint(agentConfig);
      const result = await validateBlueprint(blueprint, false);

      if (result.valid) {
        addLog(`[${new Date().toISOString()}] ✓ Blueprint is valid`);
        toast.success('Blueprint is valid!');
      } else {
        addLog(`[${new Date().toISOString()}] ✗ Blueprint validation failed`);
        result.errors.forEach(error => {
          addLog(`  - ${error.field}: ${error.message}`);
        });
        // Show first error in toast for visibility
        const firstError = result.errors[0];
        toast.error(`Validation failed: ${firstError?.field}: ${firstError?.message}`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      addLog(`[${new Date().toISOString()}] ERROR: ${errorMessage}`);
      toast.error(`Validation error: ${errorMessage}`);
    } finally {
      setIsValidating(false);
    }
  };

  const handleExport = () => {
    const blueprint = convertToBlueprint(agentConfig);
    console.log('Agent Blueprint:', JSON.stringify(blueprint, null, 2));
    addLog(`[${new Date().toISOString()}] Blueprint exported to console`);
    toast.success('Blueprint exported to console');
  };

  const handleDeploy = async () => {
    const isTeamMode = agentConfig.leg?.id === 'team';
    
    // Different validation for team mode vs single agent mode
    if (isTeamMode) {
      // Team mode: need leg and at least one team member with a head
      const teamMembers = agentConfig.teamMembers || [];
      const hasReadyMember = teamMembers.some(m => m.head);
      
      if (!agentConfig.leg) {
        toast.error('Execution Mode is required');
        return;
      }
      if (teamMembers.length === 0) {
        toast.error('At least one team member is required');
        return;
      }
      if (!hasReadyMember) {
        toast.error('At least one team member needs a Head (LLM)');
        return;
      }
    } else {
      // Single agent mode: need head and leg
      if (!agentConfig.head || !agentConfig.leg) {
        toast.error('Head and Execution Mode are required');
        return;
      }
    }

    setIsDeploying(true);
    addLog(`[${new Date().toISOString()}] Deploying ${isTeamMode ? 'team' : 'agent'}...`);

    try {
      const blueprint = convertToBlueprint(agentConfig);
      const result = await validateBlueprint(blueprint, true);

      if (result.valid) {
        setDeployedBlueprint(result.normalized_blueprint || blueprint);
        addLog(`[${new Date().toISOString()}] ✓ Agent deployed successfully`);
        if (result.blueprint_id) {
          addLog(`[${new Date().toISOString()}] Blueprint ID: ${result.blueprint_id}`);
        }
        toast.success('Agent deployed! You can now test it in the chat panel.');
      } else {
        addLog(`[${new Date().toISOString()}] ✗ Deployment failed - validation errors`);
        result.errors.forEach(error => {
          addLog(`  - ${error.field}: ${error.message}`);
        });
        // Show first error in toast for visibility
        const firstError = result.errors[0];
        toast.error(`Deployment failed: ${firstError?.field}: ${firstError?.message}`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      addLog(`[${new Date().toISOString()}] ERROR: ${errorMessage}`);
      toast.error(`Deployment error: ${errorMessage}`);
    } finally {
      setIsDeploying(false);
    }
  };

  const handleSaveBlueprint = () => {
    if (!isAuthenticated) {
      toast.error('Please log in to save blueprints');
      setShowAuthDialog(true);
      return;
    }
    setShowSaveDialog(true);
  };

  const handleOpenSaveAgentDialog = () => {
    if (!isAuthenticated) {
      toast.error('Please log in to save agents');
      setShowAuthDialog(true);
      return;
    }
    setShowSaveAgentDialog(true);
  };

  const handleSaveAgent = async (name: string, description: string) => {
    if (!token) return;
    
    setIsSavingAgent(true);
    addLog(`[${new Date().toISOString()}] Saving agent "${name}"...`);
    
    try {
      const blueprint = convertToBlueprint(agentConfig);
      blueprint.name = name;
      blueprint.description = description;
      
      // Use the agent API on the backend to save the blueprint
      const response = await fetch(`${API_BASE_URL}/api/agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          description,
          blueprint_data: blueprint,
          is_public: false,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save agent');
      }
      
      const data = await response.json();
      const savedAgent = data.agent;
      setCurrentBlueprintId(savedAgent.id);
      addLog(`[${new Date().toISOString()}] ✓ Agent saved successfully (ID: ${savedAgent.id})`);
      toast.success(`Agent "${name}" saved successfully!`);
      setShowSaveAgentDialog(false);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      addLog(`[${new Date().toISOString()}] ERROR: ${errorMessage}`);
      toast.error(`Failed to save agent: ${errorMessage}`);
    } finally {
      setIsSavingAgent(false);
    }
  };

  const handleLoadBlueprint = async (id: string) => {
    if (!token) return;

    try {
      const blueprint = await getBlueprint(token, id);
      // TODO: Convert blueprint data back to AgentConfiguration format
      setCurrentBlueprintId(id);
      toast.success('Blueprint loaded');
      setShowBlueprintList(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load blueprint';
      toast.error(message);
    }
  };

  const handleAgentChange = (blueprintId: string, sessionId: string) => {
    setCurrentBlueprintId(blueprintId);
    setCurrentSessionId(sessionId);
    // TODO: Load blueprint and deploy it
  };

  const addLog = (log: string) => {
    setLogs(prev => [...prev, log]);
  };

  const clearLogs = () => {
    setLogs([]);
    // Also clear backend logs in LogsPanel
    clearLogsBackendRef.current?.();
    toast.info('Logs cleared');
  };

  const clearAll = () => {
    // Clear logs
    setLogs([]);
    clearLogsBackendRef.current?.();
    // Clear chat/test agent panel
    clearChatRef.current?.();
    setCurrentSessionId(undefined);
    // Hide Test Agent and Logs panels by clearing deployed blueprint
    setDeployedBlueprint(undefined);
    toast.info('Cleared');
  };

  const totalParts = [
    agentConfig.head,
    ...agentConfig.arms,
    agentConfig.heart,
    agentConfig.leg,
    agentConfig.spine,
  ].filter(Boolean).length;

  // Handler for using a blueprint from the marketplace
  const handleUseMarketplaceBlueprint = (config: AgentConfiguration) => {
    setAgentConfig(config);
    setCurrentBlueprintId(undefined);
    setShowMarketplace(false);
  };

  // Handler for loading a blueprint from My Agents
  const handleUseMyAgentBlueprint = (blueprintData: any) => {
    // Convert backend blueprint format to frontend AgentConfiguration format
    const config: AgentConfiguration = {
      arms: [],
    };
    
    // Convert head
    if (blueprintData.head) {
      const head = blueprintData.head;
      let headId = 'gpt4o-mini';
      let headName = 'OpenAI GPT-4o-mini';
      
      // Map backend provider/model to frontend head ID
      if (head.provider === 'openai') {
        if (head.model?.includes('gpt-4')) {
          headId = 'gpt4o-mini';
          headName = 'OpenAI GPT-4o-mini';
        } else {
          headId = 'gpt4o-mini';
          headName = 'OpenAI GPT-4o-mini';
        }
      } else if (head.provider === 'anthropic') {
        headId = 'claude-haiku';
        headName = 'Claude 3 Haiku';
      }
      
      config.head = {
        id: headId,
        instanceId: `head-${Date.now()}`,
        type: 'head',
        name: headName,
        category: 'Head',
        color: '#10a37f',
        position: { x: 0, y: 0 },
        config: {
          systemPrompt: head.system_prompt || 'You are a helpful AI assistant.',
          temperature: head.temperature || 0.7,
          maxTokens: head.max_tokens || 1000,
        },
      };
    }
    
    // Convert arms (tools)
    if (blueprintData.arms && Array.isArray(blueprintData.arms)) {
      config.arms = blueprintData.arms.map((arm: any, index: number) => {
        let armId = 'tavily-search';
        let armName = 'Tavily Search';
        let armColor = '#8b5cf6';
        let armConfig: any = {};
        
        if (arm.type === 'tavily_search') {
          armId = 'tavily-search';
          armName = 'Tavily Search';
          armColor = '#8b5cf6';
          armConfig = {
            maxResults: arm.config?.max_results || 5,
            searchDepth: arm.config?.search_depth || 'basic',
          };
        } else if (arm.type === 'http_tool') {
          armId = 'http-tool';
          armName = 'HTTP Tool';
          armColor = '#06b6d4';
          armConfig = {
            name: arm.config?.name || 'HTTP Request',
            description: arm.config?.description || 'Make HTTP requests',
            baseUrl: arm.config?.base_url || '',
            defaultHeaders: arm.config?.default_headers || {},
            timeout: arm.config?.timeout || 30,
          };
        } else if (arm.type === 'mcp_tool') {
          armId = 'mcp-tool';
          armName = 'MCP Tool';
          armColor = '#14b8a6';
          armConfig = {
            transportType: arm.config?.transport_type || 'sse',
            serverLabel: arm.config?.server_label || '',
            serverUrl: arm.config?.server_url || '',
            allowedTools: arm.config?.allowed_tools || [],
            requireApproval: arm.config?.require_approval || 'never',
            apiToken: arm.config?.api_token || '',
            authHeader: arm.config?.auth_header || 'Authorization',
          };
        }
        
        return {
          id: armId,
          instanceId: `arm-${Date.now()}-${index}`,
          type: 'arm' as const,
          name: armName,
          category: 'Tool',
          color: armColor,
          position: { x: 0, y: 0 },
          config: armConfig,
        };
      });
    }
    
    // Convert legs (execution mode)
    const legs = blueprintData.legs || blueprintData.leg;
    if (legs) {
      let legId = 'single-agent';
      let legName = 'Single Agent';
      
      if (legs.execution_mode === 'single_agent') {
        legId = 'single-agent';
        legName = 'Single Agent';
      } else if (legs.execution_mode === 'workflow') {
        legId = 'workflow';
        legName = 'Workflow';
      } else if (legs.execution_mode === 'team') {
        legId = 'team';
        legName = 'Team';
      }
      
      config.leg = {
        id: legId,
        instanceId: `leg-${Date.now()}`,
        type: 'leg',
        name: legName,
        category: 'Execution',
        color: '#6366f1',
        position: { x: 0, y: 0 },
        config: {},
      };
    }
    
    // Convert heart (memory)
    if (blueprintData.heart) {
      const heart = blueprintData.heart;
      config.heart = {
        id: 'convo-memory',
        instanceId: `heart-${Date.now()}`,
        type: 'heart',
        name: 'Convo Memory',
        category: 'Memory',
        color: '#ef4444',
        position: { x: 0, y: 0 },
        config: {
          maxMessages: heart.history_length || 10,
        },
      };
    }
    
    // Convert spine (guardrails)
    if (blueprintData.spine) {
      const spine = blueprintData.spine;
      config.spine = {
        id: 'max-tool-calls',
        instanceId: `spine-${Date.now()}`,
        type: 'spine',
        name: 'Max Tool Calls',
        category: 'Guardrail',
        color: '#78716c',
        position: { x: 0, y: 0 },
        config: {
          maxCalls: spine.max_tool_calls || 10,
        },
      };
    }
    
    setAgentConfig(config);
    setCurrentBlueprintId(undefined);
    setShowBlueprintList(false);
    toast.success('Agent loaded successfully');
  };

  // If settings page is open, show full-page settings
  if (showSettings) {
    return (
      <DndProvider backend={HTML5Backend}>
        <SettingsPage 
          onBack={() => setShowSettings(false)}
          onOpenMarketplace={() => {
            setShowSettings(false);
            setShowMarketplace(true);
          }}
          onOpenMyAgents={() => {
            setShowSettings(false);
            setShowBlueprintList(true);
          }}
          onOpenAuthDialog={() => setShowAuthDialog(true)}
        />
        <Toaster />
        <AuthDialog
          open={showAuthDialog}
          onOpenChange={setShowAuthDialog}
        />
        <MyAgentsDialog
          open={showBlueprintList}
          onOpenChange={setShowBlueprintList}
          onLoad={handleLoadBlueprint}
          onUseBlueprint={(blueprintData) => {
            handleUseMyAgentBlueprint(blueprintData);
            setShowSettings(false);
            setShowBlueprintList(false);
          }}
        />
      </DndProvider>
    );
  }

  // If marketplace is open, show full-page marketplace
  if (showMarketplace) {
    return (
      <DndProvider backend={HTML5Backend}>
        <div className="h-screen w-screen flex flex-col bg-gray-950 text-white overflow-hidden">
          <Toaster />
          
          {/* Full-page Marketplace - has its own top bar */}
          <Marketplace
            onBack={() => setShowMarketplace(false)}
            onUseBlueprint={handleUseMarketplaceBlueprint}
            isAuthenticated={isAuthenticated}
            onOpenMyAgents={() => setShowBlueprintList(true)}
            onOpenSettings={() => setShowSettings(true)}
            onOpenAuthDialog={() => setShowAuthDialog(true)}
          />
        </div>

        {/* Dialogs */}
        <AuthDialog
          open={showAuthDialog}
          onOpenChange={setShowAuthDialog}
        />
        <APIKeyManager
          open={showApiKeyManager}
          onOpenChange={setShowApiKeyManager}
        />
        <MyAgentsDialog
          open={showBlueprintList}
          onOpenChange={setShowBlueprintList}
          onLoad={handleLoadBlueprint}
        />
      </DndProvider>
    );
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen w-screen flex flex-col bg-gray-950 text-white overflow-hidden">
        <Toaster />
        
        {/* Top Bar */}
        <TopBar
          isAuthenticated={isAuthenticated}
          onOpenMarketplace={() => setShowMarketplace(true)}
          onOpenMyAgents={() => setShowBlueprintList(true)}
          onOpenSettings={() => setShowSettings(true)}
          onOpenAuthDialog={() => setShowAuthDialog(true)}
        />

        {/* Main content */}
        <ResizablePanelGroup direction="horizontal" className="flex-1">
          {/* Left Sidebar - Body Parts Library - 1/4 (25%) */}
          <ResizablePanel 
            defaultSize={
              agentConfig.leg?.id === 'team' 
                ? 15 
                : deployedBlueprint ? 15 : 25
            } 
            minSize={10} 
            maxSize={30}
          >
            <BodyPartLibrary />
          </ResizablePanel>
          
          <ResizableHandle withHandle />

          {/* Center - Canvas with Frankenstein Agent - 2/4 (50%) */}
          <ResizablePanel 
            defaultSize={
              agentConfig.leg?.id === 'team' 
                ? 60 
                : deployedBlueprint ? 25 : 50
            } 
            minSize={30}
          >
            <Canvas
              config={agentConfig}
              onAddNode={handleAddNode}
              onRemoveNode={handleRemoveNode}
              onUpdateNode={handleUpdateNode}
            />
          </ResizablePanel>

          <ResizableHandle withHandle />

          {/* Right Sidebar - Configuration Panel - 1/4 (25%) */}
          <ResizablePanel 
            defaultSize={
              agentConfig.leg?.id === 'team' 
                ? 25 
                : deployedBlueprint ? 20 : 25
            } 
            minSize={15} 
            maxSize={40}
          >
            <AgentPanel
              config={agentConfig}
              onRemovePart={handleRemoveNode}
              onAddNode={handleAddNode}
              onClearAll={handleClearAll}
              onValidate={handleValidate}
              onExport={handleExport}
              onDeploy={handleDeploy}
              onSaveAgent={handleOpenSaveAgentDialog}
              isValidating={isValidating}
              isDeploying={isDeploying}
              isSaving={isSavingAgent}
              // Team mode props
              onAddTeamMember={handleAddTeamMember}
              onRemoveTeamMember={handleRemoveTeamMember}
              onUpdateTeamMember={handleUpdateTeamMember}
              onAddNodeToTeamMember={handleAddNodeToTeamMember}
              onRemoveNodeFromTeamMember={handleRemoveNodeFromTeamMember}
              onUpdateNodeInTeamMember={handleUpdateNodeInTeamMember}
            />
          </ResizablePanel>

          {deployedBlueprint && (
            <>
              <ResizableHandle withHandle />

              {/* Chat Panel */}
              <ResizablePanel defaultSize={22} minSize={15} maxSize={35}>
                <ChatPanel
                  blueprint={deployedBlueprint}
                  blueprintName={agentConfig.head?.name}
                  onLogUpdate={addLog}
                  onSessionIdChange={setCurrentSessionId}
                  onClearRef={(fn) => { clearChatRef.current = fn; }}
                />
              </ResizablePanel>

              <ResizableHandle withHandle />

              {/* Logs Panel */}
              <ResizablePanel defaultSize={18} minSize={12} maxSize={30}>
                <LogsPanel
                  logs={logs}
                  onClearLogs={clearAll}
                  sessionId={currentSessionId}
                  onClearRef={(fn) => { clearLogsBackendRef.current = fn; }}
                />
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>

        {/* Footer */}
        <Footer />
      </div>

      {/* Dialogs */}
      <AuthDialog
        open={showAuthDialog}
        onOpenChange={setShowAuthDialog}
      />
      <ResetPasswordDialog
        open={showResetPassword}
        token={resetPasswordToken || ''}
        onSuccess={() => {
          setShowResetPassword(false);
          setResetPasswordToken(null);
          setShowAuthDialog(true);
        }}
        onClose={() => {
          setShowResetPassword(false);
          setResetPasswordToken(null);
        }}
      />
      <APIKeyManager
        open={showApiKeyManager}
        onOpenChange={setShowApiKeyManager}
      />
      <SaveBlueprintDialog
        open={showSaveDialog}
        onOpenChange={setShowSaveDialog}
        blueprintData={convertToBlueprint(agentConfig)}
        existingBlueprintId={currentBlueprintId}
        onSuccess={() => {
          toast.success('Blueprint saved successfully');
        }}
      />
      <MyAgentsDialog
        open={showBlueprintList}
        onOpenChange={setShowBlueprintList}
        onLoad={handleLoadBlueprint}
        onUseBlueprint={handleUseMyAgentBlueprint}
      />
      <SaveAgentDialog
        open={showSaveAgentDialog}
        onOpenChange={setShowSaveAgentDialog}
        config={agentConfig}
        onSave={handleSaveAgent}
        isSaving={isSavingAgent}
      />
    </DndProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
