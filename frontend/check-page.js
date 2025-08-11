const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });
  
  // Get page structure
  const structure = await page.evaluate(() => {
    const getTextContent = (selector) => {
      const el = document.querySelector(selector);
      return el ? el.textContent.trim() : null;
    };
    
    return {
      title: document.title,
      hasHeader: !!document.querySelector('header'),
      hasTabs: !!document.querySelector('[role="tablist"]'),
      hasUploadSection: !!document.querySelector('[id*="upload"]'),
      headerText: getTextContent('header h1'),
      activeTab: getTextContent('[role="tab"][aria-selected="true"]'),
      bodyText: document.body.textContent.substring(0, 500)
    };
  });
  
  console.log('=== PAGE STRUCTURE ===');
  console.log('Title:', structure.title);
  console.log('Has Header:', structure.hasHeader);
  console.log('Has Tabs:', structure.hasTabs);
  console.log('Has Upload Section:', structure.hasUploadSection);
  console.log('Header Text:', structure.headerText);
  console.log('Active Tab:', structure.activeTab);
  console.log('\nFirst 500 chars of content:');
  console.log(structure.bodyText);
  
  // Take a screenshot
  await page.screenshot({ path: 'frontend-screenshot.png', fullPage: true });
  console.log('\nScreenshot saved as frontend-screenshot.png');
  
  await browser.close();
})();