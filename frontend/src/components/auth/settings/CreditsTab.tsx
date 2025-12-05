import React, { useState, useEffect } from 'react';
import { Button } from '../../ui/button';
import { Card } from '../../ui/card';
import { ScrollArea } from '../../ui/scroll-area';
import {
  CreditCard,
  TrendingUp,
  DollarSign,
  Download,
  Calendar,
  Zap,
  Crown,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { 
  getCreditBalance, 
  getCreditTransactions, 
  formatTransaction,
  type CreditBalance,
  type CreditTransaction as ApiCreditTransaction
} from '../../../utils/creditsApi';
import { useAuth } from '../../../contexts/AuthContext';

interface CreditTransaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  type: 'usage' | 'purchase' | 'refund';
  balance?: number;
}

interface CreditsTabProps {
  // These props are now optional as we fetch from API
  usedTokens?: number;
  totalTokens?: number;
  remainingTokens?: number;
  tokenUsagePercent?: number;
}

export function CreditsTab({
  usedTokens: propUsedTokens,
  totalTokens: propTotalTokens,
  remainingTokens: propRemainingTokens,
  tokenUsagePercent: propTokenUsagePercent,
}: CreditsTabProps) {
  const { token } = useAuth();
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const formatNumber = (num: number) => num.toLocaleString();

  // Fetch credit data from API
  useEffect(() => {
    async function fetchCreditData() {
      if (!token) return;
      
      setIsLoading(true);
      setError(null);
      
      try {
        // Fetch balance
        const balanceData = await getCreditBalance(token);
        setBalance(balanceData);
        
        // Fetch transactions
        const txData = await getCreditTransactions(token, 50);
        const formattedTx = txData.map(formatTransaction);
        setTransactions(formattedTx);
      } catch (err: any) {
        console.error('Failed to fetch credit data:', err);
        setError(err.message || 'Failed to load credit data');
      } finally {
        setIsLoading(false);
      }
    }
    
    fetchCreditData();
  }, [token]);

  // Use API data if available, otherwise fall back to props
  const usedTokens = balance?.credits_used_this_month ?? propUsedTokens ?? 0;
  const totalTokens = balance?.monthly_limit ?? propTotalTokens ?? 1000;
  const remainingTokens = balance?.credit_balance ?? propRemainingTokens ?? 1000;
  const tokenUsagePercent = balance 
    ? (balance.credits_used_this_month / balance.monthly_limit) * 100 
    : propTokenUsagePercent ?? 0;

  const handleRefresh = async () => {
    if (!token) return;
    
    setIsLoading(true);
    try {
      const balanceData = await getCreditBalance(token);
      setBalance(balanceData);
      
      const txData = await getCreditTransactions(token, 50);
      const formattedTx = txData.map(formatTransaction);
      setTransactions(formattedTx);
    } catch (err: any) {
      console.error('Failed to refresh credit data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = () => {
    // Export transactions to CSV
    const csv = [
      ['Date', 'Description', 'Amount', 'Type', 'Balance'].join(','),
      ...transactions.map(tx => 
        [tx.date, `"${tx.description}"`, tx.amount, tx.type, tx.balance || ''].join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `credit-transactions-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (isLoading && !balance) {
    return (
      <div className="max-w-5xl mx-auto flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-2" />
          <p className="text-gray-400">Loading credit data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto">
        <Card className="p-6 bg-red-900/20 border-red-800">
          <p className="text-red-400">Error loading credit data: {error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 3fr', gap: '24px' }}>
        {/* Left Column - Credit Balance & Pricing */}
        <div className="space-y-6">
          {/* Credit Balance */}
          <Card className="p-6 bg-gray-900 border-gray-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-medium text-gray-100">Credit Balance</h3>
            <p className="text-sm text-gray-400">
              {balance?.reset_date 
                ? `Resets ${new Date(balance.reset_date).toLocaleDateString()}`
                : 'Your available credits for AI agent operations'
              }
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
          <Button 
            variant="outline"
            size="sm"
            className="gap-2 transition-colors"
            style={{ 
              backgroundColor: '#14532d', 
              color: '#4ade80', 
              borderColor: '#166534' 
            }}
            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => { 
              e.currentTarget.style.backgroundColor = '#15803d'; 
              e.currentTarget.style.color = '#86efac'; 
              e.currentTarget.style.borderColor = '#16a34a'; 
            }}
            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => { 
              e.currentTarget.style.backgroundColor = '#14532d'; 
              e.currentTarget.style.color = '#4ade80'; 
              e.currentTarget.style.borderColor = '#166534'; 
            }}
          >
            <CreditCard className="w-4 h-4" />
            Buy Credits
          </Button>
        </div>

        <div className="mb-4">
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-4xl font-bold text-gray-100">{formatNumber(remainingTokens)}</span>
            <span className="text-lg text-gray-400">/ {formatNumber(totalTokens)} credits</span>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Usage</span>
            <span className="text-sm text-gray-400">{tokenUsagePercent.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-300"
              style={{ 
                width: `${Math.min(tokenUsagePercent, 100)}%`,
                background: tokenUsagePercent < 50 
                  ? 'linear-gradient(to right, #10b981, #059669)' // green
                  : tokenUsagePercent < 80 
                  ? 'linear-gradient(to right, #eab308, #f97316)' // yellow to orange
                  : 'linear-gradient(to right, #ef4444, #dc2626)' // red
              }} 
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-900/50 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 !text-blue-400" style={{ color: '#60a5fa' }} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Purchased</p>
              <p className="text-sm font-medium text-gray-100">{formatNumber(totalTokens)} credits</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-900/50 flex items-center justify-center">
              <DollarSign className="w-5 h-5 !text-orange-400" style={{ color: '#fb923c' }} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Spent</p>
              <p className="text-sm font-medium text-gray-100">{formatNumber(usedTokens)} credits</p>
            </div>
          </div>
        </div>
      </Card>

          {/* Upgrade to Pro */}
          <Card className="p-6 bg-gray-900 border-purple-800/50" style={{ background: 'linear-gradient(to bottom right, rgba(88, 28, 135, 0.15), rgba(147, 51, 234, 0.1), rgba(219, 39, 119, 0.15))' }}>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-purple-600/20 flex items-center justify-center flex-shrink-0">
                <Crown className="w-6 h-6 !text-purple-400" style={{ color: '#c084fc' }} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg font-semibold text-gray-100">Upgrade to Pro</h3>
                  <span className="px-2 py-0.5 bg-purple-600/80 text-white text-xs rounded font-medium">Coming Soon</span>
                </div>
                <p className="text-sm text-gray-400 mb-4">
                  Unlock premium features when we launch
                </p>
                
                <div className="space-y-3 mb-4">
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 !text-purple-400 flex-shrink-0 mt-0.5" style={{ color: '#c084fc' }} />
                    <div>
                      <p className="text-sm font-medium text-gray-200">Unlimited AI Agent Executions</p>
                      <p className="text-xs text-gray-500">No credit limits on agent runs</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 !text-purple-400 flex-shrink-0 mt-0.5" style={{ color: '#c084fc' }} />
                    <div>
                      <p className="text-sm font-medium text-gray-200">Priority Support</p>
                      <p className="text-xs text-gray-500">Get help from our team faster</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 !text-purple-400 flex-shrink-0 mt-0.5" style={{ color: '#c084fc' }} />
                    <div>
                      <p className="text-sm font-medium text-gray-200">Advanced Analytics</p>
                      <p className="text-xs text-gray-500">Deep insights into agent performance</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 !text-purple-400 flex-shrink-0 mt-0.5" style={{ color: '#c084fc' }} />
                    <div>
                      <p className="text-sm font-medium text-gray-200">Team Collaboration</p>
                      <p className="text-xs text-gray-500">Share and collaborate with your team</p>
                    </div>
                  </div>
                </div>

                <div 
                  className="flex items-start gap-3 p-3 border border-yellow-600/40 rounded-lg mb-4"
                  style={{ backgroundColor: 'rgba(113, 63, 18, 0.3)' }}
                >
                  <Sparkles className="w-5 h-5 !text-yellow-400 flex-shrink-0 mt-0.5" style={{ color: '#facc15' }} />
                  <div>
                    <p className="text-sm font-medium mb-1" style={{ color: '#fef08a' }}>Currently in Beta</p>
                    <p className="text-xs" style={{ color: '#fef3c7' }}>
                      Frankenstein AI is currently in beta. Pro plans will be available when we launch to the public. As a beta user, you'll get exclusive early access and special pricing!
                    </p>
                  </div>
                </div>

                <Button
                  disabled
                  className="w-full cursor-not-allowed"
                  style={{ 
                    backgroundColor: 'rgba(147, 51, 234, 0.3)', 
                    color: '#d8b4fe',
                    opacity: 0.7
                  }}
                >
                  <Crown className="w-4 h-4 mr-2" style={{ color: '#d8b4fe' }} />
                  Available After Launch
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column - Transaction History */}
        <Card className="bg-gray-900 border-gray-800">
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-100">
            Transaction History
            {transactions.length > 0 && (
              <span className="ml-2 text-sm text-gray-500">({transactions.length})</span>
            )}
          </h3>
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-2 bg-gray-950 border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100"
            onClick={handleExport}
            disabled={transactions.length === 0}
          >
            <Download className="w-4 h-4" />
            Export
          </Button>
        </div>
        
        <ScrollArea className="h-[300px] scrollbar-hide">
          <div className="p-4 space-y-3">
            {transactions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CreditCard className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No transactions yet</p>
                <p className="text-sm">Start using agents to see your credit usage here</p>
              </div>
            ) : (
              transactions.map((tx) => (
              <div 
                key={tx.id} 
                className="p-4 bg-gray-950 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      tx.type === 'purchase' ? 'bg-green-900/50' :
                      tx.type === 'refund' ? 'bg-blue-900/50' :
                      'bg-yellow-900/50'
                    }`}>
                      {tx.type === 'purchase' ? (
                        <CreditCard className="w-5 h-5 !text-green-400" style={{ color: '#4ade80' }} />
                      ) : tx.type === 'refund' ? (
                        <TrendingUp className="w-5 h-5 !text-blue-400" style={{ color: '#60a5fa' }} />
                      ) : (
                        <Zap className="w-5 h-5 !text-yellow-400" style={{ color: '#facc15' }} />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-100">{tx.description}</p>
                      <div className="flex items-center gap-1.5 mt-1 text-xs text-gray-500">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(tx.date).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <span className={`text-sm font-medium ${
                    tx.amount > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {tx.amount > 0 ? '+' : ''}{formatNumber(tx.amount)}
                  </span>
                </div>
              </div>
            ))
            )}
          </div>
        </ScrollArea>
      </Card>
      </div>
    </div>
  );
}
