import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiUsers,
  FiShield,
  FiLock,
  FiUnlock,
  FiUserPlus,
  FiUserMinus,
  FiEdit2,
  FiTrash2,
  FiSettings,
  FiActivity,
  FiAlertCircle,
  FiCheck,
  FiX,
  FiChevronDown,
  FiChevronRight,
  FiEye,
  FiKey,
} from 'react-icons/fi';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';

interface Team {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  is_active: boolean;
  max_members: number;
  storage_quota_mb: number;
  storage_used_mb: number;
  member_count: number;
  transcript_count: number;
  created_at: string;
  updated_at: string;
  user_role?: string;
}

interface TeamMember {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    full_name?: string;
  };
  role: string;
  joined_at: string;
  invited_by?: {
    id: number;
    username: string;
    full_name?: string;
  };
}

interface Permission {
  name: string;
  value: string;
  category: string;
}

interface RolePermissions {
  role: string;
  permissions: Permission[];
}

const RoleManagement: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'teams' | 'permissions' | 'users' | 'audit'>('teams');
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [showInviteMember, setShowInviteMember] = useState(false);
  const [expandedRoles, setExpandedRoles] = useState<Set<string>>(new Set());

  // Check if user has admin permissions
  const isAdmin = user?.role === 'admin';
  const canManageTeams = user?.role === 'admin' || user?.role === 'user';

  useEffect(() => {
    if (canManageTeams) {
      fetchTeams();
    }
  }, [canManageTeams]);

  const fetchTeams = async () => {
    setLoading(true);
    try {
      const response = await api.get('/teams');
      setTeams(response.data);
    } catch (error) {
      console.error('Failed to fetch teams:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeamMembers = async (teamId: number) => {
    try {
      const response = await api.get(`/teams/${teamId}/members`);
      setTeamMembers(response.data);
    } catch (error) {
      console.error('Failed to fetch team members:', error);
    }
  };

  const handleCreateTeam = async (data: {
    name: string;
    description?: string;
    max_members: number;
    storage_quota_mb: number;
  }) => {
    try {
      await api.post('/teams', data);
      fetchTeams();
      setShowCreateTeam(false);
    } catch (error) {
      console.error('Failed to create team:', error);
    }
  };

  const handleInviteMember = async (teamId: number, email: string, role: string) => {
    try {
      await api.post(`/teams/${teamId}/invite`, { email, role });
      fetchTeamMembers(teamId);
      setShowInviteMember(false);
    } catch (error) {
      console.error('Failed to invite member:', error);
    }
  };

  const handleUpdateMemberRole = async (teamId: number, memberId: number, role: string) => {
    try {
      await api.put(`/teams/${teamId}/members/${memberId}`, { role });
      fetchTeamMembers(teamId);
    } catch (error) {
      console.error('Failed to update member role:', error);
    }
  };

  const handleRemoveMember = async (teamId: number, memberId: number) => {
    if (!confirm('Are you sure you want to remove this member?')) return;
    
    try {
      await api.delete(`/teams/${teamId}/members/${memberId}`);
      fetchTeamMembers(teamId);
    } catch (error) {
      console.error('Failed to remove member:', error);
    }
  };

  const renderTeamsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Team Management
        </h2>
        {canManageTeams && (
          <button
            onClick={() => setShowCreateTeam(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <FiUserPlus className="w-4 h-4" />
            <span>Create Team</span>
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team) => (
            <motion.div
              key={team.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => {
                setSelectedTeam(team);
                fetchTeamMembers(team.id);
              }}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {team.name}
                  </h3>
                  {team.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {team.description}
                    </p>
                  )}
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  team.is_active 
                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' 
                    : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                }`}>
                  {team.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Members</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {team.member_count}/{team.max_members}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Storage</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {(team.storage_used_mb / 1024).toFixed(1)}GB/{(team.storage_quota_mb / 1024).toFixed(0)}GB
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Transcripts</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {team.transcript_count}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Your Role</p>
                  <p className="font-semibold text-gray-900 dark:text-white capitalize">
                    {team.user_role || 'Member'}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Create Team Modal */}
      <AnimatePresence>
        {showCreateTeam && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full"
            >
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Create New Team
              </h3>
              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                handleCreateTeam({
                  name: formData.get('name') as string,
                  description: formData.get('description') as string,
                  max_members: parseInt(formData.get('max_members') as string),
                  storage_quota_mb: parseInt(formData.get('storage_quota') as string) * 1024,
                });
              }}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Team Name
                    </label>
                    <input
                      type="text"
                      name="name"
                      required
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Description (Optional)
                    </label>
                    <textarea
                      name="description"
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Max Members
                      </label>
                      <input
                        type="number"
                        name="max_members"
                        defaultValue="10"
                        min="2"
                        max="100"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Storage (GB)
                      </label>
                      <input
                        type="number"
                        name="storage_quota"
                        defaultValue="5"
                        min="1"
                        max="100"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateTeam(false)}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Create Team
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Team Details Modal */}
      <AnimatePresence>
        {selectedTeam && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {selectedTeam.name}
                </h3>
                <button
                  onClick={() => setSelectedTeam(null)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <FiX className="w-5 h-5" />
                </button>
              </div>

              {/* Team Members */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Team Members ({teamMembers.length}/{selectedTeam.max_members})
                  </h4>
                  {selectedTeam.user_role === 'owner' || selectedTeam.user_role === 'admin' ? (
                    <button
                      onClick={() => setShowInviteMember(true)}
                      className="flex items-center space-x-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <FiUserPlus className="w-4 h-4" />
                      <span>Invite Member</span>
                    </button>
                  ) : null}
                </div>

                <div className="space-y-3">
                  {teamMembers.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold">
                          {(member.user.full_name || member.user.username).charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {member.user.full_name || member.user.username}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {member.user.email}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        {selectedTeam.user_role === 'owner' || selectedTeam.user_role === 'admin' ? (
                          <>
                            <select
                              value={member.role}
                              onChange={(e) => handleUpdateMemberRole(selectedTeam.id, member.id, e.target.value)}
                              disabled={member.role === 'owner'}
                              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                            >
                              <option value="viewer">Viewer</option>
                              <option value="member">Member</option>
                              <option value="admin">Admin</option>
                              {member.role === 'owner' && <option value="owner">Owner</option>}
                            </select>
                            {member.role !== 'owner' && (
                              <button
                                onClick={() => handleRemoveMember(selectedTeam.id, member.id)}
                                className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                              >
                                <FiUserMinus className="w-4 h-4" />
                              </button>
                            )}
                          </>
                        ) : (
                          <span className="px-3 py-1 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm rounded-lg capitalize">
                            {member.role}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Invite Member Modal */}
              <AnimatePresence>
                {showInviteMember && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
                  >
                    <motion.div
                      initial={{ scale: 0.9 }}
                      animate={{ scale: 1 }}
                      exit={{ scale: 0.9 }}
                      className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                        Invite Team Member
                      </h3>
                      <form onSubmit={(e) => {
                        e.preventDefault();
                        const formData = new FormData(e.currentTarget);
                        handleInviteMember(
                          selectedTeam.id,
                          formData.get('email') as string,
                          formData.get('role') as string
                        );
                      }}>
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                              Email Address
                            </label>
                            <input
                              type="email"
                              name="email"
                              required
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                              Role
                            </label>
                            <select
                              name="role"
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="viewer">Viewer</option>
                              <option value="member">Member</option>
                              <option value="admin">Admin</option>
                            </select>
                          </div>
                        </div>
                        <div className="flex justify-end space-x-3 mt-6">
                          <button
                            type="button"
                            onClick={() => setShowInviteMember(false)}
                            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            Send Invite
                          </button>
                        </div>
                      </form>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  const renderPermissionsTab = () => {
    const systemRoles = [
      {
        role: 'admin',
        permissions: [
          { category: 'System', items: ['Full system access', 'User management', 'System configuration'] },
          { category: 'Transcripts', items: ['Create', 'Read all', 'Update all', 'Delete all', 'Share', 'Export'] },
          { category: 'Teams', items: ['Create', 'Read all', 'Update all', 'Delete all', 'Manage members'] },
          { category: 'API', items: ['Create keys', 'Manage all keys', 'View usage'] },
        ]
      },
      {
        role: 'user',
        permissions: [
          { category: 'Transcripts', items: ['Create', 'Read own', 'Update own', 'Delete own', 'Share', 'Export'] },
          { category: 'Teams', items: ['Create', 'Read member teams', 'Leave team'] },
          { category: 'API', items: ['Create own keys', 'Manage own keys'] },
        ]
      },
      {
        role: 'viewer',
        permissions: [
          { category: 'Transcripts', items: ['Read shared', 'Export if allowed'] },
          { category: 'Teams', items: ['Read member teams'] },
        ]
      }
    ];

    const teamRoles = [
      {
        role: 'owner',
        permissions: ['Full team control', 'Delete team', 'Manage all members', 'Transfer ownership']
      },
      {
        role: 'admin',
        permissions: ['Manage team content', 'Invite members', 'Remove members', 'Update settings']
      },
      {
        role: 'member',
        permissions: ['Create transcripts', 'Read team content', 'Update own content', 'Share content']
      },
      {
        role: 'viewer',
        permissions: ['Read team content', 'Export if allowed']
      }
    ];

    return (
      <div className="space-y-8">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            Role Permissions
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Overview of permissions granted to each role in the system.
          </p>
        </div>

        {/* System Roles */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Roles
          </h3>
          <div className="space-y-4">
            {systemRoles.map((role) => (
              <div key={role.role} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <button
                  onClick={() => {
                    const newExpanded = new Set(expandedRoles);
                    if (newExpanded.has(role.role)) {
                      newExpanded.delete(role.role);
                    } else {
                      newExpanded.add(role.role);
                    }
                    setExpandedRoles(newExpanded);
                  }}
                  className="w-full flex items-center justify-between"
                >
                  <div className="flex items-center space-x-3">
                    <FiShield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    <h4 className="text-lg font-medium text-gray-900 dark:text-white capitalize">
                      {role.role}
                    </h4>
                  </div>
                  {expandedRoles.has(role.role) ? (
                    <FiChevronDown className="w-5 h-5 text-gray-500" />
                  ) : (
                    <FiChevronRight className="w-5 h-5 text-gray-500" />
                  )}
                </button>

                <AnimatePresence>
                  {expandedRoles.has(role.role) && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="mt-4 space-y-3"
                    >
                      {role.permissions.map((category) => (
                        <div key={category.category}>
                          <h5 className="font-medium text-gray-700 dark:text-gray-300 mb-2">
                            {category.category}
                          </h5>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {category.items.map((permission) => (
                              <div
                                key={permission}
                                className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400"
                              >
                                <FiCheck className="w-4 h-4 text-green-500" />
                                <span>{permission}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>

        {/* Team Roles */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Team Roles
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {teamRoles.map((role) => (
              <div key={role.role} className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <h4 className="font-medium text-gray-900 dark:text-white capitalize mb-3">
                  {role.role}
                </h4>
                <ul className="space-y-2">
                  {role.permissions.map((permission) => (
                    <li
                      key={permission}
                      className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400"
                    >
                      <FiCheck className="w-4 h-4 text-green-500 flex-shrink-0" />
                      <span>{permission}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderAuditTab = () => {
    const auditLogs = [
      {
        id: 1,
        timestamp: '2024-01-20T10:30:45Z',
        user: 'john.doe',
        action: 'Permission Granted',
        resource: 'transcript:123',
        permission: 'transcript:read',
        status: 'success',
        ip: '192.168.1.1'
      },
      {
        id: 2,
        timestamp: '2024-01-20T10:28:12Z',
        user: 'jane.smith',
        action: 'Permission Denied',
        resource: 'team:456',
        permission: 'team:delete',
        status: 'denied',
        ip: '192.168.1.2'
      },
      {
        id: 3,
        timestamp: '2024-01-20T10:25:00Z',
        user: 'admin',
        action: 'Role Changed',
        resource: 'user:789',
        permission: 'user:manage_roles',
        status: 'success',
        details: 'Changed role from viewer to member',
        ip: '192.168.1.3'
      }
    ];

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            Access Audit Log
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Monitor access control events and permission changes across the system.
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Date Range
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <option>Last 24 hours</option>
                <option>Last 7 days</option>
                <option>Last 30 days</option>
                <option>Custom range</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Event Type
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <option>All Events</option>
                <option>Permission Granted</option>
                <option>Permission Denied</option>
                <option>Role Changed</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                User
              </label>
              <input
                type="text"
                placeholder="Filter by user..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Resource
              </label>
              <input
                type="text"
                placeholder="Filter by resource..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Audit Logs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  IP Address
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {auditLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {log.user}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <div>
                      {log.action}
                      {log.details && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {log.details}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                      {log.resource}
                    </code>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      log.status === 'success'
                        ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                        : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {log.ip}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Access Control Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage teams, roles, and permissions across the system
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700 mb-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('teams')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'teams'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <div className="flex items-center space-x-2">
                <FiUsers className="w-4 h-4" />
                <span>Teams</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('permissions')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'permissions'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <div className="flex items-center space-x-2">
                <FiLock className="w-4 h-4" />
                <span>Permissions</span>
              </div>
            </button>

            {isAdmin && (
              <>
                <button
                  onClick={() => setActiveTab('users')}
                  className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'users'
                      ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <FiShield className="w-4 h-4" />
                    <span>User Access</span>
                  </div>
                </button>

                <button
                  onClick={() => setActiveTab('audit')}
                  className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'audit'
                      ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <FiActivity className="w-4 h-4" />
                    <span>Audit Log</span>
                  </div>
                </button>
              </>
            )}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'teams' && renderTeamsTab()}
        {activeTab === 'permissions' && renderPermissionsTab()}
        {activeTab === 'audit' && renderAuditTab()}
      </div>
    </div>
  );
};

export default RoleManagement;