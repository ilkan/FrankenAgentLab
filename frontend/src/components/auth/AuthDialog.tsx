import { useEffect, useState } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { ForgotPasswordDialog } from './ForgotPasswordDialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';

interface AuthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultMode?: 'login' | 'register';
}

export function AuthDialog({ open, onOpenChange, defaultMode = 'login' }: AuthDialogProps) {
  const [authMode, setAuthMode] = useState<'login' | 'register'>(defaultMode);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

  useEffect(() => {
    if (open) {
      setAuthMode(defaultMode);
      setShowForgotPassword(false);
    }
  }, [open, defaultMode]);

  return (
    <>
      <Dialog open={open && !showForgotPassword} onOpenChange={onOpenChange}>
        <DialogContent
          className="sm:max-w-lg !bg-[#0b1324] border border-gray-800 rounded-xl shadow-[0_20px_80px_rgba(0,0,0,0.45)] px-7 py-6"
          style={{ backgroundColor: '#0b1324', borderColor: '#1f2937' }}
        >
          <DialogHeader className="space-y-2">
            <DialogTitle className="text-2xl text-gray-100 font-semibold">
              {authMode === 'login' ? 'Welcome Back' : 'Create Account'}
            </DialogTitle>
            <DialogDescription className="text-gray-400">
              {authMode === 'login'
                ? 'Sign in to save and manage your AI agents'
                : 'Start building your Frankenstein AI agents'}
            </DialogDescription>
          </DialogHeader>

          {authMode === 'login' ? (
            <LoginForm
              onSuccess={() => onOpenChange(false)}
              onSwitchToRegister={() => setAuthMode('register')}
              onForgotPassword={() => setShowForgotPassword(true)}
            />
          ) : (
            <RegisterForm
              onSuccess={() => onOpenChange(false)}
              onSwitchToLogin={() => setAuthMode('login')}
            />
          )}
        </DialogContent>
      </Dialog>

      <ForgotPasswordDialog
        open={showForgotPassword}
        onOpenChange={setShowForgotPassword}
        onBackToLogin={() => {
          setShowForgotPassword(false);
          setAuthMode('login');
        }}
      />
    </>
  );
}
