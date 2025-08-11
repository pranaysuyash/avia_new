import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('File Upload Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Mock login if needed
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

  test('should display file upload area', async ({ page }) => {
    await expect(page.locator('text=/Upload.*file|Drop.*file|Choose.*file/i')).toBeVisible();
  });

  test('should upload audio file successfully', async ({ page }) => {
    // Create a test file path (you'd need to have a test file)
    const filePath = path.join(__dirname, 'fixtures', 'test-audio.mp3');
    
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Check for upload progress or success message
    await expect(page.locator('text=/Upload.*success|Processing|Transcribing/i')).toBeVisible({
      timeout: 10000
    });
  });

  test('should reject invalid file types', async ({ page }) => {
    // Try to upload a non-audio/video file
    const filePath = path.join(__dirname, 'fixtures', 'test.txt');
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Check for error message
    await expect(page.locator('text=/Invalid.*file.*type|Only.*audio.*video/i')).toBeVisible();
  });

  test('should handle drag and drop upload', async ({ page }) => {
    // Create a DataTransfer with files
    await page.evaluate(() => {
      const dropZone = document.querySelector('[data-testid="file-drop-zone"]') || 
                      document.querySelector('.file-upload-area') ||
                      document.body;
      
      const event = new DragEvent('drop', {
        dataTransfer: new DataTransfer(),
        bubbles: true,
        cancelable: true,
      });
      
      // Simulate file drop
      dropZone?.dispatchEvent(event);
    });
    
    // Check for some response
    await page.waitForTimeout(1000);
  });

  test('should show file size limit error for large files', async ({ page }) => {
    // Mock a large file upload attempt
    await page.evaluate(() => {
      const largeFile = new File(['x'.repeat(500 * 1024 * 1024)], 'large.mp3', {
        type: 'audio/mp3'
      });
      
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(largeFile);
        fileInput.files = dataTransfer.files;
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    
    // Check for size limit error
    await expect(page.locator('text=/File.*too.*large|Maximum.*size/i')).toBeVisible();
  });
});