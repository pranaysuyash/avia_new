const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  // Capture console messages
  const logs = [];
  page.on('console', (msg) => {
    logs.push({
      type: msg.type(),
      text: msg.text()
    });
  });
  
  // Capture page errors
  page.on('pageerror', (err) => {
    logs.push({
      type: 'error',
      text: err.toString()
    });
  });
  
  try {
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });
    await page.waitForTimeout(2000);
    
    // Print all logs
    console.log('=== Console Logs ===');
    logs.forEach(log => {
      console.log(`[${log.type}] ${log.text}`);
    });
    
    // Check if app loaded
    const title = await page.title();
    console.log('\n=== Page Title ===');
    console.log(title);
    
    // Check for React error boundary
    const hasError = await page.evaluate(() => {
      return document.querySelector('.error-boundary') !== null ||
             document.body.textContent.includes('Something went wrong') ||
             document.body.textContent.includes('Error');
    });
    
    if (hasError) {
      console.log('\n=== Error detected on page ===');
      const bodyText = await page.evaluate(() => document.body.textContent);
      console.log(bodyText.substring(0, 500));
    }
    
  } catch (err) {
    console.error('Failed to load page:', err);
  }
  
  await browser.close();
})();