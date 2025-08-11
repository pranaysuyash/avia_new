// Simple test to check if AuthContext exists
const https = require('http');

const postData = JSON.stringify({
  url: 'http://localhost:3000',
  code: `
    // Check if React has rendered
    const rootDiv = document.getElementById('root');
    const hasContent = rootDiv && rootDiv.innerHTML.length > 0;
    console.log('Root content length:', rootDiv ? rootDiv.innerHTML.length : 0);
    console.log('Has content:', hasContent);
    
    // Check for any errors in console
    if (window.errors) {
      console.log('Window errors:', window.errors);
    }
    
    // Check if React components are loading
    if (window.React) {
      console.log('React is available');
    } else {
      console.log('React is NOT available');
    }
  `
});

console.log('Testing if app renders content...');
console.log('Visit http://localhost:3000 in your browser to see the actual app');