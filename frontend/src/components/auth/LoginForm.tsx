import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL } from '../../config';

const inputBaseClasses =
  'h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25';

// OAuth provider icons
const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24">
    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
);

const GitHubIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
  </svg>
);

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
  onForgotPassword?: () => void;
}

export function LoginForm({ onSuccess, onSwitchToRegister, onForgotPassword }: LoginFormProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    setIsLoading(true);
    try {
      await login(email, password);
      toast.success('Logged in successfully!');
      onSuccess?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthLogin = async (provider: 'google' | 'github') => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/oauth/url/${provider}`);
      const data = await response.json();

      if (data.auth_url) {
        // Store state in localStorage (persists across redirects)
        localStorage.setItem('oauth_state', data.state);
        localStorage.setItem('oauth_provider', provider);
        localStorage.setItem('oauth_timestamp', Date.now().toString());
        window.location.href = data.auth_url;
      } else {
        toast.error('Failed to initiate OAuth login');
        setIsLoading(false);
      }
    } catch (error) {
      toast.error('OAuth login failed');
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 py-1">
      <div className="flex flex-col gap-3">
        {/* Google OAuth button hidden per user request */}
        {/* <Button
          type="button"
          variant="outline"
          onClick={() => handleOAuthLogin('google')}
          disabled={isLoading}
          className="w-full h-11 rounded-lg bg-[#0c1426] border-gray-800 text-gray-200 hover:bg-[#111c31] hover:text-white transition-colors justify-center"
        >
          <GoogleIcon />
          <span className="ml-2">Continue with Google</span>
        </Button> */}

        <Button
          type="button"
          variant="outline"
          onClick={() => handleOAuthLogin('github')}
          disabled={isLoading}
          className="w-full h-11 rounded-lg bg-[#0c1426] border-gray-800 text-gray-200 hover:bg-[#111c31] hover:text-white transition-colors justify-center"
        >
          <GitHubIcon />
          <span className="ml-2">Continue with GitHub</span>
        </Button>
      </div>

      <div className="relative py-2">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-800"></div>
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="px-2 bg-[#111c2f] text-gray-500">OR</span>
        </div>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-gray-200">Email</Label>
          <div className="relative">
            <Mail className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
            <Input
              id="email"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              required
              className={`${inputBaseClasses} pr-12`}
              style={{ paddingLeft: '44px' }}
              autoComplete="email"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="text-gray-200">Password</Label>
          <div className="relative">
            <Lock className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              required
              className={`${inputBaseClasses} pr-14`}
              style={{ paddingLeft: '44px' }}
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div className="flex justify-start">
          <button
            type="button"
            className="text-sm text-green-400 hover:text-green-400 transition-colors font-medium"
            onClick={onForgotPassword}
          >
            Forgot password?
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-4 pt-2">
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full h-12 rounded-lg !bg-gradient-to-r !from-[#00b140] !via-[#12a72f] !to-[#55a100] hover:saturate-125 text-white font-semibold shadow-lg shadow-green-900/30 border-0"
          style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
        >
          {isLoading ? 'Signing in...' : 'Sign In'}
        </Button>

        {onSwitchToRegister && (
          <div className="text-center text-sm text-gray-400">
            Don't have an account?{' '}
            <button
              type="button"
              onClick={onSwitchToRegister}
              className="text-green-400 hover:text-green-300 transition-colors font-medium"
            >
              Sign up
            </button>
          </div>
        )}
      </div>
    </form>
  );
}
