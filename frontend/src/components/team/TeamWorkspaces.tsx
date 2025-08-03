import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  Grid, 
  Chip,
  Avatar,
  AvatarGroup,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  People as PeopleIcon,
  Folder as FolderIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  Share as ShareIcon,
  Edit as EditIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

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
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [createTeamOpen, setCreateTeamOpen] = useState(false);
  const [createWorkspaceOpen, setCreateWorkspaceOpen] = useState(false);
  const [inviteMemberOpen, setInviteMemberOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

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
            }
          ]
        }
      ];
      setTeams(mockTeams);
      if (mockTeams.length > 0) {
        setSelectedTeam(mockTeams[0]);
      }
    } catch (err) {
      setError('Failed to load teams');
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
        }
      ];
      setWorkspaces(mockWorkspaces);
    } catch (err) {
      setError('Failed to load workspaces');
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
    } catch (err) {
      setError('Failed to load invitations');
    }
  };

  const handleCreateTeam = async () => {
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
      setCreateTeamOpen(false);
    } catch (err) {
      setError('Failed to create team');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkspace = async () => {
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
      setCreateWorkspaceOpen(false);
    } catch (err) {
      setError('Failed to create workspace');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteMember = async () => {
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
      setInviteMemberOpen(false);
    } catch (err) {
      setError('Failed to send invitation');
    } finally {
      setLoading(false);
    }
  };

  const renderTeamCard = (team: Team) => (
    <Card 
      key={team.id}
      sx={{ 
        cursor: 'pointer',
        border: selectedTeam?.id === team.id ? 2 : 1,
        borderColor: selectedTeam?.id === team.id ? 'primary.main' : 'divider'
      }}
      onClick={() => setSelectedTeam(team)}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="h6" gutterBottom>
              {team.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {team.description}
            </Typography>
            <Chip 
              label={team.subscriptionTier.toUpperCase()} 
              size="small" 
              color={team.subscriptionTier === 'enterprise' ? 'primary' : 'default'}
            />
          </Box>
          <IconButton
            onClick={(e) => {
              e.stopPropagation();
              setMenuAnchor(e.currentTarget);
            }}
          >
            <MoreVertIcon />
          </IconButton>
        </Box>
        
        <Box mt={2}>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Typography variant="caption" color="text.secondary">
                Members
              </Typography>
              <Typography variant="h6">
                {team.memberCount}
              </Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="caption" color="text.secondary">
                Workspaces
              </Typography>
              <Typography variant="h6">
                {team.workspaceCount}
              </Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="caption" color="text.secondary">
                Storage
              </Typography>
              <Typography variant="h6">
                {team.storageUsed}GB
              </Typography>
            </Grid>
          </Grid>
          
          <Box mt={1}>
            <LinearProgress 
              variant="determinate" 
              value={(team.storageUsed / team.storageLimit) * 100}
              sx={{ height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" color="text.secondary">
              {team.storageUsed}GB / {team.storageLimit}GB used
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const renderWorkspaceCard = (workspace: Workspace) => (
    <Card key={workspace.id}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="h6" gutterBottom>
              <FolderIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              {workspace.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {workspace.description}
            </Typography>
          </Box>
          <IconButton>
            <MoreVertIcon />
          </IconButton>
        </Box>
        
        <Box mt={2}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Content Items
              </Typography>
              <Typography variant="h6">
                {workspace.contentCount}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Last Activity
              </Typography>
              <Typography variant="body2">
                {workspace.lastActivity}
              </Typography>
            </Grid>
          </Grid>
        </Box>
        
        <Box mt={2} display="flex" justifyContent="space-between">
          <Button startIcon={<ShareIcon />} size="small">
            Share
          </Button>
          <Button startIcon={<EditIcon />} size="small">
            Open
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box p={3}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Team Workspaces
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateTeamOpen(true)}
        >
          Create Team
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Typography variant="h6" gutterBottom>
            Your Teams
          </Typography>
          <Box display="flex" flexDirection="column" gap={2}>
            {teams.map(renderTeamCard)}
          </Box>
        </Grid>

        <Grid item xs={12} md={8}>
          {selectedTeam && (
            <>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h5">
                  {selectedTeam.name}
                </Typography>
                <Box>
                  <Button
                    startIcon={<AddIcon />}
                    onClick={() => setCreateWorkspaceOpen(true)}
                    sx={{ mr: 1 }}
                  >
                    New Workspace
                  </Button>
                  <Button
                    startIcon={<PeopleIcon />}
                    onClick={() => setInviteMemberOpen(true)}
                  >
                    Invite Member
                  </Button>
                </Box>
              </Box>

              <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
                <Tab label="Workspaces" />
                <Tab label="Members" />
                <Tab label="Invitations" />
                <Tab label="Settings" />
              </Tabs>

              <Box mt={2}>
                {activeTab === 0 && (
                  <Grid container spacing={2}>
                    {workspaces.map((workspace) => (
                      <Grid item xs={12} sm={6} key={workspace.id}>
                        {renderWorkspaceCard(workspace)}
                      </Grid>
                    ))}
                  </Grid>
                )}

                {activeTab === 1 && (
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Member</TableCell>
                          <TableCell>Role</TableCell>
                          <TableCell>Last Active</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {selectedTeam.members.map((member) => (
                          <TableRow key={member.id}>
                            <TableCell>
                              <Box display="flex" alignItems="center">
                                <Avatar sx={{ mr: 2 }}>
                                  {member.name.charAt(0)}
                                </Avatar>
                                <Box>
                                  <Typography variant="body2">
                                    {member.name}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {member.email}
                                  </Typography>
                                </Box>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Chip label={member.role} size="small" />
                            </TableCell>
                            <TableCell>{member.lastActive}</TableCell>
                            <TableCell>
                              <Chip 
                                label={member.status} 
                                size="small"
                                color={member.status === 'active' ? 'success' : 'default'}
                              />
                            </TableCell>
                            <TableCell>
                              <IconButton size="small">
                                <EditIcon />
                              </IconButton>
                              <IconButton size="small">
                                <DeleteIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}

                {activeTab === 2 && (
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Email</TableCell>
                          <TableCell>Role</TableCell>
                          <TableCell>Invited By</TableCell>
                          <TableCell>Expires</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {invitations.map((invitation) => (
                          <TableRow key={invitation.id}>
                            <TableCell>{invitation.email}</TableCell>
                            <TableCell>
                              <Chip label={invitation.role} size="small" />
                            </TableCell>
                            <TableCell>{invitation.invitedBy}</TableCell>
                            <TableCell>{invitation.expiresAt}</TableCell>
                            <TableCell>
                              <Chip 
                                label={invitation.status} 
                                size="small"
                                color={invitation.status === 'pending' ? 'warning' : 'default'}
                              />
                            </TableCell>
                            <TableCell>
                              <Button size="small">Resend</Button>
                              <Button size="small" color="error">Cancel</Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Box>
            </>
          )}
        </Grid>
      </Grid>

      {/* Create Team Dialog */}
      <Dialog open={createTeamOpen} onClose={() => setCreateTeamOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Team</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Team Name"
            value={teamForm.name}
            onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description"
            value={teamForm.description}
            onChange={(e) => setTeamForm({ ...teamForm, description: e.target.value })}
            margin="normal"
            multiline
            rows={3}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Subscription Tier</InputLabel>
            <Select
              value={teamForm.subscriptionTier}
              onChange={(e) => setTeamForm({ ...teamForm, subscriptionTier: e.target.value as any })}
            >
              <MenuItem value="free">Free (5 members, 1GB)</MenuItem>
              <MenuItem value="pro">Pro (25 members, 10GB)</MenuItem>
              <MenuItem value="enterprise">Enterprise (100 members, 100GB)</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateTeamOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateTeam} variant="contained" disabled={!teamForm.name}>
            Create Team
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Workspace Dialog */}
      <Dialog open={createWorkspaceOpen} onClose={() => setCreateWorkspaceOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Workspace</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Workspace Name"
            value={workspaceForm.name}
            onChange={(e) => setWorkspaceForm({ ...workspaceForm, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description"
            value={workspaceForm.description}
            onChange={(e) => setWorkspaceForm({ ...workspaceForm, description: e.target.value })}
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateWorkspaceOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateWorkspace} variant="contained" disabled={!workspaceForm.name}>
            Create Workspace
          </Button>
        </DialogActions>
      </Dialog>

      {/* Invite Member Dialog */}
      <Dialog open={inviteMemberOpen} onClose={() => setInviteMemberOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite Team Member</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={inviteForm.email}
            onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
            margin="normal"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Role</InputLabel>
            <Select
              value={inviteForm.role}
              onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
            >
              <MenuItem value="viewer">Viewer</MenuItem>
              <MenuItem value="member">Member</MenuItem>
              <MenuItem value="editor">Editor</MenuItem>
              <MenuItem value="admin">Admin</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteMemberOpen(false)}>Cancel</Button>
          <Button onClick={handleInviteMember} variant="contained" disabled={!inviteForm.email}>
            Send Invitation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <SettingsIcon sx={{ mr: 1 }} />
          Settings
        </MenuItem>
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <AnalyticsIcon sx={{ mr: 1 }} />
          Analytics
        </MenuItem>
        <MenuItem onClick={() => setMenuAnchor(null)}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete Team
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default TeamWorkspaces;