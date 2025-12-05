import { User, Activity, CreditCard, Key, FileText } from 'lucide-react';

interface SettingsTabNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function SettingsTabNavigation({ activeTab, onTabChange }: SettingsTabNavigationProps) {
  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    // { id: 'usage', label: 'Usage Logs', icon: Activity }, // Hidden - not needed for MVP
    { id: 'credits', label: 'Credits', icon: CreditCard },
    // { id: 'apikeys', label: 'API Keys', icon: Key }, // Hidden - API keys managed by system
  ];

  return (
    <div className="flex gap-6 md:gap-20 border-b border-gray-800 mb-16 overflow-x-auto pb-0">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 px-2 py-3 text-base font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'text-green-400 border-green-500'
                : 'text-gray-400 border-transparent hover:text-gray-200'
            }`}
          >
            <Icon className="w-5 h-5" />
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
