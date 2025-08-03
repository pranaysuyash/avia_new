#!/usr/bin/env node
/**
 * Electron Integration Tests for Team Workspaces
 * Tests the team workspace functionality in the Electron desktop environment
 */

const { Application } = require('spectron');
const path = require('path');
const assert = require('assert');
const { spawn } = require('child_process');

class ElectronTeamWorkspacesTest {
  constructor() {
    this.app = null;
    this.testResults = [];
  }

  async setup() {
    console.log('🚀 Setting up Electron test environment...');
    
    // Start the Electron app
    this.app = new Application({
      path: path.join(__dirname, 'node_modules', '.bin', 'electron'),
      args: [path.join(__dirname, 'electron-main.js')],
      env: {
        NODE_ENV: 'test',
        ELECTRON_IS_DEV: '1'
      },
      startTimeout: 10000,
      waitTimeout: 5000
    });

    await this.app.start();
    console.log('✅ Electron app started successfully');
  }

  async teardown() {
    if (this.app && this.app.isRunning()) {
      await this.app.stop();
      console.log('✅ Electron app stopped');
    }
  }

  async runTest(testName, testFn) {
    console.log(`🧪 Running test: ${testName}`);
    try {
      await testFn();
      this.testResults.push({ name: testName, status: 'PASSED' });
      console.log(`✅ ${testName} - PASSED`);
    } catch (error) {
      this.testResults.push({ name: testName, status: 'FAILED', error: error.message });
      console.log(`❌ ${testName} - FAILED: ${error.message}`);
    }
  }

  async testInitialLoad() {
    await this.runTest('Initial Load', async () => {
      // Wait for the app to load
      await this.app.client.waitUntilWindowLoaded();
      
      // Check if the main window is visible
      const windowCount = await this.app.client.getWindowCount();
      assert.strictEqual(windowCount, 1, 'Should have exactly one window');
      
      // Check if the team workspaces component is loaded
      const title = await this.app.client.getTitle();
      assert(title.includes('Team Workspaces') || title.includes('Audio/Video Transcription'), 
             'Window title should contain app name');
      
      // Wait for the team workspaces interface to load
      await this.app.client.waitForExist('[data-testid="team-workspaces"]', 10000);
    });
  }

  async testTeamCreation() {
    await this.runTest('Team Creation', async () => {
      // Click create team button
      await this.app.client.waitForExist('[data-testid="create-team-button"]', 5000);
      await this.app.client.click('[data-testid="create-team-button"]');
      
      // Wait for modal to appear
      await this.app.client.waitForExist('[data-testid="create-team-modal"]', 5000);
      
      // Fill in team details
      await this.app.client.setValue('[data-testid="team-name-input"]', 'Electron Test Team');
      await this.app.client.setValue('[data-testid="team-description-input"]', 'Test team created from Electron');
      
      // Select subscription tier
      await this.app.client.click('[data-testid="subscription-tier-select"]');
      await this.app.client.click('[data-value="pro"]');
      
      // Submit form
      await this.app.client.click('[data-testid="create-team-submit"]');
      
      // Wait for success message or team to appear in list
      await this.app.client.waitForExist('[data-testid="team-card-electron-test-team"]', 10000);
      
      // Verify team was created
      const teamName = await this.app.client.getText('[data-testid="team-card-electron-test-team"] [data-testid="team-name"]');
      assert.strictEqual(teamName, 'Electron Test Team', 'Team should be created with correct name');
    });
  }

  async testWorkspaceManagement() {
    await this.runTest('Workspace Management', async () => {
      // Select the created team
      await this.app.client.click('[data-testid="team-card-electron-test-team"]');
      
      // Wait for team details to load
      await this.app.client.waitForExist('[data-testid="team-details"]', 5000);
      
      // Create new workspace
      await this.app.client.click('[data-testid="create-workspace-button"]');
      await this.app.client.waitForExist('[data-testid="create-workspace-modal"]', 5000);
      
      // Fill workspace details
      await this.app.client.setValue('[data-testid="workspace-name-input"]', 'Electron Test Workspace');
      await this.app.client.setValue('[data-testid="workspace-description-input"]', 'Test workspace from Electron');
      
      // Submit
      await this.app.client.click('[data-testid="create-workspace-submit"]');
      
      // Verify workspace appears
      await this.app.client.waitForExist('[data-testid="workspace-card-electron-test-workspace"]', 10000);
      
      const workspaceName = await this.app.client.getText('[data-testid="workspace-card-electron-test-workspace"] [data-testid="workspace-name"]');
      assert.strictEqual(workspaceName, 'Electron Test Workspace', 'Workspace should be created with correct name');
    });
  }

