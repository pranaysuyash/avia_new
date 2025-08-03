const { chromium } = require('playwright');

async function testTranscriptionsAccess() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    console.log('Loading app and logging in...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    // Check if already logged in
    const authState = await page.evaluate(() => {
      return !!localStorage.getItem('access_token');
    });
    
    if (!authState) {
      // Login first
      await page.click('button:has-text("Sign In")');
      await page.waitForTimeout(1000);
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'password');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
    }
    
    console.log('\nNavigating to History page...');
    // Look for History link in sidebar
    await page.click('a:has-text("History"), button:has-text("History")');
    await page.waitForTimeout(2000);
    
    console.log('Current URL:', page.url());
    
    // Look for transcription data
    console.log('\nLooking for transcriptions...');
    
    // Check for loading state
    try {
      const loadingElement = await page.locator('.animate-spin').first();
      if (await loadingElement.isVisible({ timeout: 1000 })) {
        console.log('Loading indicator found, waiting...');
        await page.waitForTimeout(3000);
      }
    } catch (e) {
      // No loading indicator
    }
    
    // Check for transcriptions
    const transcriptionSelectors = [
      'text=/Meeting Recording/i',
      'text=/Interview with Client/i',
      'text=/Team Standup/i',
      '[class*="transcription"]',
      'text=/minutes/i',
      'text=/completed/i',
      'text=/processing/i',
      'table tbody tr',
      '[class*="hover:bg-gray-50"]'
    ];
    
    let foundTranscriptions = false;
    for (const selector of transcriptionSelectors) {
      const elements = await page.locator(selector).all();
      if (elements.length > 0) {
        console.log(`✅ Found ${elements.length} items matching: ${selector}`);
        foundTranscriptions = true;
        
        // Get text content of all items
        for (let i = 0; i < elements.length; i++) {
          const text = await elements[i].textContent();
          console.log(`  Item ${i + 1}: ${text.substring(0, 150)}...`);
        }
        
        // Also look for specific item details
        const itemDetails = await page.locator('[class*="hover:bg-gray"]').all();
        console.log(`\n✅ Found ${itemDetails.length} transcription items in the list`);
        break;
      }
    }
    
    if (!foundTranscriptions) {
      console.log('❌ No transcriptions found');
      
      // Check for empty state message
      const emptyMessages = await page.locator('text=/no transcription/i, text=/empty/i, text=/no data/i').all();
      if (emptyMessages.length > 0) {
        console.log('Empty state message found:', await emptyMessages[0].textContent());
      }
    }
    
    // Check API calls in network tab
    console.log('\nChecking API calls...');
    page.on('response', response => {
      if (response.url().includes('/api/') && response.url().includes('transcript')) {
        console.log(`API call: ${response.url()} - Status: ${response.status()}`);
      }
    });
    
    // Reload to capture API calls
    await page.reload();
    await page.waitForTimeout(3000);
    
    // Take screenshot
    await page.screenshot({ path: 'history-page.png', fullPage: true });
    console.log('\nScreenshot saved as history-page.png');
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await page.waitForTimeout(5000);
    await browser.close();
  }
}

testTranscriptionsAccess();