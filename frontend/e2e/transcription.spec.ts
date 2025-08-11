import { test, expect } from '@playwright/test';

test.describe('Transcription Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Mock authentication
    await page.evaluate(() => {
      localStorage.setItem('auth_tokens', JSON.stringify({
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        expiresIn: 3600
      }));
      localStorage.setItem('auth_user', JSON.stringify({
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        role: 'user'
      }));
    });
    
    await page.reload();
  });

  test('should display transcriptions list', async ({ page }) => {
    // Navigate to transcriptions tab
    await page.click('text=Transcriptions');
    
    // Check for transcriptions list or empty state
    const hasTranscriptions = await page.locator('.transcription-item').count() > 0;
    const hasEmptyState = await page.locator('text=/No transcriptions|Upload.*first.*file/i').isVisible();
    
    expect(hasTranscriptions || hasEmptyState).toBeTruthy();
  });

  test('should view transcription details', async ({ page }) => {
    // Navigate to transcriptions tab
    await page.click('text=Transcriptions');
    
    // If there are transcriptions, click on one
    const transcriptionItems = page.locator('.transcription-item');
    const count = await transcriptionItems.count();
    
    if (count > 0) {
      await transcriptionItems.first().click();
      
      // Check for transcription details
      await expect(page.locator('text=/Transcript|Content|Text/i')).toBeVisible();
    }
  });

  test('should search transcriptions', async ({ page }) => {
    // Click on search tab
    await page.click('text=Search');
    
    // Enter search query
    await page.fill('input[placeholder*="Search"]', 'test query');
    
    // Press Enter or click search button
    await page.press('input[placeholder*="Search"]', 'Enter');
    
    // Wait for search results
    await page.waitForTimeout(1000);
    
    // Check for results or no results message
    const hasResults = await page.locator('.search-result').count() > 0;
    const hasNoResults = await page.locator('text=/No results|No matches/i').isVisible();
    
    expect(hasResults || hasNoResults).toBeTruthy();
  });

  test('should export transcription', async ({ page }) => {
    // Navigate to transcriptions
    await page.click('text=Transcriptions');
    
    const transcriptionItems = page.locator('.transcription-item');
    const count = await transcriptionItems.count();
    
    if (count > 0) {
      // Click on export button for first transcription
      const exportButton = page.locator('button:has-text("Export")').first();
      if (await exportButton.isVisible()) {
        await exportButton.click();
        
        // Check for export options
        await expect(page.locator('text=/PDF|JSON|TXT|SRT/i')).toBeVisible();
      }
    }
  });

  test('should delete transcription', async ({ page }) => {
    // Navigate to transcriptions
    await page.click('text=Transcriptions');
    
    const transcriptionItems = page.locator('.transcription-item');
    const initialCount = await transcriptionItems.count();
    
    if (initialCount > 0) {
      // Click delete button
      const deleteButton = page.locator('button:has-text("Delete")').first();
      if (await deleteButton.isVisible()) {
        await deleteButton.click();
        
        // Confirm deletion
        await page.click('button:has-text("Confirm")');
        
        // Wait for deletion
        await page.waitForTimeout(1000);
        
        // Check count decreased
        const newCount = await transcriptionItems.count();
        expect(newCount).toBeLessThan(initialCount);
      }
    }
  });

  test('should play audio for transcription', async ({ page }) => {
    // Navigate to transcriptions
    await page.click('text=Transcriptions');
    
    const audioPlayer = page.locator('audio, [data-testid="audio-player"]');
    if (await audioPlayer.isVisible()) {
      // Check play button exists
      await expect(page.locator('button[aria-label*="Play"]')).toBeVisible();
    }
  });
});