  async testMemberInvitation() {
    await this.runTest('Member Invitation', async () => {
      // Click invite member button
      await this.app.client.click('[data-testid="invite-member-button"]');
      await this.app.client.waitForExist('[data-testid="invite-member-modal"]', 5000);
      
      // Fill invitation details
      await this.app.client.setValue('[data-testid="invite-email-input"]', 'test@electron.com');
      
      // Select role
      await this.app.client.click('[data-testid="invite-role-select"]');
      await this.app.client.click('[data-value="editor"]');
      
      // Send invitation
      await this.app.client.click('[data-testid="send-invitation-button"]');
      
      // Switch to invitations tab
      await this.app.client.click('[data-testid="invitations-tab"]');
      
      // Verify invitation appears
      await this.app.client.waitForExist('[data-testid="invitation-test@electron.com"]', 10000);
      
      const invitationEmail = await this.app.client.getText('[data-testid="invitation-test@electron.com"] [data-testid="invitation-email"]');
      assert.strictEqual(invitationEmail, 'test@electron.com', 'Invitation should be created for correct email');
    });
  }

  async testTabNavigation() {
    await this.runTest('Tab Navigation', async () => {
      // Test switching between tabs
      const tabs = ['workspaces-tab', 'members-tab', 'invitations-tab', 'settings-tab'];
      
      for (const tab of tabs) {
        await this.app.client.click(`[data-testid="${tab}"]`);
        await this.app.client.waitForExist(`[data-testid="${tab}-content"]`, 5000);
        
        // Verify tab is active
        const isActive = await this.app.client.getAttribute(`[data-testid="${tab}"]`, 'aria-selected');
        assert.strictEqual(isActive, 'true', `${tab} should be active when clicked`);
      }
    });
  }

  async testKeyboardNavigation() {
    await this.runTest('Keyboard Navigation', async () => {
      // Test keyboard shortcuts
      await this.app.client.keys(['Control', 't']); // Ctrl+T for new team
      await this.app.client.waitForExist('[data-testid="create-team-modal"]', 5000);
      
      // Close modal with Escape
      await this.app.client.keys('Escape');
      await this.app.client.waitForExist('[data-testid="create-team-modal"]', 1000, true); // Wait for it to disappear
      
      // Test Tab navigation
      await this.app.client.keys('Tab');
      const focusedElement = await this.app.client.execute(() => document.activeElement.getAttribute('data-testid'));
      assert(focusedElement, 'Should have a focused element after Tab key');
    });
  }

  async testWindowManagement() {
    await this.runTest('Window Management', async () => {
      // Test window resizing
      await this.app.browserWindow.setSize(1200, 800);
      const size = await this.app.browserWindow.getSize();
      assert.strictEqual(size[0], 1200, 'Window width should be 1200');
      assert.strictEqual(size[1], 800, 'Window height should be 800');
      
      // Test minimizing and restoring
      await this.app.browserWindow.minimize();
      const isMinimized = await this.app.browserWindow.isMinimized();
      assert.strictEqual(isMinimized, true, 'Window should be minimized');
      
      await this.app.browserWindow.restore();
      const isVisible = await this.app.browserWindow.isVisible();
      assert.strictEqual(isVisible, true, 'Window should be visible after restore');
    });
  }

  async testDataPersistence() {
    await this.runTest('Data Persistence', async () => {
      // Create some data
      await this.app.client.click('[data-testid="create-team-button"]');
      await this.app.client.waitForExist('[data-testid="create-team-modal"]', 5000);
      await this.app.client.setValue('[data-testid="team-name-input"]', 'Persistence Test Team');
      await this.app.client.click('[data-testid="create-team-submit"]');
      
      // Wait for team to be created
      await this.app.client.waitForExist('[data-testid="team-card-persistence-test-team"]', 10000);
      
      // Restart the app
      await this.app.restart();
      await this.app.client.waitUntilWindowLoaded();
      
      // Check if data persisted
      await this.app.client.waitForExist('[data-testid="team-card-persistence-test-team"]', 10000);
      const teamName = await this.app.client.getText('[data-testid="team-card-persistence-test-team"] [data-testid="team-name"]');
      assert.strictEqual(teamName, 'Persistence Test Team', 'Team data should persist after restart');
    });
  }

