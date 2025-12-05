import { useAuth } from '../../contexts/AuthContext';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { User, LogOut, Settings } from 'lucide-react';

interface UserMenuProps {
  onOpenSettings?: () => void;
}

export function UserMenu({ onOpenSettings }: UserMenuProps) {
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="w-10 h-10 rounded-full bg-gradient-to-br from-green-600 to-lime-600 hover:from-green-500 hover:to-lime-500 border-2 border-green-500 hover:border-green-400 flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-green-400 cursor-pointer transition-all shadow-lg shadow-green-500/30">
        <User className="w-5 h-5 text-white" />
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        sideOffset={8}
        className="w-56 bg-gray-900 border-gray-800 z-[100] p-2"
      >
        <DropdownMenuLabel className="text-gray-100 px-2 py-2">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{user.full_name || 'User'}</p>
            <p className="text-xs text-gray-400">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-gray-800 my-2" />
        <DropdownMenuItem
          onSelect={() => onOpenSettings?.()}
          className="text-gray-300 focus:bg-gray-800 focus:text-gray-100 cursor-pointer px-2 py-2 mb-1 rounded-md"
        >
          <Settings className="w-4 h-4 mr-3" />
          Settings
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={() => logout()}
          className="text-red-400 focus:bg-gray-800 focus:text-red-300 cursor-pointer px-2 py-2 rounded-md"
        >
          <LogOut className="w-4 h-4 mr-3" />
          Log Out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
