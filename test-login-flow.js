const { chromium } = require('playwright');

async function testLoginFlow() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    console.log('Loading app...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    // Click Sign In button
    console.log('\nClicking Sign In button...');
    await page.click('button:has-text("Sign In")');
    await page.waitForTimeout(1000);
    
    // Should be on login page
    console.log('Current URL:', page.url());
    
    // Fill in login form
    console.log('\nFilling login form...');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password');
    
    // Take screenshot of login form
    await page.screenshot({ path: 'login-form.png' });
    
    // Submit form
    console.log('Submitting login form...');
    await page.click('button[type="submit"]');
    
    // Wait for navigation or error
    await page.waitForTimeout(3000);
    
    console.log('\nAfter login attempt:');
    console.log('Current URL:', page.url());
    
    // Check for error messages
    const errorElement = await page.locator('.bg-red-50, .bg-red-900\\/20').first();
    if (await errorElement.isVisible({ timeout: 1000 })) {
      const errorText = await errorElement.textContent();
      console.log('Error message:', errorText);
    }
    
    // Check if we're logged in
    const authState = await page.evaluate(() => {
      return {
        accessToken: !!localStorage.getItem('access_token'),
        refreshToken: !!localStorage.getItem('refresh_token'),
        user: localStorage.getItem('user')
      };
    });
    console.log('Auth state:', authState);
    
    // Look for user menu
    console.log('\nLooking for user menu after login...');
    const userMenuSelectors = [
      'button:has-text("test@example.com")',
      'button:has-text("John Doe")',
      'button:has-text("User")',
      '[class*="user-menu"]',
      'button img[class*="UserCircle"]'
    ];
    
    let foundUserMenu = false;
    for (const selector of userMenuSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible({ timeout: 1000 })) {
          console.log(`✅ Found user menu: ${selector}`);
          foundUserMenu = true;
          
          // Click to open dropdown
          await element.click();
          await page.waitForTimeout(1000);
          
          // Look for logout button
          const logoutBtn = await page.locator('button:has-text("Logout")').first();
          if (await logoutBtn.isVisible({ timeout: 1000 })) {
            console.log('✅ Found Logout button in dropdown');
          }
          
          break;
        }
      } catch (e) {
        // Continue
      }
    }
    
    if (!foundUserMenu) {
      console.log('❌ User menu not found after login');
    }
    
    // Take final screenshot
    await page.screenshot({ path: 'after-login.png', fullPage: false });
    console.log('\nScreenshots saved: login-form.png, after-login.png');
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await page.waitForTimeout(5000); // Keep browser open
    await browser.close();
  }
}

testLoginFlow();