  async testOfflineMode() {
    await this.runTest('Offline Mode', async () => {
      // Simulate offline mode
      await this.app.client.execute(() => {
        // Mock fetch to simulate network failure
        window.fetch = () => Promise.reject(new Error('Network unavailable'));
      });
      
      // Try to create a team (should show offline message)
      await this.app.client.click('[data-testid="create-team-button"]');
      await this.app.client.waitForExist('[data-testid="create-team-modal"]', 5000);
      await this.app.client.setValue('[data-testid="team-name-input"]', 'Offline Test Team');
      await this.app.client.click('[data-testid="create-team-submit"]');
      
      // Should show offline error
      await this.app.client.waitForExist('[data-testid="offline-error"]', 5000);
      const errorMessage = await this.app.client.getText('[data-testid="offline-error"]');
      assert(errorMessage.includes('offline') || errorMessage.includes('network'), 
             'Should show offline/network error message');
    });
  }

  async testPerformance() {
    await this.runTest('Performance', async () => {
      // Measure initial load time
      const startTime = Date.now();
      await this.app.client.waitForExist('[data-testid="team-workspaces"]', 10000);
      const loadTime = Date.now() - startTime;
      
      assert(loadTime < 5000, `Initial load should be under 5 seconds, was ${loadTime}ms`);
      
      // Test with large dataset
      await this.app.client.execute(() => {
        // Mock large team list
        const largeTeamList = Array.from({ length: 100 }, (_, i) => ({
          id: `team${i}`,
          name: `Team ${i}`,
          description: `Description for team ${i}`,
          memberCount: Math.floor(Math.random() * 50),
          workspaceCount: Math.floor(Math.random() * 10),
          storageUsed: Math.random() * 100,
          storageLimit: 100,
          subscriptionTier: 'pro',
          role: 'member'
        }));
        
        // Simulate API response
        window.mockTeamData = largeTeamList;
      });
      
      // Refresh to load large dataset
      await this.app.client.refresh();
      await this.app.client.waitForExist('[data-testid="team-workspaces"]', 10000);
      
      // Measure rendering time for large dataset
      const renderStartTime = Date.now();
      await this.app.client.waitForExist('[data-testid="team-card-team99"]', 10000);
      const renderTime = Date.now() - renderStartTime;
      
      assert(renderTime < 3000, `Large dataset rendering should be under 3 seconds, was ${renderTime}ms`);
    });
  }

  async testAccessibility() {
    await this.runTest('Accessibility', async () => {
      // Check for ARIA labels
      const createButton = await this.app.client.getAttribute('[data-testid="create-team-button"]', 'aria-label');
      assert(createButton, 'Create team button should have aria-label');
      
      // Check for keyboard accessibility
      await this.app.client.keys('Tab');
      const focusedElement = await this.app.client.execute(() => document.activeElement);
      assert(focusedElement, 'Should be able to focus elements with keyboard');
      
      // Check color contrast (basic test)
      const backgroundColor = await this.app.client.getCssProperty('body', 'background-color');
      const textColor = await this.app.client.getCssProperty('body', 'color');
      assert(backgroundColor.value !== textColor.value, 'Background and text colors should be different');
    });
  }

  async runAllTests() {
    console.log('🎯 Starting Electron Team Workspaces Tests...\n');
    
    try {
      await this.setup();
      
      // Run all tests
      await this.testInitialLoad();
      await this.testTeamCreation();
      await this.testWorkspaceManagement();
      await this.testMemberInvitation();
      await this.testTabNavigation();
      await this.testKeyboardNavigation();
      await this.testWindowManagement();
      await this.testDataPersistence();
      await this.testOfflineMode();
      await this.testPerformance();
      await this.testAccessibility();
      
    } catch (error) {
      console.error('❌ Test setup failed:', error);
    } finally {
      await this.teardown();
    }
    
    // Print results
    console.log('\n📊 Test Results Summary:');
    console.log('========================');
    
    const passed = this.testResults.filter(r => r.status === 'PASSED').length;
    const failed = this.testResults.filter(r => r.status === 'FAILED').length;
    
    this.testResults.forEach(result => {
      const icon = result.status === 'PASSED' ? '✅' : '❌';
      console.log(`${icon} ${result.name}: ${result.status}`);
      if (result.error) {
        console.log(`   Error: ${result.error}`);
      }
    });
    
    console.log(`\nTotal: ${this.testResults.length} tests`);
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Success Rate: ${((passed / this.testResults.length) * 100).toFixed(1)}%`);
    
    if (failed > 0) {
      process.exit(1);
    } else {
      console.log('\n🎉 All tests passed!');
      process.exit(0);
    }
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const tester = new ElectronTeamWorkspacesTest();
  tester.runAllTests().catch(error => {
    console.error('❌ Test runner failed:', error);
    process.exit(1);
  });
}

module.exports = ElectronTeamWorkspacesTest;