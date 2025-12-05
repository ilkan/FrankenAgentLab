import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Mail, CheckCircle, ArrowLeft } from 'lucide-react';
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

interface ForgotPasswordDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onBackToLogin: () => void;
}

export function ForgotPasswordDialog({ open, onOpenChange, onBackToLogin }: ForgotPasswordDialogProps) {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      toast.error('Please enter your email address');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        toast.success('Password reset email sent!');
      } else {
        toast.error(data.detail || 'Failed to send reset email');
      }
    } catch (error) {
      toast.error('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setEmail('');
    setSuccess(false);
    onOpenChange(false);
  };

  const handleBackToLogin = () => {
    setEmail('');
    setSuccess(false);
    onBackToLogin();
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
                Check Your Email
              </DialogTitle>
              <DialogDescription className="text-gray-400 text-center">
                If an account exists with <strong className="text-gray-300">{email}</strong>, you will receive a password reset link shortly.
              </DialogDescription>
            </DialogHeader>

            <div className="flex flex-col gap-3 pt-4">
              <Button
                onClick={handleBackToLogin}
                className="w-full h-12 rounded-lg !bg-gradient-to-r !from-[#00b140] !via-[#12a72f] !to-[#55a100] hover:saturate-125 text-white font-semibold shadow-lg shadow-green-900/30 border-0"
                style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Login
              </Button>
            </div>
          </>
        ) : (
          <>
            <DialogHeader className="space-y-2">
              <DialogTitle className="text-2xl text-gray-100 font-semibold">
                Reset Password
              </DialogTitle>
              <DialogDescription className="text-gray-400">
                Enter your email address and we'll send you a link to reset your password.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleSubmit} className="space-y-4 py-1">
              <div className="space-y-2">
                <Label htmlFor="forgot-email" className="text-gray-200">Email</Label>
                <div className="relative">
                  <Mail className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
                  <Input
                    id="forgot-email"
                    type="email"
                    placeholder="your@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    required
                    className={inputBaseClasses}
                    style={{ paddingLeft: '44px' }}
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-3 pt-2">
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-12 rounded-lg !bg-gradient-to-r !from-[#00b140] !via-[#12a72f] !to-[#55a100] hover:saturate-125 text-white font-semibold shadow-lg shadow-green-900/30 border-0"
                  style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
                >
                  {isLoading ? 'Sending...' : 'Send Reset Link'}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  onClick={handleBackToLogin}
                  className="w-full text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Login
                </Button>
              </div>
            </form>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
