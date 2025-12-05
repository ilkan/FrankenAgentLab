import { useState, useEffect } from 'react';
import { Tabs, TabsContent } from '../ui/tabs';
import { Footer } from '../Footer';
import { TopBar } from '../TopBar';
import { useAuth as useAuthContext } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import {
  getProfile,
  getUsageStats,
  getExecutionLogs,
  getAPIKeys,
  Profile,
  UsageStats,
  QuotaInfo,
  ExecutionLog,
  APIKey,
} from '../../utils/agentApi';
import {
  ProfileTab,
  UsageTab,
  CreditsTab,
  APIKeysTab,
  SettingsTabNavigation,
} from './settings';

interface SettingsPageProps {
  onBack: () => void;
  onOpenMarketplace?: () => void;
  onOpenMyAgents?: () => void;
  onOpenAuthDialog?: () => void;
}

interface CreditTransaction {
  id: string;
  date: string;
  action: string;
  description: string;
  amount: number;
  type: 'credit' | 'debit';
}

export function SettingsPage({ 
  onBack, 
  onOpenMarketplace,
  onOpenMyAgents,
  onOpenAuthDialog 
}: SettingsPageProps) {
  const { user, token, isAuthenticated, refreshUser } = useAuthContext();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [quotaInfo, setQuotaInfo] = useState<QuotaInfo | null>(null);
  const [executionLogs, setExecutionLogs] = useState<ExecutionLog[]>([]);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile');

  const tokenUsagePercent = quotaInfo ? ((quotaInfo.used / quotaInfo.quota) * 100) : (user ? (user.token_used / user.token_quota) * 100 : 0);
  const remainingTokens = quotaInfo ? quotaInfo.remaining : (user ? user.token_quota - user.token_used : 0);
  const totalTokens = quotaInfo ? quotaInfo.quota : (user?.token_quota || 0);
  const usedTokens = quotaInfo ? quotaInfo.used : (user?.token_used || 0);

  // Fetch profile and usage data
  useEffect(() => {
    const fetchData = async () => {
      if (!token) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const profileData = await getProfile(token);
        setProfile(profileData);

        const { usage, quota } = await getUsageStats(token);
        setUsageStats(usage);
        setQuotaInfo(quota);

        const logs = await getExecutionLogs(token, { limit: 20 });
        setExecutionLogs(logs);

        // Convert logs to transaction format
        const txns: CreditTransaction[] = logs.map(log => ({
          id: log.id,
          date: new Date(log.created_at).toLocaleDateString(),
          action: 'Agent execution',
          description: `${log.model} - ${log.status}`,
          amount: -log.total_tokens,
          type: 'debit' as const,
        }));
        setTransactions(txns);

        const keys = await getAPIKeys(token);
        setApiKeys(keys);
      } catch (error) {
        console.error('Failed to fetch settings data:', error);
        toast.error('Failed to load settings data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [token]);

  // Refresh API keys when apikeys tab is selected
  useEffect(() => {
    const refreshApiKeys = async () => {
      if (activeTab === 'apikeys' && token) {
        try {
          const keys = await getAPIKeys(token);
          setApiKeys(keys);
        } catch (error) {
          console.error('Failed to refresh API keys:', error);
        }
      }
    };

    refreshApiKeys();
  }, [activeTab, token]);

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-950 text-white overflow-hidden">
      <TopBar
        subtitle="Account Settings"
        isAuthenticated={isAuthenticated}
        onNavigateHome={onBack}
        onOpenMarketplace={onOpenMarketplace}
        onOpenMyAgents={onOpenMyAgents}
        onOpenSettings={() => {}}
        onOpenAuthDialog={onOpenAuthDialog}
      />

      <div className="flex-1 overflow-hidden p-4 md:p-6">
        <div className="max-w-6xl mx-auto h-full">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <SettingsTabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

            <TabsContent value="profile" className="flex-1 overflow-auto mt-0 scrollbar-hide">
              <ProfileTab
                profile={profile}
                token={token}
                onProfileUpdate={setProfile}
                onRefreshUser={refreshUser}
              />
            </TabsContent>

            <TabsContent value="usage" className="flex-1 overflow-auto mt-0 scrollbar-hide">
              <UsageTab
                executionLogs={executionLogs}
                isLoading={isLoading}
              />
            </TabsContent>

            <TabsContent value="credits" className="flex-1 overflow-auto mt-0 scrollbar-hide">
              <CreditsTab
                usedTokens={usedTokens}
                totalTokens={totalTokens}
                remainingTokens={remainingTokens}
                tokenUsagePercent={tokenUsagePercent}
              />
            </TabsContent>

            <TabsContent value="apikeys" className="flex-1 overflow-auto mt-0 scrollbar-hide">
              <APIKeysTab
                apiKeys={apiKeys}
                isLoading={isLoading}
                token={token}
                onKeysUpdate={setApiKeys}
              />
            </TabsContent>

          </Tabs>
        </div>
      </div>

      <Footer />
    </div>
  );
}
