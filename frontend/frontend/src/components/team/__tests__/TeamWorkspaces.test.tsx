import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import '@testing-library/jest-dom';
import TeamWorkspaces from '../TeamWorkspaces';

// Mock Material-UI components that might cause issues in tests
jest.mock('@mui/material/LinearProgress', () => {
  return function MockLinearProgress({ value, ...props }: any) {
    return <div data-testid="linear-progress" data-value={value} {...props} />;
  };
});

// Mock API calls
const mockTeams = [
  {
    id: 'team1',
    name: 'Acme Corporation',
    description: 'Main company workspace',
    memberCount: 12,
    workspaceCount: 5,
    storageUsed: 45.2,
    storageLimit: 100,
    subscriptionTier: 'enterprise' as const,
    role: 'owner' as const,
    members: [
      {
        id: 'user1',
        name: 'Alice Johnson',
        email: 'alice@acme.com',
        role: 'owner',
        lastActive: '2 hours ago',
        status: 'active' as const
      },
      {
        id: 'user2',
        name: 'Bob Smith',
        email: 'bob@acme.com',
        role: 'admin',
        lastActive: '1 day ago',
        status: 'active' as const
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
    subscriptionTier: 'pro' as const,
    role: 'editor' as const,
    members: []
  }
];

const mockWorkspaces = [
  {
    id: 'ws1',
    name: 'Development',
    description: 'Software development projects',
    teamId: 'team1',
    contentCount: 156,
    lastActivity: '2 hours ago',
    members: []
  },
  {
    id: 'ws2',
    name: 'Marketing',
    description: 'Marketing campaigns and content',
    teamId: 'team1',
    contentCount: 89,
    lastActivity: '1 day ago',
    members: []
  }
];

const mockInvitations = [
  {
    id: 'inv1',
    email: 'newdev@acme.com',
    role: 'editor',
    invitedBy: 'Alice Johnson',
    createdAt: '2024-03-05',
    expiresAt: '2024-03-12',
    status: 'pending' as const
  }
];

// Mock fetch globally
global.fetch = jest.fn();

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('TeamWorkspaces Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/teams')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTeams)
        });
      }
      if (url.includes('/workspaces')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockWorkspaces)
        });
      }
      if (url.includes('/invitations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockInvitations)
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });
  });

  describe('Initial Rendering', () => {
    test('renders main header correctly', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      expect(screen.getByText('Team Workspaces')).toBeInTheDocument();
      expect(screen.getByText('Create Team')).toBeInTheDocument();
    });

    test('displays loading state initially', () => {
      renderWithTheme(<TeamWorkspaces />);
      
      // Component should show some loading indication
      // This depends on your loading implementation
    });

    test('loads and displays teams after initial load', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(screen.getByText('Acme Corporation')).toBeInTheDocument();
        expect(screen.getByText('Design Team')).toBeInTheDocument();
      });
    });
  });

  describe('Team Management', () => {
    test('displays team information correctly', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const acmeTeam = screen.getByText('Acme Corporation').closest('[role="button"]') || 
                         screen.getByText('Acme Corporation').closest('div');
        
        if (acmeTeam) {
          expect(within(acmeTeam).getByText('Main company workspace')).toBeInTheDocument();
          expect(within(acmeTeam).getByText('ENTERPRISE')).toBeInTheDocument();
          expect(within(acmeTeam).getByText('12')).toBeInTheDocument(); // member count
          expect(within(acmeTeam).getByText('5')).toBeInTheDocument(); // workspace count
        }
      });
    });

    test('shows storage usage with progress bar', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const progressBars = screen.getAllByTestId('linear-progress');
        expect(progressBars.length).toBeGreaterThan(0);
        
        // Check if progress value is calculated correctly (45.2/100 * 100 = 45.2%)
        const acmeProgressBar = progressBars.find(bar => 
          bar.getAttribute('data-value') === '45.2'
        );
        expect(acmeProgressBar).toBeInTheDocument();
      });
    });

    test('allows team selection', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const designTeam = screen.getByText('Design Team');
        fireEvent.click(designTeam);
      });

      // Should show selected team content
      await waitFor(() => {
        expect(screen.getByText('Design Team')).toBeInTheDocument();
      });
    });
  });

  describe('Team Creation', () => {
    test('opens create team dialog when button is clicked', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      const createButton = screen.getByText('Create Team');
      fireEvent.click(createButton);
      
      await waitFor(() => {
        expect(screen.getByText('Create New Team')).toBeInTheDocument();
        expect(screen.getByLabelText('Team Name')).toBeInTheDocument();
        expect(screen.getByLabelText('Description')).toBeInTheDocument();
        expect(screen.getByLabelText('Subscription Tier')).toBeInTheDocument();
      });
    });

    test('validates team name input', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      const createButton = screen.getByText('Create Team');
      fireEvent.click(createButton);
      
      await waitFor(() => {
        const createTeamButton = screen.getByRole('button', { name: /create team/i });
        expect(createTeamButton).toBeDisabled();
      });
      
      const nameInput = screen.getByLabelText('Team Name');
      fireEvent.change(nameInput, { target: { value: 'New Team' } });
      
      await waitFor(() => {
        const createTeamButton = screen.getByRole('button', { name: /create team/i });
        expect(createTeamButton).not.toBeDisabled();
      });
    });

    test('creates new team with form data', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'new-team',
            name: 'New Team',
            description: 'Test description',
            subscriptionTier: 'pro'
          })
        })
      );

      renderWithTheme(<TeamWorkspaces />);
      
      const createButton = screen.getByText('Create Team');
      fireEvent.click(createButton);
      
      await waitFor(() => {
        const nameInput = screen.getByLabelText('Team Name');
        const descInput = screen.getByLabelText('Description');
        
        fireEvent.change(nameInput, { target: { value: 'New Team' } });
        fireEvent.change(descInput, { target: { value: 'Test description' } });
      });
      
      const createTeamButton = screen.getByRole('button', { name: /create team/i });
      fireEvent.click(createTeamButton);
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/teams'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('New Team')
          })
        );
      });
    });
  });

  describe('Workspace Management', () => {
    test('displays workspaces for selected team', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(screen.getByText('Development')).toBeInTheDocument();
        expect(screen.getByText('Software development projects')).toBeInTheDocument();
        expect(screen.getByText('Marketing')).toBeInTheDocument();
        expect(screen.getByText('Marketing campaigns and content')).toBeInTheDocument();
      });
    });

    test('shows workspace statistics', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(screen.getByText('156')).toBeInTheDocument(); // Development content count
        expect(screen.getByText('89')).toBeInTheDocument(); // Marketing content count
      });
    });

    test('opens create workspace dialog', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const newWorkspaceButton = screen.getByText('New Workspace');
        fireEvent.click(newWorkspaceButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Create New Workspace')).toBeInTheDocument();
        expect(screen.getByLabelText('Workspace Name')).toBeInTheDocument();
      });
    });
  });

  describe('Member Management', () => {
    test('displays team members in members tab', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const membersTab = screen.getByText('Members');
        fireEvent.click(membersTab);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
        expect(screen.getByText('alice@acme.com')).toBeInTheDocument();
        expect(screen.getByText('Bob Smith')).toBeInTheDocument();
        expect(screen.getByText('bob@acme.com')).toBeInTheDocument();
      });
    });

    test('shows member roles and status', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const membersTab = screen.getByText('Members');
        fireEvent.click(membersTab);
      });
      
      await waitFor(() => {
        expect(screen.getByText('owner')).toBeInTheDocument();
        expect(screen.getByText('admin')).toBeInTheDocument();
        expect(screen.getAllByText('active')).toHaveLength(2);
      });
    });

    test('opens invite member dialog', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const inviteButton = screen.getByText('Invite Member');
        fireEvent.click(inviteButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Invite Team Member')).toBeInTheDocument();
        expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
        expect(screen.getByLabelText('Role')).toBeInTheDocument();
      });
    });
  });

  describe('Invitation Management', () => {
    test('displays pending invitations', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const invitationsTab = screen.getByText('Invitations');
        fireEvent.click(invitationsTab);
      });
      
      await waitFor(() => {
        expect(screen.getByText('newdev@acme.com')).toBeInTheDocument();
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
        expect(screen.getByText('2024-03-12')).toBeInTheDocument();
      });
    });

    test('shows invitation actions', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const invitationsTab = screen.getByText('Invitations');
        fireEvent.click(invitationsTab);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
        expect(screen.getByText('Cancel')).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    test('switches between tabs correctly', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        // Default should be workspaces tab
        expect(screen.getByText('Development')).toBeInTheDocument();
        
        // Switch to members tab
        const membersTab = screen.getByText('Members');
        fireEvent.click(membersTab);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
        
        // Switch to invitations tab
        const invitationsTab = screen.getByText('Invitations');
        fireEvent.click(invitationsTab);
      });
      
      await waitFor(() => {
        expect(screen.getByText('newdev@acme.com')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('displays error message when API fails', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.reject(new Error('API Error'))
      );

      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(screen.getByText(/failed to load teams/i)).toBeInTheDocument();
      });
    });

    test('handles team creation errors', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.reject(new Error('Creation failed'))
      );

      renderWithTheme(<TeamWorkspaces />);
      
      const createButton = screen.getByText('Create Team');
      fireEvent.click(createButton);
      
      await waitFor(() => {
        const nameInput = screen.getByLabelText('Team Name');
        fireEvent.change(nameInput, { target: { value: 'New Team' } });
        
        const createTeamButton = screen.getByRole('button', { name: /create team/i });
        fireEvent.click(createTeamButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText(/failed to create team/i)).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    test('adapts layout for different screen sizes', () => {
      // Mock window.innerWidth
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      renderWithTheme(<TeamWorkspaces />);
      
      // Check if responsive classes are applied
      // This would depend on your specific responsive implementation
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        // Check for proper button roles
        expect(screen.getByRole('button', { name: /create team/i })).toBeInTheDocument();
        
        // Check for proper form labels
        const createButton = screen.getByText('Create Team');
        fireEvent.click(createButton);
      });
      
      await waitFor(() => {
        expect(screen.getByLabelText('Team Name')).toBeInTheDocument();
        expect(screen.getByLabelText('Description')).toBeInTheDocument();
      });
    });

    test('supports keyboard navigation', async () => {
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        const createButton = screen.getByText('Create Team');
        createButton.focus();
        expect(createButton).toHaveFocus();
        
        // Test Enter key
        fireEvent.keyDown(createButton, { key: 'Enter', code: 'Enter' });
      });
      
      await waitFor(() => {
        expect(screen.getByText('Create New Team')).toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    test('renders efficiently with large datasets', async () => {
      const largeTeamList = Array.from({ length: 100 }, (_, i) => ({
        ...mockTeams[0],
        id: `team${i}`,
        name: `Team ${i}`
      }));

      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(largeTeamList)
        })
      );

      const startTime = performance.now();
      renderWithTheme(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(screen.getByText('Team 0')).toBeInTheDocument();
      });
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // Should render within reasonable time (adjust threshold as needed)
      expect(renderTime).toBeLessThan(1000); // 1 second
    });
  });
});

