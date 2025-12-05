/**
 * API client for session management
 */

import { API_BASE_URL } from '../config';

export interface Session {
  id: string;
  blueprint_id: string;
  blueprint_name: string;
  message_count: number;
  last_message_preview?: string;
  last_message_at?: string;
  created_at: string;
}

/**
 * Get all sessions for the current user
 */
export async function getUserSessions(token: string): Promise<Session[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to fetch sessions');
  }

  const data = await response.json();
  return data.sessions || [];
}

/**
 * Create a new session
 */
export async function createSession(token: string, blueprintId: string): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      blueprint_id: blueprintId,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to create session');
  }

  return response.json();
}

/**
 * Get session history
 */
export async function getSessionHistory(token: string, sessionId: string): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/history`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to fetch session history');
  }

  const data = await response.json();
  return data.messages || [];
}
