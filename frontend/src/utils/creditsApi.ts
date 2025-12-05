/**
 * Credits API - Handles all credit and usage tracking API calls
 */

import { API_BASE_URL } from '../config';

export interface CreditBalance {
  credit_balance: number;
  monthly_limit: number;
  credits_used_this_month: number;
  reset_date: string | null;
  total_operations: number;
}

export interface CreditTransaction {
  id: string;
  transaction_type: 'debit' | 'credit' | 'refund';
  amount: number;
  balance_after: number;
  description: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface UsageLog {
  id: string;
  usage_type: 'llm_call' | 'tool_call' | 'agent_execution';
  component_type: string | null;
  credits_used: number;
  token_count: number | null;
  model_name: string | null;
  details: Record<string, any>;
  created_at: string;
}

export interface CreditCosts {
  llm_base: number;
  llm_per_1k_tokens: number;
  mcp_tool: number;
  http_tool: number;
  tavily_search: number;
  python_eval: number;
  single_agent: number;
  workflow: number;
  team: number;
  guardrail_check: number;
}

/**
 * Get current credit balance and usage summary
 */
export async function getCreditBalance(token: string): Promise<CreditBalance> {
  const response = await fetch(`${API_BASE_URL}/api/credits/balance`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get credit transaction history with pagination
 */
export async function getCreditTransactions(
  token: string,
  limit: number = 50,
  offset: number = 0
): Promise<CreditTransaction[]> {
  const url = new URL(`${API_BASE_URL}/api/credits/transactions`);
  url.searchParams.append('limit', limit.toString());
  url.searchParams.append('offset', offset.toString());

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get usage logs with optional filtering
 */
export async function getUsageLogs(
  token: string,
  limit: number = 50,
  offset: number = 0,
  usageType?: string
): Promise<UsageLog[]> {
  const url = new URL(`${API_BASE_URL}/api/credits/usage`);
  url.searchParams.append('limit', limit.toString());
  url.searchParams.append('offset', offset.toString());
  if (usageType) {
    url.searchParams.append('usage_type', usageType);
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get credit costs configuration
 */
export async function getCreditCosts(token: string): Promise<CreditCosts> {
  const response = await fetch(`${API_BASE_URL}/api/credits/costs`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Format transaction for display
 */
export function formatTransaction(transaction: CreditTransaction) {
  return {
    id: transaction.id,
    date: new Date(transaction.created_at).toLocaleDateString(),
    description: transaction.description,
    amount: transaction.amount,
    type: transaction.transaction_type === 'debit' ? 'usage' : 
          transaction.transaction_type === 'credit' ? 'purchase' : 'refund',
    balance: transaction.balance_after,
  };
}

/**
 * Format usage log for display
 */
export function formatUsageLog(log: UsageLog) {
  return {
    id: log.id,
    type: log.usage_type,
    component: log.component_type || 'N/A',
    credits: log.credits_used,
    tokens: log.token_count || 0,
    model: log.model_name || 'N/A',
    timestamp: new Date(log.created_at).toLocaleString(),
    details: log.details,
  };
}
