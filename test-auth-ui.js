const { chromium } = require('playwright');

async function testAuthUI() {
  const browser = await chromium.launch({ headless: false }); // Show browser
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    console.log('Loading app...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(3000);
    
    // Look for user menu/profile elements
    console.log('\nChecking for authentication UI elements:');
    
    // Common patterns for user menu
    const userMenuSelectors = [
      'button:has-text("John Doe")',
      'button:has-text("test@example.com")',
      '[aria-label="User menu"]',
      '[aria-label="Account"]',
      'button:has-text("Profile")',
      'button:has-text("Account")',
      'button:has-text("Sign In")',
      'button:has-text("Login")',
      'button:has-text("Log In")',
      '[class*="user-menu"]',
      '[class*="profile"]',
      '[class*="avatar"]',
      'img[alt*="Avatar"]',
      'img[alt*="Profile"]',
      'button img[src*="avatar"]'
    ];
    
    console.log('Searching for user menu elements...');
    let foundElement = null;
    
    for (const selector of userMenuSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible({ timeout: 1000 })) {
          console.log(`✅ Found: ${selector}`);
          foundElement = element;
          break;
        }
      } catch (e) {
        // Continue checking
      }
    }
    
    if (!foundElement) {
      console.log('❌ No user menu found! Looking for any clickable elements in header...');
      
      // Check header area
      const headerElements = await page.locator('header button, nav button, [class*="header"] button').all();
      console.log(`Found ${headerElements.length} buttons in header area`);
      
      // List all visible text in header
      const headerText = await page.locator('header, nav, [class*="header"]').textContent();
      console.log('Header text:', headerText);
    } else {
      console.log('\nClicking user menu...');
      await foundElement.click();
      await page.waitForTimeout(1000);
      
      // Look for logout option
      const logoutSelectors = [
        'button:has-text("Logout")',
        'button:has-text("Log Out")',
        'button:has-text("Sign Out")',
        'a:has-text("Logout")',
        '[role="menuitem"]:has-text("Logout")'
      ];
      
      for (const selector of logoutSelectors) {
        const logoutBtn = await page.locator(selector).first();
        if (await logoutBtn.isVisible({ timeout: 1000 })) {
          console.log(`✅ Found logout option: ${selector}`);
          break;
        }
      }
    }
    
    // Take screenshot
    await page.screenshot({ path: 'auth-ui-test.png', fullPage: false });
    console.log('\nScreenshot saved as auth-ui-test.png');
    
    // Check current URL
    console.log('Current URL:', page.url());
    
    // Check localStorage for auth tokens
    const hasToken = await page.evaluate(() => {
      return {
        accessToken: !!localStorage.getItem('access_token'),
        refreshToken: !!localStorage.getItem('refresh_token'),
        user: localStorage.getItem('user')
      };
    });
    console.log('\nAuth state:', hasToken);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await page.waitForTimeout(5000); // Keep browser open to see
    await browser.close();
  }
}

testAuthUI();