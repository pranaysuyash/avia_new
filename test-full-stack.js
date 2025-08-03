const { spawn } = require('child_process');
const { chromium } = require('playwright');

// Kill any existing servers
console.log('Cleaning up existing servers...');
require('child_process').execSync('lsof -ti:3000 | xargs kill -9 2>/dev/null || true', { stdio: 'ignore' });
require('child_process').execSync('lsof -ti:8000 | xargs kill -9 2>/dev/null || true', { stdio: 'ignore' });

// Start FastAPI backend
console.log('Starting FastAPI backend...');
const backendProcess = spawn('python', ['-m', 'uvicorn', 'api.main:app', '--reload', '--port', '8000'], {
  cwd: '/Users/pranay/Projects/LLM/video/ner',
  stdio: ['ignore', 'pipe', 'pipe']
});

let backendReady = false;
backendProcess.stdout.on('data', (data) => {
  const output = data.toString();
  console.log('Backend:', output.trim());
  if (output.includes('Application startup complete')) {
    backendReady = true;
  }
});

backendProcess.stderr.on('data', (data) => {
  console.error('Backend Error:', data.toString().trim());
});

// Start React frontend
console.log('Starting React frontend...');
const frontendProcess = spawn('npm', ['start'], {
  cwd: '/Users/pranay/Projects/LLM/video/ner/desktop_app/src/renderer',
  stdio: ['ignore', 'pipe', 'pipe'],
  env: { ...process.env, BROWSER: 'none' }
});

let frontendReady = false;
frontendProcess.stdout.on('data', (data) => {
  const output = data.toString();
  if (output.includes('Compiled successfully') || output.includes('webpack compiled')) {
    frontendReady = true;
  }
});

frontendProcess.stderr.on('data', (data) => {
  const output = data.toString();
  if (!output.includes('DeprecationWarning')) {
    console.error('Frontend Error:', output.trim());
  }
});

// Wait for both servers to be ready
async function waitForServers() {
  console.log('Waiting for servers to start...');
  let attempts = 0;
  while ((!backendReady || !frontendReady) && attempts < 30) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    attempts++;
  }
  
  if (!backendReady) {
    console.error('Backend failed to start');
    return false;
  }
  if (!frontendReady) {
    console.error('Frontend failed to start');
    return false;
  }
  
  console.log('Both servers are ready!');
  return true;
}

// Test with Playwright
async function testIntegration() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Test backend health
    console.log('\\nTesting backend health...');
    const healthResponse = await page.request.get('http://localhost:8000/api/health');
    console.log('Backend health:', await healthResponse.json());
    
    // Load frontend
    console.log('\\nLoading frontend...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // Check API connection status
    const apiStatus = await page.locator('text=/API Connected|API Disconnected/').textContent();
    console.log('API Status in UI:', apiStatus);
    
    // Take screenshot
    await page.screenshot({ path: 'full-stack-test.png', fullPage: true });
    console.log('Screenshot saved as full-stack-test.png');
    
    // Check for errors
    const errors = await page.locator('text=/error|Error|failed|Failed/i').count();
    console.log('Error messages found:', errors);
    
  } catch (error) {
    console.error('Test error:', error.message);
  } finally {
    await browser.close();
  }
}

// Main execution
(async () => {
  const serversReady = await waitForServers();
  
  if (serversReady) {
    // Wait a bit more for full initialization
    await new Promise(resolve => setTimeout(resolve, 3000));
    await testIntegration();
  }
  
  // Cleanup
  console.log('\\nStopping servers...');
  backendProcess.kill();
  frontendProcess.kill();
  
  // Force kill after a delay
  setTimeout(() => {
    require('child_process').execSync('lsof -ti:3000 | xargs kill -9 2>/dev/null || true', { stdio: 'ignore' });
    require('child_process').execSync('lsof -ti:8000 | xargs kill -9 2>/dev/null || true', { stdio: 'ignore' });
    process.exit(0);
  }, 2000);
})();