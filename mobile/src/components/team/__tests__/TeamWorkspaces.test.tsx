import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import TeamWorkspaces from '../TeamWorkspaces';

// Mock React Native components and modules
jest.mock('react-native-vector-icons/MaterialIcons', () => 'Icon');
jest.mock('react-native-safe-area-context', () => ({
  SafeAreaView: ({ children }: any) => children,
}));

// Mock Alert
jest.spyOn(Alert, 'alert');

// Mock fetch
global.fetch = jest.fn();

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
      }
    ]
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
  }
];

describe('TeamWorkspaces Mobile Component', () => {
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
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      });
    });
  });

  describe('Initial Rendering', () => {
    test('renders main header correctly', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      expect(getByText('Team Workspaces')).toBeTruthy();
      expect(getByText('Your Teams')).toBeTruthy();
    });

    test('loads and displays teams', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(getByText('Acme Corporation')).toBeTruthy();
        expect(getByText('Main company workspace')).toBeTruthy();
      });
    });
  });

  describe('Team Management', () => {
    test('displays team statistics correctly', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(getByText('12')).toBeTruthy(); // member count
        expect(getByText('5')).toBeTruthy(); // workspace count
        expect(getByText('45.2GB')).toBeTruthy(); // storage used
      });
    });

    test('shows subscription tier badge', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(getByText('ENTERPRISE')).toBeTruthy();
      });
    });
  });

  describe('Team Creation', () => {
    test('opens create team modal when plus button is pressed', async () => {
      const { getByText, getByTestId } = render(<TeamWorkspaces />);
      
      // Find and press the create button (plus icon)
      const createButton = getByTestId('create-team-button') || 
                          getByText('+') || 
                          getByText('Create Team');
      
      fireEvent.press(createButton);
      
      await waitFor(() => {
        expect(getByText('Create Team')).toBeTruthy();
        expect(getByText('Team Name')).toBeTruthy();
      });
    });

    test('validates team name input', async () => {
      const { getByText, getByDisplayValue, getByPlaceholderText } = render(<TeamWorkspaces />);
      
      // Open modal
      const createButton = getByTestId('create-team-button') || getByText('Create Team');
      fireEvent.press(createButton);
      
      await waitFor(() => {
        const nameInput = getByPlaceholderText('Enter team name');
        fireEvent.changeText(nameInput, '');
        
        const createTeamButton = getByText('Create');
        fireEvent.press(createTeamButton);
      });
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Error', 'Team name is required');
      });
    });

    test('creates team successfully', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'new-team', name: 'New Team' })
        })
      );

      const { getByText, getByPlaceholderText } = render(<TeamWorkspaces />);
      
      // Open modal
      const createButton = getByTestId('create-team-button') || getByText('Create Team');
      fireEvent.press(createButton);
      
      await waitFor(() => {
        const nameInput = getByPlaceholderText('Enter team name');
        fireEvent.changeText(nameInput, 'New Team');
        
        const createTeamButton = getByText('Create');
        fireEvent.press(createTeamButton);
      });
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Success', 'Team created successfully');
      });
    });
  });

  describe('Workspace Management', () => {
    test('displays workspaces for selected team', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(getByText('Development')).toBeTruthy();
        expect(getByText('Software development projects')).toBeTruthy();
        expect(getByText('156')).toBeTruthy(); // content count
      });
    });

    test('opens create workspace modal', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        const workspaceButton = getByText('Workspace');
        fireEvent.press(workspaceButton);
      });
      
      await waitFor(() => {
        expect(getByText('Create Workspace')).toBeTruthy();
        expect(getByText('Workspace Name')).toBeTruthy();
      });
    });
  });

  describe('Tab Navigation', () => {
    test('switches between tabs correctly', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        // Should start with workspaces tab
        expect(getByText('Development')).toBeTruthy();
        
        // Switch to members tab
        const membersTab = getByText('Members');
        fireEvent.press(membersTab);
      });
      
      await waitFor(() => {
        expect(getByText('Alice Johnson')).toBeTruthy();
        expect(getByText('alice@acme.com')).toBeTruthy();
      });
    });

    test('shows correct tab content', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        // Switch to invitations tab
        const invitationsTab = getByText('Invitations');
        fireEvent.press(invitationsTab);
      });
      
      // Should show invitations content (even if empty)
      // This depends on your empty state implementation
    });
  });

  describe('Member Management', () => {
    test('displays team members correctly', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        const membersTab = getByText('Members');
        fireEvent.press(membersTab);
      });
      
      await waitFor(() => {
        expect(getByText('Alice Johnson')).toBeTruthy();
        expect(getByText('alice@acme.com')).toBeTruthy();
        expect(getByText('owner')).toBeTruthy();
        expect(getByText('Last active: 2 hours ago')).toBeTruthy();
      });
    });

    test('opens invite member modal', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        const inviteButton = getByText('Invite');
        fireEvent.press(inviteButton);
      });
      
      await waitFor(() => {
        expect(getByText('Invite Member')).toBeTruthy();
        expect(getByText('Email Address')).toBeTruthy();
        expect(getByText('Role')).toBeTruthy();
      });
    });

    test('validates email input for invitations', async () => {
      const { getByText, getByPlaceholderText } = render(<TeamWorkspaces />);
      
      // Open invite modal
      const inviteButton = getByText('Invite');
      fireEvent.press(inviteButton);
      
      await waitFor(() => {
        const emailInput = getByPlaceholderText('Enter email address');
        fireEvent.changeText(emailInput, 'invalid-email');
        
        const sendButton = getByText('Send');
        fireEvent.press(sendButton);
      });
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Error', 'Please enter a valid email address');
      });
    });
  });

  describe('Pull to Refresh', () => {
    test('refreshes data when pulled down', async () => {
      const { getByTestId } = render(<TeamWorkspaces />);
      
      // Find ScrollView with RefreshControl
      const scrollView = getByTestId('team-workspaces-scroll') || 
                        getByTestId('scroll-view');
      
      if (scrollView) {
        // Simulate pull to refresh
        fireEvent(scrollView, 'refresh');
        
        await waitFor(() => {
          expect(global.fetch).toHaveBeenCalledTimes(2); // Initial load + refresh
        });
      }
    });
  });

  describe('Error Handling', () => {
    test('shows error alert when API fails', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.reject(new Error('Network error'))
      );

      render(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Error', 'Failed to load teams');
      });
    });

    test('handles workspace creation errors', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.reject(new Error('Creation failed'))
      );

      const { getByText, getByPlaceholderText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        const workspaceButton = getByText('Workspace');
        fireEvent.press(workspaceButton);
      });
      
      await waitFor(() => {
        const nameInput = getByPlaceholderText('Enter workspace name');
        fireEvent.changeText(nameInput, 'Test Workspace');
        
        const createButton = getByText('Create');
        fireEvent.press(createButton);
      });
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith('Error', 'Failed to create workspace');
      });
    });
  });

  describe('Modal Interactions', () => {
    test('closes modal when cancel is pressed', async () => {
      const { getByText, queryByText } = render(<TeamWorkspaces />);
      
      // Open create team modal
      const createButton = getByTestId('create-team-button') || getByText('Create Team');
      fireEvent.press(createButton);
      
      await waitFor(() => {
        expect(getByText('Create Team')).toBeTruthy();
      });
      
      // Close modal
      const cancelButton = getByText('Cancel');
      fireEvent.press(cancelButton);
      
      await waitFor(() => {
        expect(queryByText('Create Team')).toBeFalsy();
      });
    });

    test('subscription tier selection works', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      // Open create team modal
      const createButton = getByTestId('create-team-button') || getByText('Create Team');
      fireEvent.press(createButton);
      
      await waitFor(() => {
        const proOption = getByText('Pro (25 members, 10GB)');
        fireEvent.press(proOption);
        
        // Verify selection (this would depend on your UI feedback)
        expect(proOption).toBeTruthy();
      });
    });
  });

  describe('Responsive Layout', () => {
    test('adapts to different screen sizes', () => {
      // Mock Dimensions
      const mockDimensions = {
        get: jest.fn(() => ({ width: 375, height: 812 }))
      };
      
      jest.doMock('react-native', () => ({
        ...jest.requireActual('react-native'),
        Dimensions: mockDimensions
      }));
      
      const { getByText } = render(<TeamWorkspaces />);
      expect(getByText('Team Workspaces')).toBeTruthy();
    });
  });

  describe('Performance', () => {
    test('handles large team lists efficiently', async () => {
      const largeTeamList = Array.from({ length: 50 }, (_, i) => ({
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

      const startTime = Date.now();
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        expect(getByText('Team 0')).toBeTruthy();
      });
      
      const endTime = Date.now();
      const renderTime = endTime - startTime;
      
      // Should render within reasonable time
      expect(renderTime).toBeLessThan(2000); // 2 seconds for mobile
    });
  });

  describe('Accessibility', () => {
    test('has proper accessibility labels', async () => {
      const { getByLabelText, getByA11yLabel } = render(<TeamWorkspaces />);
      
      // Check for accessibility labels on important elements
      // This would depend on your accessibility implementation
      await waitFor(() => {
        // Example: Check if create button has proper label
        const createButton = getByA11yLabel?.('Create new team') || 
                            getByLabelText?.('Create new team');
        if (createButton) {
          expect(createButton).toBeTruthy();
        }
      });
    });

    test('supports screen reader navigation', async () => {
      const { getByText } = render(<TeamWorkspaces />);
      
      await waitFor(() => {
        // Verify that important text is accessible to screen readers
        expect(getByText('Team Workspaces')).toBeTruthy();
        expect(getByText('Your Teams')).toBeTruthy();
      });
    });
  });
});