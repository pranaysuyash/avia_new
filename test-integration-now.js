const { chromium } = require('playwright');

async function testIntegration() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Test backend health
    console.log('Testing backend health...');
    const healthResponse = await page.request.get('http://localhost:8000/api/health');
    const healthData = await healthResponse.json();
    console.log('Backend health:', healthData);
    console.log('Backend status:', healthResponse.status());
    
    // Load frontend
    console.log('\nLoading frontend...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // Wait for React to render
    await page.waitForTimeout(2000);
    
    // Check API connection status
    const apiStatusElement = await page.locator('text=/API Connected|API Disconnected/').first();
    const apiStatus = await apiStatusElement.textContent();
    console.log('API Status in UI:', apiStatus);
    
    // Check if dashboard loaded
    const dashboardTitle = await page.locator('h1:has-text("Dashboard")').count();
    console.log('Dashboard title found:', dashboardTitle > 0);
    
    // Check for loading indicators
    const loadingElements = await page.locator('.animate-pulse').count();
    console.log('Loading elements:', loadingElements);
    
    // Take screenshot
    await page.screenshot({ path: 'integration-test.png', fullPage: true });
    console.log('\nScreenshot saved as integration-test.png');
    
    // Check network activity
    const networkRequests = [];
    page.on('request', request => {
      if (request.url().includes('localhost:8000')) {
        networkRequests.push({
          url: request.url(),
          method: request.method()
        });
      }
    });
    
    // Wait to capture network activity
    await page.waitForTimeout(1000);
    
    console.log('\nAPI requests made:', networkRequests.length);
    networkRequests.forEach(req => {
      console.log(`  ${req.method} ${req.url}`);
    });
    
  } catch (error) {
    console.error('Test error:', error.message);
  } finally {
    await browser.close();
  }
}

testIntegration()
  .then(() => {
    console.log('\nTest completed!');
    process.exit(0);
  })
  .catch(console.error);