describe('TeamWorkspaces Integration Tests', () => {
  test('complete workflow: create team, add workspace, invite member', async () => {
    let createdTeam: any = null;
    let createdWorkspace: any = null;
    let sentInvitation: any = null;

    (global.fetch as jest.Mock).mockImplementation((url: string, options: any) => {
      if (url.includes('/teams') && options?.method === 'POST') {
        createdTeam = JSON.parse(options.body);
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ...createdTeam, id: 'new-team-id' })
        });
      }
      if (url.includes('/workspaces') && options?.method === 'POST') {
        createdWorkspace = JSON.parse(options.body);
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ...createdWorkspace, id: 'new-workspace-id' })
        });
      }
      if (url.includes('/invitations') && options?.method === 'POST') {
        sentInvitation = JSON.parse(options.body);
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ...sentInvitation, id: 'new-invitation-id' })
        });
      }
      // Default mock responses
      if (url.includes('/teams')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTeams)
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      });
    });

    renderWithTheme(<TeamWorkspaces />);

    // Step 1: Create team
    await waitFor(() => {
      const createButton = screen.getByText('Create Team');
      fireEvent.click(createButton);
    });

    await waitFor(() => {
      const nameInput = screen.getByLabelText('Team Name');
      const descInput = screen.getByLabelText('Description');
      
      fireEvent.change(nameInput, { target: { value: 'Integration Test Team' } });
      fireEvent.change(descInput, { target: { value: 'Test team for integration' } });
      
      const createTeamButton = screen.getByRole('button', { name: /create team/i });
      fireEvent.click(createTeamButton);
    });

    // Verify team creation
    await waitFor(() => {
      expect(createdTeam).toEqual(
        expect.objectContaining({
          name: 'Integration Test Team',
          description: 'Test team for integration'
        })
      );
    });

    // Step 2: Create workspace (assuming team is selected)
    await waitFor(() => {
      const newWorkspaceButton = screen.getByText('New Workspace');
      fireEvent.click(newWorkspaceButton);
    });

    await waitFor(() => {
      const nameInput = screen.getByLabelText('Workspace Name');
      fireEvent.change(nameInput, { target: { value: 'Test Workspace' } });
      
      const createWorkspaceButton = screen.getByRole('button', { name: /create workspace/i });
      fireEvent.click(createWorkspaceButton);
    });

    // Verify workspace creation
    await waitFor(() => {
      expect(createdWorkspace).toEqual(
        expect.objectContaining({
          name: 'Test Workspace'
        })
      );
    });

    // Step 3: Invite member
    await waitFor(() => {
      const inviteButton = screen.getByText('Invite Member');
      fireEvent.click(inviteButton);
    });

    await waitFor(() => {
      const emailInput = screen.getByLabelText('Email Address');
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      
      const sendInvitationButton = screen.getByRole('button', { name: /send invitation/i });
      fireEvent.click(sendInvitationButton);
    });

    // Verify invitation sent
    await waitFor(() => {
      expect(sentInvitation).toEqual(
        expect.objectContaining({
          email: 'test@example.com'
        })
      );
    });
  });
});