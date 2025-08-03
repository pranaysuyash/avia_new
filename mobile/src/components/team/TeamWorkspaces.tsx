import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Modal,
  TextInput,
  Alert,
  RefreshControl,
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';

const { width } = Dimensions.get('window');

interface Team {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  workspaceCount: number;
  storageUsed: number;
  storageLimit: number;
  subscriptionTier: 'free' | 'pro' | 'enterprise';
  role: 'owner' | 'admin' | 'editor' | 'member' | 'viewer';
  members: TeamMember[];
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
  lastActive: string;
  status: 'active' | 'inactive';
}

interface Workspace {
  id: string;
  name: string;
  description: string;
  teamId: string;
  contentCount: number;
  lastActivity: string;
  members: TeamMember[];
}

interface Invitation {
  id: string;
  email: string;
  role: string;
  invitedBy: string;
  createdAt: string;
  expiresAt: string;
  status: 'pending' | 'accepted' | 'declined' | 'expired';
}

const TeamWorkspaces: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [activeTab, setActiveTab] = useState<'workspaces' | 'members' | 'invitations'>('workspaces');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  // Modal states
  const [createTeamModal, setCreateTeamModal] = useState(false);
  const [createWorkspaceModal, setCreateWorkspaceModal] = useState(false);
  const [inviteMemberModal, setInviteMemberModal] = useState(false);
  const [teamMenuModal, setTeamMenuModal] = useState(false);

  // Form states
  const [teamForm, setTeamForm] = useState({
    name: '',
    description: '',
    subscriptionTier: 'free' as const
  });
  const [workspaceForm, setWorkspaceForm] = useState({
    name: '',
    description: ''
  });
  const [inviteForm, setInviteForm] = useState({
    email: '',
    role: 'member'
  });

  useEffect(() => {
    loadTeams();
  }, []);

  useEffect(() => {
    if (selectedTeam) {
      loadWorkspaces(selectedTeam.id);
      loadInvitations(selectedTeam.id);
    }
  }, [selectedTeam]);

  const loadTeams = async () => {
    setLoading(true);
    try {
      // Mock API call - replace with actual API
      const mockTeams: Team[] = [
        {
          id: 'team1',
          name: 'Acme Corporation',
          description: 'Main company workspace',
          memberCount: 12,
          workspaceCount: 5,
          storageUsed: 45.2,
          storageLimit: 100,
          subscriptionTier: 'enterprise',
          role: 'owner',
          members: [
            {
              id: 'user1',
              name: 'Alice Johnson',
              email: 'alice@acme.com',
              role: 'owner',
              lastActive: '2 hours ago',
              status: 'active'
            },
            {
              id: 'user2',
              name: 'Bob Smith',
              email: 'bob@acme.com',
              role: 'admin',
              lastActive: '1 day ago',
              status: 'active'
            }
          ]
        },
        {
          id: 'team2',
          name: 'Design Team',
          description: 'Creative design projects',
          memberCount: 5,
          workspaceCount: 3,
          storageUsed: 12.8,
          storageLimit: 10,
          subscriptionTier: 'pro',
          role: 'editor',
          members: []
        }
      ];
      setTeams(mockTeams);
      if (mockTeams.length > 0 && !selectedTeam) {
        setSelectedTeam(mockTeams[0]);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to load teams');
    } finally {
      setLoading(false);
    }
  };

  const loadWorkspaces = async (teamId: string) => {
    try {
      // Mock API call
      const mockWorkspaces: Workspace[] = [
        {
          id: 'ws1',
          name: 'Development',
          description: 'Software development projects',
          teamId,
          contentCount: 156,
          lastActivity: '2 hours ago',
          members: []
        },
        {
          id: 'ws2',
          name: 'Marketing',
          description: 'Marketing campaigns and content',
          teamId,
          contentCount: 89,
          lastActivity: '1 day ago',
          members: []
        }
      ];
      setWorkspaces(mockWorkspaces);
    } catch (error) {
      Alert.alert('Error', 'Failed to load workspaces');
    }
  };

  const loadInvitations = async (teamId: string) => {
    try {
      // Mock API call
      const mockInvitations: Invitation[] = [
        {
          id: 'inv1',
          email: 'newdev@acme.com',
          role: 'editor',
          invitedBy: 'Alice Johnson',
          createdAt: '2024-03-05',
          expiresAt: '2024-03-12',
          status: 'pending'
        }
      ];
      setInvitations(mockInvitations);
    } catch (error) {
      Alert.alert('Error', 'Failed to load invitations');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadTeams();
    setRefreshing(false);
  };

  const handleCreateTeam = async () => {
    if (!teamForm.name.trim()) {
      Alert.alert('Error', 'Team name is required');
      return;
    }

    setLoading(true);
    try {
      // Mock API call
      const newTeam: Team = {
        id: `team_${Date.now()}`,
        name: teamForm.name,
        description: teamForm.description,
        memberCount: 1,
        workspaceCount: 0,
        storageUsed: 0,
        storageLimit: teamForm.subscriptionTier === 'free' ? 1 : 
                     teamForm.subscriptionTier === 'pro' ? 10 : 100,
        subscriptionTier: teamForm.subscriptionTier,
        role: 'owner',
        members: []
      };
      
      setTeams([...teams, newTeam]);
      setTeamForm({ name: '', description: '', subscriptionTier: 'free' });
      setCreateTeamModal(false);
      Alert.alert('Success', 'Team created successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to create team');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkspace = async () => {
    if (!workspaceForm.name.trim()) {
      Alert.alert('Error', 'Workspace name is required');
      return;
    }

    if (!selectedTeam) return;
    
    setLoading(true);
    try {
      // Mock API call
      const newWorkspace: Workspace = {
        id: `ws_${Date.now()}`,
        name: workspaceForm.name,
        description: workspaceForm.description,
        teamId: selectedTeam.id,
        contentCount: 0,
        lastActivity: 'Just created',
        members: []
      };
      
      setWorkspaces([...workspaces, newWorkspace]);
      setWorkspaceForm({ name: '', description: '' });
      setCreateWorkspaceModal(false);
      Alert.alert('Success', 'Workspace created successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to create workspace');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteMember = async () => {
    if (!inviteForm.email.trim() || !inviteForm.email.includes('@')) {
      Alert.alert('Error', 'Please enter a valid email address');
      return;
    }

    if (!selectedTeam) return;
    
    setLoading(true);
    try {
      // Mock API call
      const newInvitation: Invitation = {
        id: `inv_${Date.now()}`,
        email: inviteForm.email,
        role: inviteForm.role,
        invitedBy: 'Current User',
        createdAt: new Date().toISOString().split('T')[0],
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        status: 'pending'
      };
      
      setInvitations([...invitations, newInvitation]);
      setInviteForm({ email: '', role: 'member' });
      setInviteMemberModal(false);
      Alert.alert('Success', 'Invitation sent successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to send invitation');
    } finally {
      setLoading(false);
    }
  };

  const renderTeamCard = ({ item: team }: { item: Team }) => (
    <TouchableOpacity
      style={[
        styles.teamCard,
        selectedTeam?.id === team.id && styles.selectedTeamCard
      ]}
      onPress={() => setSelectedTeam(team)}
    >
      <View style={styles.teamCardHeader}>
        <View style={styles.teamInfo}>
          <Text style={styles.teamName}>{team.name}</Text>
          <Text style={styles.teamDescription}>{team.description}</Text>
          <View style={styles.tierBadge}>
            <Text style={styles.tierText}>{team.subscriptionTier.toUpperCase()}</Text>
          </View>
        </View>
        <TouchableOpacity
          style={styles.menuButton}
          onPress={() => setTeamMenuModal(true)}
        >
          <Icon name="more-vert" size={24} color="#666" />
        </TouchableOpacity>
      </View>
      
      <View style={styles.teamStats}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{team.memberCount}</Text>
          <Text style={styles.statLabel}>Members</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{team.workspaceCount}</Text>
          <Text style={styles.statLabel}>Workspaces</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{team.storageUsed}GB</Text>
          <Text style={styles.statLabel}>Storage</Text>
        </View>
      </View>
      
      <View style={styles.storageBar}>
        <View 
          style={[
            styles.storageProgress,
            { width: `${(team.storageUsed / team.storageLimit) * 100}%` }
          ]}
        />
      </View>
      <Text style={styles.storageText}>
        {team.storageUsed}GB / {team.storageLimit}GB used
      </Text>
    </TouchableOpacity>
  );

  const renderWorkspaceCard = ({ item: workspace }: { item: Workspace }) => (
    <TouchableOpacity style={styles.workspaceCard}>
      <View style={styles.workspaceHeader}>
        <View style={styles.workspaceInfo}>
          <View style={styles.workspaceTitleRow}>
            <Icon name="folder" size={20} color="#2196F3" />
            <Text style={styles.workspaceName}>{workspace.name}</Text>
          </View>
          <Text style={styles.workspaceDescription}>{workspace.description}</Text>
        </View>
        <TouchableOpacity style={styles.menuButton}>
          <Icon name="more-vert" size={20} color="#666" />
        </TouchableOpacity>
      </View>
      
      <View style={styles.workspaceStats}>
        <View style={styles.workspaceStatItem}>
          <Text style={styles.workspaceStatLabel}>Content Items</Text>
          <Text style={styles.workspaceStatValue}>{workspace.contentCount}</Text>
        </View>
        <View style={styles.workspaceStatItem}>
          <Text style={styles.workspaceStatLabel}>Last Activity</Text>
          <Text style={styles.workspaceStatValue}>{workspace.lastActivity}</Text>
        </View>
      </View>
      
      <View style={styles.workspaceActions}>
        <TouchableOpacity style={styles.actionButton}>
          <Icon name="share" size={16} color="#2196F3" />
          <Text style={styles.actionButtonText}>Share</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Icon name="edit" size={16} color="#2196F3" />
          <Text style={styles.actionButtonText}>Open</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  const renderMemberItem = ({ item: member }: { item: TeamMember }) => (
    <View style={styles.memberItem}>
      <View style={styles.memberAvatar}>
        <Text style={styles.memberAvatarText}>{member.name.charAt(0)}</Text>
      </View>
      <View style={styles.memberInfo}>
        <Text style={styles.memberName}>{member.name}</Text>
        <Text style={styles.memberEmail}>{member.email}</Text>
        <Text style={styles.memberLastActive}>Last active: {member.lastActive}</Text>
      </View>
      <View style={styles.memberRole}>
        <Text style={styles.roleText}>{member.role}</Text>
        <View style={[
          styles.statusDot,
          { backgroundColor: member.status === 'active' ? '#4CAF50' : '#9E9E9E' }
        ]} />
      </View>
    </View>
  );

  const renderInvitationItem = ({ item: invitation }: { item: Invitation }) => (
    <View style={styles.invitationItem}>
      <View style={styles.invitationInfo}>
        <Text style={styles.invitationEmail}>{invitation.email}</Text>
        <Text style={styles.invitationRole}>Role: {invitation.role}</Text>
        <Text style={styles.invitationDetails}>
          Invited by {invitation.invitedBy} • Expires {invitation.expiresAt}
        </Text>
      </View>
      <View style={styles.invitationActions}>
        <TouchableOpacity style={styles.resendButton}>
          <Text style={styles.resendButtonText}>Resend</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.cancelButton}>
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'workspaces':
        return (
          <FlatList
            data={workspaces}
            renderItem={renderWorkspaceCard}
            keyExtractor={(item) => item.id}
            numColumns={1}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.workspacesList}
          />
        );
      case 'members':
        return (
          <FlatList
            data={selectedTeam?.members || []}
            renderItem={renderMemberItem}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.membersList}
          />
        );
      case 'invitations':
        return (
          <FlatList
            data={invitations}
            renderItem={renderInvitationItem}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.invitationsList}
          />
        );
      default:
        return null;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Team Workspaces</Text>
          <TouchableOpacity
            style={styles.createButton}
            onPress={() => setCreateTeamModal(true)}
          >
            <Icon name="add" size={24} color="#fff" />
          </TouchableOpacity>
        </View>

        {/* Teams List */}
        <View style={styles.teamsSection}>
          <Text style={styles.sectionTitle}>Your Teams</Text>
          <FlatList
            data={teams}
            renderItem={renderTeamCard}
            keyExtractor={(item) => item.id}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.teamsList}
          />
        </View>

        {/* Selected Team Content */}
        {selectedTeam && (
          <View style={styles.teamContent}>
            <View style={styles.teamContentHeader}>
              <Text style={styles.teamContentTitle}>{selectedTeam.name}</Text>
              <View style={styles.teamActions}>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => setCreateWorkspaceModal(true)}
                >
                  <Icon name="add" size={16} color="#2196F3" />
                  <Text style={styles.actionButtonText}>Workspace</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => setInviteMemberModal(true)}
                >
                  <Icon name="person-add" size={16} color="#2196F3" />
                  <Text style={styles.actionButtonText}>Invite</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Tabs */}
            <View style={styles.tabs}>
              <TouchableOpacity
                style={[styles.tab, activeTab === 'workspaces' && styles.activeTab]}
                onPress={() => setActiveTab('workspaces')}
              >
                <Text style={[styles.tabText, activeTab === 'workspaces' && styles.activeTabText]}>
                  Workspaces
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, activeTab === 'members' && styles.activeTab]}
                onPress={() => setActiveTab('members')}
              >
                <Text style={[styles.tabText, activeTab === 'members' && styles.activeTabText]}>
                  Members
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, activeTab === 'invitations' && styles.activeTab]}
                onPress={() => setActiveTab('invitations')}
              >
                <Text style={[styles.tabText, activeTab === 'invitations' && styles.activeTabText]}>
                  Invitations
                </Text>
              </TouchableOpacity>
            </View>

            {/* Tab Content */}
            <View style={styles.tabContent}>
              {renderTabContent()}
            </View>
          </View>
        )}
      </ScrollView>

      {/* Loading Overlay */}
      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#2196F3" />
        </View>
      )}

      {/* Create Team Modal */}
      <Modal
        visible={createTeamModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setCreateTeamModal(false)}>
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Create Team</Text>
            <TouchableOpacity onPress={handleCreateTeam}>
              <Text style={styles.modalSaveText}>Create</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Team Name</Text>
              <TextInput
                style={styles.textInput}
                value={teamForm.name}
                onChangeText={(text) => setTeamForm({ ...teamForm, name: text })}
                placeholder="Enter team name"
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                style={[styles.textInput, styles.textArea]}
                value={teamForm.description}
                onChangeText={(text) => setTeamForm({ ...teamForm, description: text })}
                placeholder="Enter team description"
                multiline
                numberOfLines={3}
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Subscription Tier</Text>
              <View style={styles.pickerContainer}>
                {['free', 'pro', 'enterprise'].map((tier) => (
                  <TouchableOpacity
                    key={tier}
                    style={[
                      styles.pickerOption,
                      teamForm.subscriptionTier === tier && styles.selectedPickerOption
                    ]}
                    onPress={() => setTeamForm({ ...teamForm, subscriptionTier: tier as any })}
                  >
                    <Text style={[
                      styles.pickerOptionText,
                      teamForm.subscriptionTier === tier && styles.selectedPickerOptionText
                    ]}>
                      {tier === 'free' && 'Free (5 members, 1GB)'}
                      {tier === 'pro' && 'Pro (25 members, 10GB)'}
                      {tier === 'enterprise' && 'Enterprise (100 members, 100GB)'}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Create Workspace Modal */}
      <Modal
        visible={createWorkspaceModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setCreateWorkspaceModal(false)}>
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Create Workspace</Text>
            <TouchableOpacity onPress={handleCreateWorkspace}>
              <Text style={styles.modalSaveText}>Create</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Workspace Name</Text>
              <TextInput
                style={styles.textInput}
                value={workspaceForm.name}
                onChangeText={(text) => setWorkspaceForm({ ...workspaceForm, name: text })}
                placeholder="Enter workspace name"
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                style={[styles.textInput, styles.textArea]}
                value={workspaceForm.description}
                onChangeText={(text) => setWorkspaceForm({ ...workspaceForm, description: text })}
                placeholder="Enter workspace description"
                multiline
                numberOfLines={3}
              />
            </View>
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Invite Member Modal */}
      <Modal
        visible={inviteMemberModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setInviteMemberModal(false)}>
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Invite Member</Text>
            <TouchableOpacity onPress={handleInviteMember}>
              <Text style={styles.modalSaveText}>Send</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Email Address</Text>
              <TextInput
                style={styles.textInput}
                value={inviteForm.email}
                onChangeText={(text) => setInviteForm({ ...inviteForm, email: text })}
                placeholder="Enter email address"
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Role</Text>
              <View style={styles.pickerContainer}>
                {['viewer', 'member', 'editor', 'admin'].map((role) => (
                  <TouchableOpacity
                    key={role}
                    style={[
                      styles.pickerOption,
                      inviteForm.role === role && styles.selectedPickerOption
                    ]}
                    onPress={() => setInviteForm({ ...inviteForm, role })}
                  >
                    <Text style={[
                      styles.pickerOptionText,
                      inviteForm.role === role && styles.selectedPickerOptionText
                    ]}>
                      {role.charAt(0).toUpperCase() + role.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  createButton: {
    backgroundColor: '#2196F3',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  teamsSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  teamsList: {
    paddingRight: 20,
  },
  teamCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginRight: 16,
    width: width * 0.8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  selectedTeamCard: {
    borderColor: '#2196F3',
    borderWidth: 2,
  },
  teamCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  teamInfo: {
    flex: 1,
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
    marginBottom: 8,
  },
  tierBadge: {
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  tierText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2196F3',
  },
  menuButton: {
    padding: 4,
  },
  teamStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  storageBar: {
    height: 6,
    backgroundColor: '#e0e0e0',
    borderRadius: 3,
    marginBottom: 4,
  },
  storageProgress: {
    height: '100%',
    backgroundColor: '#2196F3',
    borderRadius: 3,
  },
  storageText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  teamContent: {
    backgroundColor: '#fff',
    margin: 20,
    borderRadius: 12,
    overflow: 'hidden',
  },
  teamContentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  teamContentTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
  },
  teamActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#f0f8ff',
    gap: 4,
  },
  actionButtonText: {
    fontSize: 14,
    color: '#2196F3',
    fontWeight: '500',
  },
  tabs: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#2196F3',
  },
  tabText: {
    fontSize: 16,
    color: '#666',
  },
  activeTabText: {
    color: '#2196F3',
    fontWeight: '600',
  },
  tabContent: {
    flex: 1,
  },
  workspacesList: {
    padding: 16,
  },
  workspaceCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  workspaceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  workspaceInfo: {
    flex: 1,
  },
  workspaceTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
    gap: 8,
  },
  workspaceName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  workspaceDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  workspaceStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  workspaceStatItem: {
    flex: 1,
  },
  workspaceStatLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  workspaceStatValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  workspaceActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  membersList: {
    padding: 16,
  },
  memberItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  memberAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#2196F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  memberAvatarText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  memberInfo: {
    flex: 1,
  },
  memberName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  memberEmail: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  memberLastActive: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  memberRole: {
    alignItems: 'flex-end',
  },
  roleText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#2196F3',
    marginBottom: 4,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  invitationsList: {
    padding: 16,
  },
  invitationItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  invitationInfo: {
    flex: 1,
  },
  invitationEmail: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  invitationRole: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  invitationDetails: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  invitationActions: {
    flexDirection: 'row',
    gap: 8,
  },
  resendButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#e3f2fd',
    borderRadius: 4,
  },
  resendButtonText: {
    fontSize: 12,
    color: '#2196F3',
    fontWeight: '500',
  },
  cancelButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#ffebee',
    borderRadius: 4,
  },
  cancelButtonText: {
    fontSize: 12,
    color: '#f44336',
    fontWeight: '500',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  modalCancelText: {
    fontSize: 16,
    color: '#666',
  },
  modalSaveText: {
    fontSize: 16,
    color: '#2196F3',
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  pickerContainer: {
    gap: 8,
  },
  pickerOption: {
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    backgroundColor: '#fff',
  },
  selectedPickerOption: {
    borderColor: '#2196F3',
    backgroundColor: '#e3f2fd',
  },
  pickerOptionText: {
    fontSize: 16,
    color: '#333',
  },
  selectedPickerOptionText: {
    color: '#2196F3',
    fontWeight: '500',
  },
});

export default TeamWorkspaces;