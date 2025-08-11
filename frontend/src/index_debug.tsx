import React from 'react';
import { createRoot } from 'react-dom/client';

console.log('Script is running');

const App = () => {
  console.log('App component rendering');
  return React.createElement('div', { 
    style: { padding: '20px', fontSize: '18px', color: 'blue' } 
  }, 'React is working! This is the Enterprise Transcription Platform');
};

console.log('Looking for root element...');
const container = document.getElementById('root');
console.log('Container found:', container);

if (container) {
  console.log('Creating root...');
  try {
    const root = createRoot(container);
    console.log('Root created, rendering...');
    root.render(React.createElement(App));
    console.log('Render called');
  } catch (error) {
    const err = error as unknown as { message?: string };
    console.error('Error during rendering:', error);
    container.innerHTML = '<div style="padding: 20px; color: red;">Error rendering React app: ' + (err.message || 'unknown') + '</div>';
  }
} else {
  console.error('Root container not found');
  document.body.innerHTML = '<div style="padding: 20px; color: red;">Root container not found</div>';
}