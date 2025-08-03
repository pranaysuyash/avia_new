import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Settings,
  Shield,
  Mail,
  MoreVertical,
  Search,
  Filter,
  Download,
  Trash2,
  Edit2,
  Check,
  X,
  Crown,
  UserX,
  Clock,
  Activity
} from 'lucide-react';
import { api } from '../../services/api';

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  status: 'active' | 'invited' | 'inactive';
  joinedAt: string;
  lastActive?: string;
  avatar?: string;
}

interface Team {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  memberCount: number;
  storageUsed: number;
  storageLimit: number;
}

export const TeamManagement: React.FC = () => {
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchTeamData();
  }, []);

  const fetchTeamData = async () => {
    try {
      const [teamResponse, membersResponse] = await Promise.all([
        api.get('/teams/current'),
        api.get('/teams/current/members')
      ]);
      
      setTeam(teamResponse.data);
      setMembers(membersResponse.data);
    } catch (err) {
      console.error('Failed to fetch team data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredMembers = members.filter(member => {
    const matchesSearch = member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         member.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'all' || member.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'admin':
        return <Shield className="w-4 h-4 text-blue-500" />;
      default:
        return null;
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-yellow-900/50 text-yellow-400 border-yellow-700';
      case 'admin':
        return 'bg-blue-900/50 text-blue-400 border-blue-700';
      case 'member':
        return 'bg-green-900/50 text-green-400 border-green-700';
      case 'viewer':
        return 'bg-gray-900/50 text-gray-400 border-gray-700';
      default:
        return 'bg-gray-900/50 text-gray-400 border-gray-700';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-900/50 text-green-400 border-green-700';
      case 'invited':
        return 'bg-yellow-900/50 text-yellow-400 border-yellow-700';
      case 'inactive':
        return 'bg-red-900/50 text-red-400 border-red-700';
      default:
        return 'bg-gray-900/50 text-gray-400 border-gray-700';
    }
  };

  const handleRoleChange = async (memberId: string, newRole: string) => {
    try {
      await api.patch(`/teams/current/members/${memberId}`, { role: newRole });
      setMembers(members.map(m => 
        m.id === memberId ? { ...m, role: newRole as TeamMember['role'] } : m
      ));
    } catch (err) {
      console.error('Failed to update role:', err);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (confirm('Are you sure you want to remove this member?')) {
      try {
        await api.delete(`/teams/current/members/${memberId}`);
        setMembers(members.filter(m => m.id !== memberId));
      } catch (err) {
        console.error('Failed to remove member:', err);
      }
    }
  };

  const exportMembersList = () => {
    const csv = [
      ['Name', 'Email', 'Role', 'Status', 'Joined Date'].join(','),
      ...members.map(m => [
        m.name,
        m.email,
        m.role,
        m.status,
        new Date(m.joinedAt).toLocaleDateString()
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'team_members.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-semibold flex items-center gap-2">
                <Users className="w-6 h-6" />
                Team Management
              </h1>
              {team && (
                <p className="text-gray-400 mt-1">{team.name} • {team.memberCount} members</p>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={exportMembersList}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
              <button
                onClick={() => setShowInviteModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <UserPlus className="w-4 h-4" />
                Invite Members
              </button>
            </div>
          </div>

          {/* Search and Filter */}
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search members..."
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
              />
            </div>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-4 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Roles</option>
              <option value="owner">Owner</option>
              <option value="admin">Admin</option>
              <option value="member">Member</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
        </div>

        {/* Members List */}
        <div className="flex-1 overflow-y-auto">
          <table className="w-full">
            <thead className="bg-gray-800 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Member
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Joined
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Last Active
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {filteredMembers.map(member => (
                <tr key={member.id} className="hover:bg-gray-800/50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-white font-medium">
                        {member.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-white">{member.name}</div>
                        <div className="text-sm text-gray-400">{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {getRoleIcon(member.role)}
                      <span className={`px-2 py-1 text-xs rounded-full border ${getRoleBadgeColor(member.role)}`}>
                        {member.role}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full border ${getStatusBadgeColor(member.status)}`}>
                      {member.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                    {new Date(member.joinedAt).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                    {member.lastActive ? (
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(member.lastActive).toLocaleDateString()}
                      </div>
                    ) : (
                      <span className="text-gray-600">Never</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <button
                      onClick={() => setSelectedMember(member)}
                      className="text-gray-400 hover:text-white"
                    >
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Team Stats Sidebar */}
      <div className="w-80 bg-gray-800 border-l border-gray-700 p-6">
        <h3 className="text-lg font-semibold mb-4">Team Overview</h3>
        
        {team && (
          <div className="space-y-4">
            <div className="bg-gray-900 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Storage Usage</span>
                <span className="text-sm">{(team.storageUsed / 1024 / 1024 / 1024).toFixed(2)} GB</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${(team.storageUsed / team.storageLimit) * 100}%` }}
                />
              </div>
              <div className="text-xs text-gray-400 mt-1">
                of {(team.storageLimit / 1024 / 1024 / 1024).toFixed(0)} GB
              </div>
            </div>

            <div className="bg-gray-900 rounded-lg p-4">
              <h4 className="font-medium mb-3">Member Distribution</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Owners</span>
                  <span>{members.filter(m => m.role === 'owner').length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Admins</span>
                  <span>{members.filter(m => m.role === 'admin').length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Members</span>
                  <span>{members.filter(m => m.role === 'member').length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Viewers</span>
                  <span>{members.filter(m => m.role === 'viewer').length}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 rounded-lg p-4">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Recent Activity
              </h4>
              <div className="space-y-2 text-sm text-gray-400">
                <p>• 3 new members joined this week</p>
                <p>• 15 transcriptions created today</p>
                <p>• 2 members promoted to admin</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Member Actions Modal */}
      {selectedMember && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Member Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => {
                  setSelectedMember(null);
                }}
                className="w-full flex items-center gap-3 p-3 hover:bg-gray-800 rounded transition"
              >
                <Edit2 className="w-5 h-5" />
                <span>Edit Member Details</span>
              </button>
              
              {selectedMember.role !== 'owner' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Change Role</label>
                  <select
                    value={selectedMember.role}
                    onChange={(e) => {
                      handleRoleChange(selectedMember.id, e.target.value);
                      setSelectedMember(null);
                    }}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
                  >
                    <option value="admin">Admin</option>
                    <option value="member">Member</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </div>
              )}

              {selectedMember.status === 'invited' && (
                <button className="w-full flex items-center gap-3 p-3 hover:bg-gray-800 rounded transition">
                  <Mail className="w-5 h-5" />
                  <span>Resend Invitation</span>
                </button>
              )}

              {selectedMember.role !== 'owner' && (
                <button
                  onClick={() => {
                    handleRemoveMember(selectedMember.id);
                    setSelectedMember(null);
                  }}
                  className="w-full flex items-center gap-3 p-3 hover:bg-red-900/20 text-red-400 rounded transition"
                >
                  <UserX className="w-5 h-5" />
                  <span>Remove from Team</span>
                </button>
              )}
            </div>

            <button
              onClick={() => setSelectedMember(null)}
              className="mt-4 w-full py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <InviteModal onClose={() => setShowInviteModal(false)} onInvite={fetchTeamData} />
      )}
    </div>
  );
};

const InviteModal: React.FC<{ onClose: () => void; onInvite: () => void }> = ({ onClose, onInvite }) => {
  const [emails, setEmails] = useState('');
  const [role, setRole] = useState('member');
  const [message, setMessage] = useState('');
  const [isInviting, setIsInviting] = useState(false);

  const handleInvite = async () => {
    const emailList = emails.split(',').map(e => e.trim()).filter(e => e);
    if (emailList.length === 0) return;

    setIsInviting(true);
    try {
      await api.post('/teams/current/invite', {
        emails: emailList,
        role,
        message
      });
      onInvite();
      onClose();
    } catch (err) {
      console.error('Failed to invite members:', err);
    } finally {
      setIsInviting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full">
        <h3 className="text-lg font-semibold mb-4">Invite Team Members</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Email Addresses</label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              placeholder="Enter email addresses separated by commas"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="admin">Admin</option>
              <option value="member">Member</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Personal Message (Optional)</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Add a personal message to the invitation"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
              rows={3}
            />
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={handleInvite}
            disabled={isInviting || !emails.trim()}
            className="flex-1 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
          >
            {isInviting ? 'Sending...' : 'Send Invitations'}
          </button>
          <button
            onClick={onClose}
            className="flex-1 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default TeamManagement;