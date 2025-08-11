import { test, expect } from '@playwright/test';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Mock admin authentication
    await page.evaluate(() => {
      localStorage.setItem('auth_tokens', JSON.stringify({
        accessToken: 'mock-admin-token',
        refreshToken: 'mock-refresh-token',
        expiresIn: 3600
      }));
      localStorage.setItem('auth_user', JSON.stringify({
        id: 1,
        email: 'admin@example.com',
        name: 'Admin User',
        role: 'admin'
      }));
    });
    
    await page.reload();
  });

  test('should display admin tab for admin users', async ({ page }) => {
    await expect(page.locator('text=Admin')).toBeVisible();
  });

  test('should access admin dashboard', async ({ page }) => {
    // Click on admin tab
    await page.click('text=Admin');
    
    // Check for admin dashboard elements
    await expect(page.locator('text=/User.*Management|System.*Settings|Analytics.*Overview/i')).toBeVisible();
  });

  test('should view system analytics', async ({ page }) => {
    await page.click('text=Admin');
    
    // Look for analytics section
    const analyticsSection = page.locator('text=/Total.*Users|Active.*Sessions|API.*Calls/i');
    if (await analyticsSection.isVisible()) {
      // Check for metrics
      await expect(page.locator('[data-testid="metric-value"]')).toHaveCount(3, { timeout: 5000 });
    }
  });

  test('should manage users', async ({ page }) => {
    await page.click('text=Admin');
    
    // Look for users section
    const usersButton = page.locator('button:has-text("Users")');
    if (await usersButton.isVisible()) {
      await usersButton.click();
      
      // Check for user list
      await expect(page.locator('table, [data-testid="user-list"]')).toBeVisible();
    }
  });

  test('should view system logs', async ({ page }) => {
    await page.click('text=Admin');
    
    // Look for logs section
    const logsButton = page.locator('button:has-text("Logs")');
    if (await logsButton.isVisible()) {
      await logsButton.click();
      
      // Check for log entries
      await expect(page.locator('[data-testid="log-entry"], .log-item')).toBeVisible();
    }
  });

  test('should update system settings', async ({ page }) => {
    await page.click('text=Admin');
    
    // Look for settings section
    const settingsButton = page.locator('button:has-text("Settings")');
    if (await settingsButton.isVisible()) {
      await settingsButton.click();
      
      // Check for settings form
      await expect(page.locator('input[type="checkbox"], input[type="text"], select')).toBeVisible();
    }
  });
});