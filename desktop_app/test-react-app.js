const { chromium } = require('playwright');

async function testReactApp() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Listen for console messages
  page.on('console', msg => {
    console.log(`Console ${msg.type()}: ${msg.text()}`);
  });
  
  // Listen for errors
  page.on('pageerror', error => {
    console.error('Page error:', error);
  });
  
  // Listen for request failures
  page.on('requestfailed', request => {
    console.error('Request failed:', request.url(), request.failure().errorText);
  });
  
  console.log('Navigating to React app...');
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  
  // Take screenshot
  await page.screenshot({ path: 'react-app-screenshot.png' });
  console.log('Screenshot saved as react-app-screenshot.png');
  
  // Check for any visible error messages
  const errorElements = await page.$$('[class*="error"], [class*="Error"]');
  if (errorElements.length > 0) {
    console.log(`Found ${errorElements.length} error elements on the page`);
  }
  
  // Wait a bit to see any dynamic errors
  await page.waitForTimeout(3000);
  
  // Check page title
  const title = await page.title();
  console.log('Page title:', title);
  
  // Check if main app container exists
  const appContainer = await page.$('#root');
  if (appContainer) {
    console.log('React app root element found');
  } else {
    console.error('React app root element not found!');
  }
  
  await browser.close();
}

testReactApp().catch(console.error);