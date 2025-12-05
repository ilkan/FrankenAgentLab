import { useState } from 'react';
import { Button } from '../../ui/button';
import { Card } from '../../ui/card';
import { Input } from '../../ui/input';
import {
  Mail,
  Loader2,
  Key,
  Eye,
  EyeOff,
  Shield,
  User,
  FileText,
  ExternalLink,
  CheckCircle,
} from 'lucide-react';
import { Badge } from '../../ui/badge';
import { toast } from 'sonner';
import { updateProfile, Profile } from '../../../utils/agentApi';
import { API_BASE_URL } from '../../../config';

interface ProfileTabProps {
  profile: Profile | null;
  token: string | null;
  onProfileUpdate: (profile: Profile) => void;
  onRefreshUser: () => Promise<void>;
}

export function ProfileTab({ profile, token, onProfileUpdate, onRefreshUser }: ProfileTabProps) {
  const [fullName, setFullName] = useState(profile?.full_name || '');
  const [email] = useState(profile?.email || '');
  const [isSaving, setIsSaving] = useState(false);
  
  // Password change state
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSaveProfile = async () => {
    if (!token) return;

    setIsSaving(true);
    try {
      const updates: { full_name?: string } = {};
      if (fullName !== (profile?.full_name || '')) {
        updates.full_name = fullName;
      }

      if (Object.keys(updates).length === 0) {
        toast.info('No changes to save');
        setIsSaving(false);
        return;
      }

      const updatedProfile = await updateProfile(token, updates);
      onProfileUpdate(updatedProfile);
      toast.success('Profile updated successfully');
      
      await onRefreshUser();
    } catch (error) {
      console.error('Failed to update profile:', error);
      const message = error instanceof Error ? error.message : 'Failed to update profile';
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('Please fill in all password fields');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    if (!token) {
      toast.error('Authentication required');
      return;
    }

    setIsSaving(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('Password changed successfully!');
        setShowChangePassword(false);
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        toast.error(data.detail || 'Failed to change password');
      }
    } catch (error) {
      console.error('Failed to change password:', error);
      toast.error('Failed to change password');
    } finally {
      setIsSaving(false);
    }
  };

  const policies = [
    { title: 'Terms of Service', updated: 'November 1, 2024', icon: FileText },
    { title: 'Privacy Policy', updated: 'November 1, 2024', icon: Shield },
    { title: 'Cookie Policy', updated: 'October 15, 2024', icon: FileText },
    { title: 'Acceptable Use Policy', updated: 'October 1, 2024', icon: FileText },
  ];

  const compliance = [
    { name: 'GDPR Compliant', status: 'Active', description: 'EU data protection regulation' },
    { name: 'CCPA Compliant', status: 'Active', description: 'California privacy law' },
    { name: 'SOC 2 Type II', status: 'Certified', description: 'Security & availability' },
    { name: 'ISO 27001', status: 'Certified', description: 'Information security' },
  ];

  return (
    <div className="max-w-full mx-auto px-4">
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '20px' }}>
        {/* Left Column - Personal Information & Security */}
        <div className="space-y-6">
          {/* Personal Information */}
          <Card className="p-6 bg-gray-900 border-gray-800">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Personal Information</h3>
        
        {/* Avatar Section */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative group w-32 h-32">
            <div className="w-full h-full rounded-full bg-gradient-to-br from-green-600 to-lime-600 flex items-center justify-center shadow-lg shadow-green-500/30 ring-4 ring-green-500/20 transition-all group-hover:shadow-xl group-hover:shadow-green-500/50 group-hover:ring-green-500/30" style={{ aspectRatio: '1/1' }}>
              <User className="w-16 h-16 text-white" strokeWidth={2.5} />
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-200">Profile Picture</p>
            <p className="text-xs text-gray-400 mt-1">JPG, PNG or GIF. Max 2MB</p>
          </div>
        </div>

        <div className="space-y-4 mb-4">
          <div className="space-y-2">
            <label className="text-sm text-gray-200">Full Name</label>
            <div className="relative">
              <User className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
              <Input 
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25"
                style={{ paddingLeft: '44px' }}
                placeholder="Dr. Victor Frankenstein"
                disabled={isSaving}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm text-gray-200">Email Address</label>
            <div className="relative">
              <Mail className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
              <Input 
                value={email} 
                className="h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500"
                style={{ paddingLeft: '44px' }}
                disabled
              />
            </div>
          </div>
        </div>

        <div className="flex justify-start">
          <Button 
            onClick={handleSaveProfile}
            disabled={isSaving}
            className="bg-gray-800 hover:bg-gray-700 text-gray-100 border border-gray-700"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </div>
      </Card>

          {/* Security */}
          <Card className="p-6 bg-gray-900 border-gray-800">
        <h3 className="text-lg font-medium text-gray-100 mb-4">Security</h3>

        {/* Change Password Form */}
        {!showChangePassword && (
          <Button
            onClick={() => setShowChangePassword(true)}
            variant="outline"
            className="w-full justify-start bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100"
          >
            <Key className="w-4 h-4 mr-2" />
            Change Password
          </Button>
        )}

        {/* Change Password Form */}
        {showChangePassword && (
          <div className="mt-6 space-y-4">
            <h4 className="text-sm font-medium text-gray-100">Change Password</h4>
            
            <div className="space-y-2">
              <label className="text-sm text-gray-200">Current Password</label>
              <div className="relative">
                <Key className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
                <Input
                  type={showCurrentPassword ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25 pr-14"
                  style={{ paddingLeft: '44px' }}
                  placeholder="Enter current password"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm text-gray-200">New Password</label>
              <div className="relative">
                <Key className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
                <Input
                  type={showNewPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25 pr-14"
                  style={{ paddingLeft: '44px' }}
                  placeholder="At least 8 characters"
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
              <label className="text-sm text-gray-200">Confirm New Password</label>
              <div className="relative">
                <Key className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
                <Input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="h-12 rounded-lg bg-[#0c1426] border border-gray-800 text-gray-100 placeholder:text-gray-500 focus-visible:border-green-500/70 focus-visible:ring-green-500/25 pr-14"
                  style={{ paddingLeft: '44px' }}
                  placeholder="Confirm new password"
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

            <div className="flex gap-2 pt-2">
              <Button
                onClick={() => setShowChangePassword(false)}
                variant="outline"
                className="flex-1 bg-gray-900 border-gray-700 text-gray-300"
              >
                Cancel
              </Button>
              <Button
                onClick={handleChangePassword}
                disabled={isSaving}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Updating...
                  </>
                ) : (
                  'Update Password'
                )}
              </Button>
            </div>
          </div>
        )}
      </Card>
        </div>

        {/* Column 2 - Data & Privacy Rights */}
        <Card className="p-6 bg-gray-900 border-gray-800">
          <h3 className="text-lg font-medium text-gray-100 mb-4">Data & Privacy Rights</h3>
          <div className="space-y-4">
            <div className="p-4 bg-gray-950 rounded-lg border border-gray-800">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-green-900/50 flex items-center justify-center flex-shrink-0">
                  <Shield className="w-5 h-5 text-green-400" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-100 mb-1">Right to Access</h4>
                  <p className="text-xs text-gray-400">Request a copy of all personal data we hold about you</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full bg-gray-900 border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100"
              >
                Request Data Export
              </Button>
            </div>

            <div className="p-4 bg-gray-950 rounded-lg border border-gray-800">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-blue-900/50 flex items-center justify-center flex-shrink-0">
                  <Shield className="w-5 h-5 text-blue-400" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-100 mb-1">Right to Portability</h4>
                  <p className="text-xs text-gray-400">Transfer your data to another service in a machine-readable format</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full bg-gray-900 border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-gray-100"
              >
                Download My Data
              </Button>
            </div>

            <div className="p-4 bg-gray-950 rounded-lg border border-gray-800">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-red-900/50 flex items-center justify-center flex-shrink-0">
                  <Shield className="w-5 h-5 text-red-400" />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-100 mb-1">Right to Deletion</h4>
                  <p className="text-xs text-gray-400">Permanently delete your account and all associated data</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full bg-gray-900 border-red-700 text-red-400 hover:bg-red-950/30"
              >
                Delete My Account
              </Button>
            </div>
          </div>
        </Card>

        {/* Column 3 - Terms & Policies */}
        <Card className="p-6 bg-gray-900 border-gray-800">
          <h3 className="text-lg font-medium text-gray-100 mb-4">Terms & Policies</h3>
          <div className="space-y-3">
            {policies.map((policy, index) => {
              const Icon = policy.icon;
              return (
                <button
                  key={index}
                  className="w-full p-4 bg-gray-950 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors text-left group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-900/50 flex items-center justify-center">
                        <Icon className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-100">{policy.title}</p>
                        <p className="text-xs text-gray-500">Last updated: {policy.updated}</p>
                      </div>
                    </div>
                    <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-gray-100 transition-colors" />
                  </div>
                </button>
              );
            })}
          </div>
        </Card>

        {/* Column 4 - Compliance & Certifications */}
        <Card className="p-6 bg-gray-900 border-gray-800">
          <h3 className="text-lg font-medium text-gray-100 mb-4">Compliance & Certifications</h3>
          <div className="space-y-3">
            {compliance.map((cert, index) => (
              <div key={index} className="p-4 bg-gray-950 rounded-lg border border-gray-800">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-100">{cert.name}</h4>
                  <Badge 
                    variant="outline" 
                    className="border-green-700 text-green-400 text-xs"
                  >
                    <CheckCircle className="w-3 h-3 mr-1" />
                    {cert.status}
                  </Badge>
                </div>
                <p className="text-xs text-gray-400">{cert.description}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
