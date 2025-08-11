import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login form for unauthenticated users', async ({ page }) => {
    // Check for login elements
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button:has-text("Login")')).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    // Fill login form
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    
    // Click login button
    await page.click('button:has-text("Login")');
    
    // Wait for navigation or loading state
    await page.waitForLoadState('networkidle');
    
    // Check for authenticated state
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill login form with invalid credentials
    await page.fill('input[type="email"]', 'invalid@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    
    // Click login button
    await page.click('button:has-text("Login")');
    
    // Check for error message
    await expect(page.locator('text=/Invalid credentials|Login failed/i')).toBeVisible();
  });

  test('should logout successfully', async ({ page, context }) => {
    // First login
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button:has-text("Login")');
    await page.waitForLoadState('networkidle');
    
    // Click logout button
    await page.click('button:has-text("Logout")');
    
    // Check redirected to login
    await expect(page.locator('input[type="email"]')).toBeVisible();
    
    // Check localStorage is cleared
    const token = await page.evaluate(() => localStorage.getItem('auth_tokens'));
    expect(token).toBeNull();
  });

  test('should persist authentication on page refresh', async ({ page }) => {
    // Login
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button:has-text("Login")');
    await page.waitForLoadState('networkidle');
    
    // Refresh page
    await page.reload();
    
    // Should still be authenticated
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });
});