# Settings Page Components

This directory contains the modular components for the Settings page, following clean code principles with separation of concerns.

## Architecture

The Settings page has been refactored from a monolithic 1333-line component into smaller, focused modules:

```
settings/
├── index.ts                      # Barrel export for clean imports
├── SettingsTabNavigation.tsx     # Tab navigation component
├── ProfileTab.tsx                # Profile management
├── UsageTab.tsx                  # Usage logs and statistics
├── CreditsTab.tsx                # Token balance and transactions
├── APIKeysTab.tsx                # API key management
└── AgreementsTab.tsx             # Terms and user rights
```

## Component Responsibilities

### SettingsTabNavigation
- Renders tab navigation buttons
- Manages active tab state
- Provides consistent tab styling

**Props:**
- `activeTab: string` - Currently active tab ID
- `onTabChange: (tab: string) => void` - Tab change handler

### ProfileTab
- User profile information display
- Profile editing (name, avatar)
- Security settings (password, 2FA)
- Connected accounts management

**Props:**
- `profile: Profile | null` - User profile data
- `token: string | null` - Auth token
- `onProfileUpdate: (profile: Profile) => void` - Profile update callback
- `onRefreshUser: () => Promise<void>` - User refresh callback

### UsageTab
- Token usage statistics
- Execution logs display
- Activity timeline
- Log filtering and export

**Props:**
- `usageStats: UsageStats | null` - Usage statistics
- `executionLogs: ExecutionLog[]` - Execution logs
- `isLoading: boolean` - Loading state
- `token: string | null` - Auth token
- `usedTokens: number` - Used token count
- `totalTokens: number` - Total token quota
- `remainingTokens: number` - Remaining tokens
- `tokenUsagePercent: number` - Usage percentage
- `onLogsUpdate: (logs: ExecutionLog[]) => void` - Logs update callback

### CreditsTab
- Token balance display
- Transaction history
- Pricing plans
- Upgrade options

**Props:**
- `usageStats: UsageStats | null` - Usage statistics
- `transactions: CreditTransaction[]` - Transaction history
- `usedTokens: number` - Used token count
- `totalTokens: number` - Total token quota
- `remainingTokens: number` - Remaining tokens
- `tokenUsagePercent: number` - Usage percentage

### APIKeysTab
- API key listing
- Add new API keys (with encryption)
- Delete API keys
- Provider information
- Security notices

**Props:**
- `apiKeys: APIKey[]` - List of API keys
- `isLoading: boolean` - Loading state
- `token: string | null` - Auth token
- `onKeysUpdate: (keys: APIKey[]) => void` - Keys update callback

### AgreementsTab
- Terms of Service
- Privacy Policy
- Data Processing Agreement
- User rights (GDPR compliance)

**Props:** None (static content)

## Benefits of This Architecture

### 1. Single Responsibility Principle
Each component has one clear purpose, making it easier to understand and maintain.

### 2. Improved Testability
Smaller components are easier to test in isolation with focused test cases.

### 3. Better Code Organization
Related functionality is grouped together, reducing cognitive load.

### 4. Easier Collaboration
Multiple developers can work on different tabs without conflicts.

### 5. Reusability
Components can be reused in other contexts (e.g., mobile app, admin panel).

### 6. Performance Optimization
Easier to implement code splitting and lazy loading per tab.

## Usage Example

```tsx
import { SettingsPage } from './components/auth/SettingsPage';

function App() {
  return (
    <SettingsPage
      onBack={() => navigate('/')}
      onOpenMarketplace={() => navigate('/marketplace')}
      onOpenMyAgents={() => navigate('/agents')}
      onOpenAuthDialog={() => setShowAuth(true)}
    />
  );
}
```

## State Management

The parent `SettingsPage` component manages:
- Data fetching and caching
- Shared state (profile, usage stats, API keys)
- Tab navigation state
- Loading states

Child components receive:
- Read-only data via props
- Callback functions for updates
- No direct API calls (except for tab-specific actions)

## Adding a New Tab

1. Create a new component file (e.g., `BillingTab.tsx`)
2. Define props interface with required data and callbacks
3. Implement the tab UI and logic
4. Export from `index.ts`
5. Add to `SettingsTabNavigation` tabs array
6. Add `TabsContent` in `SettingsPage.tsx`
7. Update data fetching in `SettingsPage` if needed

## Best Practices

- Keep components focused on presentation
- Use callbacks for state updates
- Avoid direct API calls in child components
- Use TypeScript for type safety
- Follow existing styling patterns
- Add loading and error states
- Implement proper accessibility

## Related Documentation

- [FrankenAgent Architecture](../../../../../.kiro/steering/frankenagent-architecture.md)
- [Best Practices](../../../../../.kiro/steering/frankenagent-best-practices.md)
- [Visual Builder Guide](../../../../../.kiro/steering/frankenagent-visual-builder.md)
