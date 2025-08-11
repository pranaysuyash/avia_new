const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  const logs = [];
  
  // Capture console messages
  page.on('console', msg => {
    logs.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    logs.push({
      type: 'pageerror',
      text: error.message,
      stack: error.stack
    });
  });
  
  // Capture request failures
  page.on('requestfailed', request => {
    logs.push({
      type: 'requestfailed',
      url: request.url(),
      failure: request.failure()
    });
  });
  
  try {
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle2', timeout: 10000 });
    
    // Wait a bit for any async errors
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Check if React mounted
    const rootContent = await page.evaluate(() => {
      const root = document.getElementById('root');
      return root ? root.innerHTML : 'ROOT NOT FOUND';
    });
    
    console.log('=== CONSOLE LOGS ===');
    logs.forEach(log => {
      if (log.type === 'error' || log.type === 'pageerror') {
        console.log(`[ERROR] ${log.text}`);
        if (log.stack) console.log(log.stack);
      } else {
        console.log(`[${log.type.toUpperCase()}] ${log.text}`);
      }
    });
    
    console.log('\n=== ROOT CONTENT ===');
    console.log(rootContent.substring(0, 200) || 'EMPTY');
    
  } catch (error) {
    console.error('Failed to load page:', error);
  }
  
  await browser.close();
})();