import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Lock, Eye, EyeOff, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL } from '../../config';

const inputBaseClasses =
  'h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      toast.error('Invalid reset link');
      navigate('/');
    }
  }, [searchParams, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newPassword || !confirmPassword) {
      toast.error('Please fill in all fields');
      return;
    }

    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          new_password: newPassword,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reset password');
      }

      setIsSuccess(true);
      toast.success('Password reset successfully!');
      
      // Redirect to home after 3 seconds
      setTimeout(() => {
        navigate('/');
      }, 3000);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to reset password';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-[#0a0f1e] flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-[#0b1324] border border-gray-800 rounded-xl shadow-[0_20px_80px_rgba(0,0,0,0.45)] p-8">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
              <h1 className="text-2xl font-semibold text-gray-100">Password Reset Successful</h1>
              <p className="text-gray-400">
                Your password has been reset successfully. You can now log in with your new password.
              </p>
              <Button
                onClick={() => navigate('/')}
                className="w-full h-12 rounded-lg !bg-gradient-to-r !from-[#00b140] !via-[#12a72f] !to-[#55a100] hover:saturate-125 text-white font-semibold shadow-lg shadow-green-900/30 border-0"
                style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
              >
                Go to Home
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0f1e] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-[#0b1324] border border-gray-800 rounded-xl shadow-[0_20px_80px_rgba(0,0,0,0.45)] p-8">
          <div className="space-y-2 mb-6">
            <h1 className="text-2xl font-semibold text-gray-100">Reset Your Password</h1>
            <p className="text-gray-400">Enter your new password below</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-password" className="text-gray-200">
                New Password
              </Label>
              <div className="relative">
                <Lock
                  className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"
                  style={{ left: '16px' }}
                />
                <Input
                  id="new-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={isLoading}
                  required
                  className={`${inputBaseClasses} pr-14`}
                  style={{ paddingLeft: '44px' }}
                  autoComplete="new-password"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-gray-500">Must be at least 8 characters</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password" className="text-gray-200">
                Confirm Password
              </Label>
              <div className="relative">
                <Lock
                  className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"
                  style={{ left: '16px' }}
                />
                <Input
                  id="confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={isLoading}
                  required
                  className={`${inputBaseClasses} pr-14`}
                  style={{ paddingLeft: '44px' }}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 rounded-lg !bg-gradient-to-r !from-[#00b140] !via-[#12a72f] !to-[#55a100] hover:saturate-125 text-white font-semibold shadow-lg shadow-green-900/30 border-0"
              style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
            >
              {isLoading ? 'Resetting Password...' : 'Reset Password'}
            </Button>

            <button
              type="button"
              onClick={() => navigate('/')}
              className="w-full text-sm text-gray-400 hover:text-gray-300 transition-colors"
            >
              Back to Home
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
