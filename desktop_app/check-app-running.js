const { chromium } = require('playwright');

async function waitForAppAndTest() {
  console.log('Waiting for React app to be ready...');
  
  // Wait a bit for the server to start
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Try multiple times with retries
    let success = false;
    for (let i = 0; i < 3; i++) {
      try {
        await page.goto('http://localhost:3000', { 
          waitUntil: 'domcontentloaded',
          timeout: 10000 
        });
        success = true;
        break;
      } catch (error) {
        console.log(`Attempt ${i + 1} failed, retrying...`);
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    }
    
    if (!success) {
      throw new Error('Could not connect to React app after 3 attempts');
    }
    
    console.log('React app loaded successfully!');
    
    // Check for compilation errors
    const compilationError = await page.locator('text=/Compiled with problems/').count();
    if (compilationError > 0) {
      console.log('⚠️  App has compilation errors');
      const errorText = await page.locator('pre').first().textContent();
      console.log('First error:', errorText?.split('\\n')[0]);
    } else {
      console.log('✅ No compilation errors visible');
    }
    
    // Check if app actually rendered
    const appContent = await page.locator('.App, #root > div').count();
    console.log('App components found:', appContent);
    
    // Take screenshot
    await page.screenshot({ path: 'app-status.png', fullPage: true });
    console.log('Screenshot saved as app-status.png');
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await browser.close();
  }
}

// First start the server in background
const { spawn } = require('child_process');
const serverProcess = spawn('npm', ['start'], {
  cwd: '/Users/pranay/Projects/LLM/video/ner/desktop_app/src/renderer',
  detached: true,
  stdio: 'ignore'
});

serverProcess.unref();

// Then test
waitForAppAndTest()
  .then(() => {
    console.log('\\nTo stop the React server, run: lsof -ti:3000 | xargs kill -9');
    process.exit(0);
  })
  .catch(console.error);