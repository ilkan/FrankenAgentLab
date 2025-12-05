import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Lock, Eye, EyeOff, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { API_BASE_URL } from '../../config';

const inputBaseClasses =
  'h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25';

interface ResetPasswordDialogProps {
  open: boolean;
  token: string;
  onSuccess: () => void;
  onClose: () => void;
}

export function ResetPasswordDialog({ open, token, onSuccess, onClose }: ResetPasswordDialogProps) {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long');
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
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          new_password: newPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        toast.success('Password reset successfully!');
        setTimeout(() => {
          onSuccess();
        }, 2000);
      } else {
        toast.error(data.detail || 'Failed to reset password');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setNewPassword('');
    setConfirmPassword('');
    setSuccess(false);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent
        className="sm:max-w-lg !bg-[#0b1324] border border-gray-800 rounded-xl shadow-[0_20px_80px_rgba(0,0,0,0.45)] px-7 py-6"
        style={{ backgroundColor: '#0b1324', borderColor: '#1f2937' }}
      >
        {success ? (
          <>
            <DialogHeader className="space-y-2">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-900/50 mb-2">
                <CheckCircle className="h-6 w-6 text-green-400" />
              </div>
              <DialogTitle className="text-2xl text-gray-100 font-semibold text-center">
                Password Reset Successful
              </DialogTitle>
              <DialogDescription className="text-gray-400 text-center">
                Your password has been reset successfully. You can now log in with your new password.
              </DialogDescription>
            </DialogHeader>
          </>
        ) : (
          <>
            <DialogHeader className="space-y-2">
              <DialogTitle className="text-2xl text-gray-100 font-semibold">
                Set New Password
              </DialogTitle>
              <DialogDescription className="text-gray-400">
                Enter your new password below.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleSubmit} className="space-y-4 py-1">
              <div className="space-y-2">
                <Label htmlFor="new-password" className="text-gray-200">New Password</Label>
                <div className="relative">
                  <Lock className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
                  <Input
                    id="new-password"
                    type={showNewPassword ? 'text' : 'password'}
                    placeholder="At least 8 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    disabled={isLoading}
                    required
                    minLength={8}
                    className={`${inputBaseClasses} pr-14`}
                    style={{ paddingLeft: '44px' }}
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password" className="text-gray-200">Confirm Password</Label>
                <div className="relative">
                  <Lock className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
                  <Input
                    id="confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Re-enter your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    disabled={isLoading}
                    required
                    minLength={8}
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

              <div className="flex flex-col gap-3 pt-2">
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-12 rounded-lg !bg-gradient-to-r !from-[#00b140] !via-[#12a72f] !to-[#55a100] hover:saturate-125 text-white font-semibold shadow-lg shadow-green-900/30 border-0"
                  style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
                >
                  {isLoading ? 'Resetting...' : 'Reset Password'}
                </Button>
              </div>
            </form>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
