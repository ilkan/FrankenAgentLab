import React from 'react';
import { Zap, Store, FolderOpen, User } from 'lucide-react';
import { Button } from './ui/button';
import { UserMenu } from './auth/UserMenu';
import FrankenAgentLogo from '../img/FrankenAgent_Logo.png';

interface TopBarProps {
  subtitle?: string;
  isAuthenticated: boolean;
  onNavigateHome?: () => void;
  onOpenMarketplace?: () => void;
  onOpenMyAgents?: () => void;
  onOpenSettings?: () => void;
  onOpenAuthDialog?: () => void;
  showNavigation?: boolean;
}

export function TopBar({
  subtitle = 'Drag & drop to assemble your AI monster',
  isAuthenticated,
  onNavigateHome,
  onOpenMarketplace,
  onOpenMyAgents,
  onOpenSettings,
  onOpenAuthDialog,
  showNavigation = true,
}: TopBarProps) {
  return (
    <header className="h-16 border-b border-gray-800 bg-gray-950 flex items-center justify-between px-6 flex-shrink-0">
      <div 
        className="flex items-center gap-3 cursor-pointer" 
        onClick={onNavigateHome}
      >
        <img 
          src={FrankenAgentLogo} 
          alt="FrankenAgent Logo" 
          className="w-10 h-10 rounded-lg shadow-lg shadow-green-500/30"
        />
        <div>
          <h1 className="text-gray-100">Frankenstein AI Agent Builder</h1>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
      </div>
      
      {showNavigation && (
        <div className="flex items-center gap-4">
          {/* Marketplace button - always visible */}
          <Button
            onClick={onOpenMarketplace}
            variant="outline"
            size="sm"
            className="gap-2 transition-colors"
            style={{ 
              backgroundColor: '#172554', 
              color: '#60a5fa', 
              borderColor: '#1e40af' 
            }}
            onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => { 
              e.currentTarget.style.backgroundColor = '#1e3a8a'; 
              e.currentTarget.style.color = '#93c5fd'; 
              e.currentTarget.style.borderColor = '#2563eb'; 
            }}
            onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => { 
              e.currentTarget.style.backgroundColor = '#172554'; 
              e.currentTarget.style.color = '#60a5fa'; 
              e.currentTarget.style.borderColor = '#1e40af'; 
            }}
          >
            <Store className="w-4 h-4" />
            Monster Marketplace
          </Button>
          
          {/* My Agents button - only when authenticated */}
          {isAuthenticated && (
            <Button
              onClick={onOpenMyAgents}
              variant="outline"
              size="sm"
              className="gap-2 transition-colors"
              style={{ 
                backgroundColor: '#0e3a3a', 
                color: '#22d3ee', 
                borderColor: '#155e75' 
              }}
              onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => { 
                e.currentTarget.style.backgroundColor = '#164e63'; 
                e.currentTarget.style.color = '#67e8f9'; 
                e.currentTarget.style.borderColor = '#0891b2'; 
              }}
              onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => { 
                e.currentTarget.style.backgroundColor = '#0e3a3a'; 
                e.currentTarget.style.color = '#22d3ee'; 
                e.currentTarget.style.borderColor = '#155e75'; 
              }}
            >
              <FolderOpen className="w-4 h-4" />
              My Agents
            </Button>
          )}
          
          {/* User menu or login button */}
          {isAuthenticated ? (
            <UserMenu onOpenSettings={onOpenSettings} />
          ) : (
            <Button
              onClick={onOpenAuthDialog}
              variant="outline"
              size="sm"
              className="transition-colors"
              style={{ 
                backgroundColor: '#14532d', 
                color: '#4ade80', 
                borderColor: '#166534' 
              }}
              onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => { 
                e.currentTarget.style.backgroundColor = '#15803d'; 
                e.currentTarget.style.color = '#86efac'; 
                e.currentTarget.style.borderColor = '#16a34a'; 
              }}
              onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => { 
                e.currentTarget.style.backgroundColor = '#14532d'; 
                e.currentTarget.style.color = '#4ade80'; 
                e.currentTarget.style.borderColor = '#166534'; 
              }}
            >
              Sign In
            </Button>
          )}
        </div>
      )}
    </header>
  );
}
