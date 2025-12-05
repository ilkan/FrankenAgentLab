import { ReactNode } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const [showAuth, setShowAuth] = useState(true);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-950">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Dialog open={showAuth} onOpenChange={setShowAuth}>
        <DialogContent className="sm:max-w-md bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-gray-100">
              {authMode === 'login' ? 'Log In' : 'Create Account'}
            </DialogTitle>
            <DialogDescription className="text-gray-400">
              {authMode === 'login'
                ? 'Log in to access your agents and blueprints'
                : 'Create an account to start building agents'}
            </DialogDescription>
          </DialogHeader>
          
          {authMode === 'login' ? (
            <LoginForm
              onSuccess={() => setShowAuth(false)}
              onSwitchToRegister={() => setAuthMode('register')}
            />
          ) : (
            <RegisterForm
              onSuccess={() => setShowAuth(false)}
              onSwitchToLogin={() => setAuthMode('login')}
            />
          )}
        </DialogContent>
      </Dialog>
    );
  }

  return <>{children}</>;
}
