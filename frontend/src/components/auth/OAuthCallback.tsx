import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { API_BASE_URL } from '../../config';

export function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setUser, setToken } = useAuth();

  useEffect(() => {
    const handleOAuthCallback = async () => {
      // Some providers return tokens in URL hash, not query params
      const hashParams = new URLSearchParams(window.location.hash.substring(1));
      const access_token = hashParams.get('access_token');
      const refresh_token = hashParams.get('refresh_token');
      const error = hashParams.get('error');
      const error_description = hashParams.get('error_description');

      // Also check query params for errors
      const queryError = searchParams.get('error');
      const queryErrorDescription = searchParams.get('error_description');

      // Check for OAuth errors
      if (error || queryError) {
        const errorMsg = error_description || queryErrorDescription || error || queryError || 'OAuth authentication failed';
        toast.error(`OAuth error: ${errorMsg}`);
        navigate('/');
        return;
      }

      // Clear stored provider
      sessionStorage.removeItem('oauth_provider');

      if (!access_token) {
        toast.error('No access token received from OAuth provider');
        navigate('/');
        return;
      }

      try {
        // Store tokens
        localStorage.setItem('token', access_token);
        localStorage.setItem('auth_token', access_token);
        if (refresh_token) {
          localStorage.setItem('refresh_token', refresh_token);
        }
        setToken(access_token);

        // Fetch user info
        const userResponse = await fetch(`${API_BASE_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${access_token}`,
          },
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUser(userData);
          toast.success('Logged in successfully!');
        } else {
          throw new Error('Failed to fetch user profile');
        }

        navigate('/');
      } catch (error) {
        const message = error instanceof Error ? error.message : 'OAuth login failed';
        toast.error(message);
        // Clear invalid tokens
        localStorage.removeItem('token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        navigate('/');
      }
    };

    handleOAuthCallback();
  }, [searchParams, navigate, setUser, setToken]);

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
        <p className="text-gray-300">Completing authentication...</p>
      </div>
    </div>
  );
}
