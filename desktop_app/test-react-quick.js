const { chromium } = require('playwright');

async function testReactApp() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const errors = [];
  
  // Collect console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(`Console error: ${msg.text()}`);
    }
  });
  
  // Collect page errors
  page.on('pageerror', error => {
    errors.push(`Page error: ${error.message}`);
  });
  
  try {
    console.log('Loading React app...');
    await page.goto('http://localhost:3000', { 
      waitUntil: 'domcontentloaded',
      timeout: 10000 
    });
    
    // Get page content
    const content = await page.content();
    
    // Check if React rendered
    const hasReactRoot = content.includes('id="root"');
    const hasReactApp = content.includes('data-reactroot') || content.includes('App');
    
    console.log('React root found:', hasReactRoot);
    console.log('React app rendered:', hasReactApp);
    
    // Check for error boundaries or error messages
    const errorText = await page.locator('text=/error|Error|failed|Failed/i').count();
    console.log('Error messages found:', errorText);
    
    // Take screenshot
    await page.screenshot({ path: 'react-app-state.png' });
    console.log('Screenshot saved');
    
    // Print any collected errors
    if (errors.length > 0) {
      console.log('\nErrors found:');
      errors.forEach(err => console.log(err));
    } else {
      console.log('\nNo JavaScript errors detected');
    }
    
  } catch (error) {
    console.error('Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testReactApp().catch(console.error);