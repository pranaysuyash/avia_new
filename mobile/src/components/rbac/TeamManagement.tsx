import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
  FlatList,
  Alert,
  RefreshControl,
  ActivityIndicator,
  StyleSheet,
  SafeAreaView,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
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

const TeamManagement: React.FC = () => {
  const { user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showMemberModal, setShowMemberModal] = useState(false);
  
  // Form states
  const [teamForm, setTeamForm] = useState({
    name: '',
    description: '',
    max_members: '10',
    storage_quota_gb: '5',
  });
  
  const [inviteForm, setInviteForm] = useState({
    email: '',
    role: 'member',
  });

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
      Alert.alert('Error', 'Failed to load teams');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchTeamMembers = async (teamId: number) => {
    try {
      const response = await api.get(`/teams/${teamId}/members`);
      setTeamMembers(response.data);
    } catch (error) {
      console.error('Failed to fetch team members:', error);
      Alert.alert('Error', 'Failed to load team members');
    }
  };

  const handleCreateTeam = async () => {
    if (!teamForm.name) {
      Alert.alert('Error', 'Team name is required');
      return;
    }

    try {
      await api.post('/teams', {
        name: teamForm.name,
        description: teamForm.description,
        max_members: parseInt(teamForm.max_members),
        storage_quota_mb: parseInt(teamForm.storage_quota_gb) * 1024,
      });
      
      Alert.alert('Success', 'Team created successfully');
      setShowCreateModal(false);
      setTeamForm({ name: '', description: '', max_members: '10', storage_quota_gb: '5' });
      fetchTeams();
    } catch (error) {
      console.error('Failed to create team:', error);
      Alert.alert('Error', 'Failed to create team');
    }
  };

  const handleInviteMember = async () => {
    if (!inviteForm.email || !selectedTeam) {
      Alert.alert('Error', 'Email is required');
      return;
    }

    try {
      await api.post(`/teams/${selectedTeam.id}/invite`, {
        email: inviteForm.email,
        role: inviteForm.role,
      });
      
      Alert.alert('Success', 'Invitation sent successfully');
      setShowInviteModal(false);
      setInviteForm({ email: '', role: 'member' });
      fetchTeamMembers(selectedTeam.id);
    } catch (error) {
      console.error('Failed to invite member:', error);
      Alert.alert('Error', 'Failed to send invitation');
    }
  };

  const handleUpdateMemberRole = async (memberId: number, newRole: string) => {
    if (!selectedTeam) return;

    try {
      await api.put(`/teams/${selectedTeam.id}/members/${memberId}`, {
        role: newRole,
      });
      fetchTeamMembers(selectedTeam.id);
    } catch (error) {
      console.error('Failed to update member role:', error);
      Alert.alert('Error', 'Failed to update member role');
    }
  };

  const handleRemoveMember = async (memberId: number, memberName: string) => {
    if (!selectedTeam) return;

    Alert.alert(
      'Remove Member',
      `Are you sure you want to remove ${memberName} from the team?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/teams/${selectedTeam.id}/members/${memberId}`);
              fetchTeamMembers(selectedTeam.id);
            } catch (error) {
              console.error('Failed to remove member:', error);
              Alert.alert('Error', 'Failed to remove member');
            }
          },
        },
      ]
    );
  };

  const renderTeamCard = ({ item }: { item: Team }) => (
    <TouchableOpacity
      style={styles.teamCard}
      onPress={() => {
        setSelectedTeam(item);
        fetchTeamMembers(item.id);
        setShowMemberModal(true);
      }}
    >
      <View style={styles.teamHeader}>
        <View style={styles.teamInfo}>
          <Text style={styles.teamName}>{item.name}</Text>
          {item.description && (
            <Text style={styles.teamDescription} numberOfLines={1}>
              {item.description}
            </Text>
          )}
        </View>
        <View style={[styles.statusBadge, item.is_active ? styles.activeBadge : styles.inactiveBadge]}>
          <Text style={styles.statusText}>
            {item.is_active ? 'Active' : 'Inactive'}
          </Text>
        </View>
      </View>

      <View style={styles.teamStats}>
        <View style={styles.stat}>
          <Icon name="users" size={16} color="#666" />
          <Text style={styles.statText}>
            {item.member_count}/{item.max_members}
          </Text>
        </View>
        <View style={styles.stat}>
          <Icon name="hard-drive" size={16} color="#666" />
          <Text style={styles.statText}>
            {(item.storage_used_mb / 1024).toFixed(1)}GB
          </Text>
        </View>
        <View style={styles.stat}>
          <Icon name="file-text" size={16} color="#666" />
          <Text style={styles.statText}>{item.transcript_count}</Text>
        </View>
      </View>

      {item.user_role && (
        <View style={styles.roleContainer}>
          <Text style={styles.roleLabel}>Your role:</Text>
          <Text style={styles.roleText}>{item.user_role}</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  const renderMember = ({ item }: { item: TeamMember }) => {
    const canManage = selectedTeam?.user_role === 'owner' || selectedTeam?.user_role === 'admin';
    const isOwner = item.role === 'owner';

    return (
      <View style={styles.memberCard}>
        <View style={styles.memberInfo}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {(item.user.full_name || item.user.username).charAt(0).toUpperCase()}
            </Text>
          </View>
          <View style={styles.memberDetails}>
            <Text style={styles.memberName}>
              {item.user.full_name || item.user.username}
            </Text>
            <Text style={styles.memberEmail}>{item.user.email}</Text>
          </View>
        </View>

        <View style={styles.memberActions}>
          {canManage && !isOwner ? (
            <>
              <TouchableOpacity
                style={styles.roleButton}
                onPress={() => {
                  const roles = ['viewer', 'member', 'admin'];
                  const currentIndex = roles.indexOf(item.role);
                  const nextRole = roles[(currentIndex + 1) % roles.length];
                  handleUpdateMemberRole(item.id, nextRole);
                }}
              >
                <Text style={styles.roleButtonText}>{item.role}</Text>
                <Icon name="chevron-down" size={12} color="#007AFF" />
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.removeButton}
                onPress={() => handleRemoveMember(item.id, item.user.full_name || item.user.username)}
              >
                <Icon name="user-minus" size={16} color="#FF3B30" />
              </TouchableOpacity>
            </>
          ) : (
            <View style={styles.roleDisplay}>
              <Text style={styles.roleDisplayText}>{item.role}</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  if (!canManageTeams) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyState}>
          <Icon name="lock" size={48} color="#999" />
          <Text style={styles.emptyStateText}>
            You don't have permission to manage teams
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Team Management</Text>
        <TouchableOpacity
          style={styles.createButton}
          onPress={() => setShowCreateModal(true)}
        >
          <Icon name="plus" size={20} color="#FFFFFF" />
          <Text style={styles.createButtonText}>Create</Text>
        </TouchableOpacity>
      </View>

      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      ) : (
        <FlatList
          data={teams}
          renderItem={renderTeamCard}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true);
                fetchTeams();
              }}
              colors={['#007AFF']}
              tintColor="#007AFF"
            />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Icon name="users" size={48} color="#999" />
              <Text style={styles.emptyStateText}>No teams yet</Text>
              <Text style={styles.emptyStateSubtext}>
                Create a team to start collaborating
              </Text>
            </View>
          }
        />
      )}

      {/* Create Team Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowCreateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create New Team</Text>
              <TouchableOpacity
                onPress={() => setShowCreateModal(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#333" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Team Name</Text>
                <TextInput
                  style={styles.input}
                  value={teamForm.name}
                  onChangeText={(text) => setTeamForm({ ...teamForm, name: text })}
                  placeholder="Enter team name"
                  placeholderTextColor="#999"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Description (Optional)</Text>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  value={teamForm.description}
                  onChangeText={(text) => setTeamForm({ ...teamForm, description: text })}
                  placeholder="Enter team description"
                  placeholderTextColor="#999"
                  multiline
                  numberOfLines={3}
                />
              </View>

              <View style={styles.row}>
                <View style={[styles.inputGroup, styles.halfWidth]}>
                  <Text style={styles.inputLabel}>Max Members</Text>
                  <TextInput
                    style={styles.input}
                    value={teamForm.max_members}
                    onChangeText={(text) => setTeamForm({ ...teamForm, max_members: text })}
                    placeholder="10"
                    placeholderTextColor="#999"
                    keyboardType="numeric"
                  />
                </View>

                <View style={[styles.inputGroup, styles.halfWidth]}>
                  <Text style={styles.inputLabel}>Storage (GB)</Text>
                  <TextInput
                    style={styles.input}
                    value={teamForm.storage_quota_gb}
                    onChangeText={(text) => setTeamForm({ ...teamForm, storage_quota_gb: text })}
                    placeholder="5"
                    placeholderTextColor="#999"
                    keyboardType="numeric"
                  />
                </View>
              </View>
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={[styles.button, styles.cancelButton]}
                onPress={() => setShowCreateModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.button, styles.primaryButton]}
                onPress={handleCreateTeam}
              >
                <Text style={styles.primaryButtonText}>Create Team</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Team Members Modal */}
      <Modal
        visible={showMemberModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowMemberModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, styles.fullModal]}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{selectedTeam?.name}</Text>
              <TouchableOpacity
                onPress={() => setShowMemberModal(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#333" />
              </TouchableOpacity>
            </View>

            <View style={styles.teamStatsModal}>
              <View style={styles.statModal}>
                <Text style={styles.statLabel}>Members</Text>
                <Text style={styles.statValue}>
                  {selectedTeam?.member_count}/{selectedTeam?.max_members}
                </Text>
              </View>
              <View style={styles.statModal}>
                <Text style={styles.statLabel}>Storage</Text>
                <Text style={styles.statValue}>
                  {selectedTeam ? (selectedTeam.storage_used_mb / 1024).toFixed(1) : 0}GB
                </Text>
              </View>
              <View style={styles.statModal}>
                <Text style={styles.statLabel}>Transcripts</Text>
                <Text style={styles.statValue}>{selectedTeam?.transcript_count}</Text>
              </View>
            </View>

            {(selectedTeam?.user_role === 'owner' || selectedTeam?.user_role === 'admin') && (
              <TouchableOpacity
                style={styles.inviteButton}
                onPress={() => setShowInviteModal(true)}
              >
                <Icon name="user-plus" size={16} color="#007AFF" />
                <Text style={styles.inviteButtonText}>Invite Member</Text>
              </TouchableOpacity>
            )}

            <FlatList
              data={teamMembers}
              renderItem={renderMember}
              keyExtractor={(item) => item.id.toString()}
              contentContainerStyle={styles.membersList}
              ListEmptyComponent={
                <View style={styles.emptyState}>
                  <Text style={styles.emptyStateText}>No members yet</Text>
                </View>
              }
            />
          </View>
        </View>
      </Modal>

      {/* Invite Member Modal */}
      <Modal
        visible={showInviteModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowInviteModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Invite Team Member</Text>
              <TouchableOpacity
                onPress={() => setShowInviteModal(false)}
                style={styles.closeButton}
              >
                <Icon name="x" size={24} color="#333" />
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Email Address</Text>
                <TextInput
                  style={styles.input}
                  value={inviteForm.email}
                  onChangeText={(text) => setInviteForm({ ...inviteForm, email: text })}
                  placeholder="user@example.com"
                  placeholderTextColor="#999"
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Role</Text>
                <View style={styles.roleSelector}>
                  {['viewer', 'member', 'admin'].map((role) => (
                    <TouchableOpacity
                      key={role}
                      style={[
                        styles.roleSelectorItem,
                        inviteForm.role === role && styles.roleSelectorItemActive,
                      ]}
                      onPress={() => setInviteForm({ ...inviteForm, role })}
                    >
                      <Text
                        style={[
                          styles.roleSelectorText,
                          inviteForm.role === role && styles.roleSelectorTextActive,
                        ]}
                      >
                        {role.charAt(0).toUpperCase() + role.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            </View>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={[styles.button, styles.cancelButton]}
                onPress={() => setShowInviteModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.button, styles.primaryButton]}
                onPress={handleInviteMember}
              >
                <Text style={styles.primaryButtonText}>Send Invite</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  createButtonText: {
    color: '#FFFFFF',
    marginLeft: 8,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: 16,
  },
  teamCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  teamHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  teamInfo: {
    flex: 1,
    marginRight: 8,
  },
  teamName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  teamDescription: {
    fontSize: 14,
    color: '#666',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  activeBadge: {
    backgroundColor: '#D4EDDA',
  },
  inactiveBadge: {
    backgroundColor: '#F8D7DA',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
  },
  teamStats: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  statText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 6,
  },
  roleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  roleLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  roleText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    textTransform: 'capitalize',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    maxHeight: '80%',
  },
  fullModal: {
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
  },
  closeButton: {
    padding: 4,
  },
  modalBody: {
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  modalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#333',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  row: {
    flexDirection: 'row',
    marginHorizontal: -8,
  },
  halfWidth: {
    flex: 1,
    marginHorizontal: 8,
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  cancelButton: {
    backgroundColor: '#F0F0F0',
  },
  cancelButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
  teamStatsModal: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  statModal: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  inviteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    marginHorizontal: 20,
    marginVertical: 16,
    borderWidth: 1,
    borderColor: '#007AFF',
    borderRadius: 8,
  },
  inviteButtonText: {
    color: '#007AFF',
    marginLeft: 8,
    fontWeight: '600',
  },
  membersList: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  memberCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  memberInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  memberDetails: {
    flex: 1,
  },
  memberName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 2,
  },
  memberEmail: {
    fontSize: 14,
    color: '#666',
  },
  memberActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  roleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F0F8FF',
    marginRight: 8,
  },
  roleButtonText: {
    fontSize: 14,
    color: '#007AFF',
    marginRight: 4,
    textTransform: 'capitalize',
  },
  removeButton: {
    padding: 8,
  },
  roleDisplay: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F0F0F0',
  },
  roleDisplayText: {
    fontSize: 14,
    color: '#666',
    textTransform: 'capitalize',
  },
  roleSelector: {
    flexDirection: 'row',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    overflow: 'hidden',
  },
  roleSelectorItem: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  roleSelectorItemActive: {
    backgroundColor: '#007AFF',
  },
  roleSelectorText: {
    fontSize: 14,
    color: '#666',
  },
  roleSelectorTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
});

export default TeamManagement;