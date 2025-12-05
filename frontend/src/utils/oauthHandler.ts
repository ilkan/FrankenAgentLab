/**
 * OAuth callback handler utility
 */

import { API_BASE_URL } from '../config';

// The redirect URI must match exactly what's configured in the backend
// and what was used when generating the OAuth authorization URL
export function getOAuthRedirectUri(): string {
  // For local development, use the backend callback URL
  // The backend will redirect back to the frontend after receiving the code
  return `${API_BASE_URL}/api/auth/callback`;
}

export async function handleOAuthCallback(): Promise<{ success: boolean; token?: string; error?: string }> {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');
  const error = params.get('error');
  const provider = sessionStorage.getItem('oauth_provider') || 'google';

  // Check for OAuth errors
  if (error) {
    return { success: false, error: `OAuth error: ${error}` };
  }

  // Check if this is an OAuth callback
  if (!code) {
    return { success: false };
  }

  // Verify state for CSRF protection
  const storedState = sessionStorage.getItem('oauth_state');
  if (state !== storedState) {
    return { success: false, error: 'Invalid OAuth state. Please try again.' };
  }

  // Clear stored state and provider
  sessionStorage.removeItem('oauth_state');
  sessionStorage.removeItem('oauth_provider');

  try {
    // Exchange code for token - use the same redirect_uri that was used for authorization
    const response = await fetch(`${API_BASE_URL}/api/auth/oauth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider,
        code,
        redirect_uri: getOAuthRedirectUri(),
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return { success: false, error: errorData.detail || 'OAuth login failed' };
    }

    const data = await response.json();
    
    // Clear OAuth params from URL
    window.history.replaceState({}, document.title, window.location.pathname);
    
    return { success: true, token: data.access_token };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'OAuth login failed';
    return { success: false, error: message };
  }
}
