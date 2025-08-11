console.log('index_test.tsx: Starting React app initialization');

import React from 'react';
import { createRoot } from 'react-dom/client';
import TestApp from './TestApp';

console.log('index_test.tsx: Imports completed');

console.log('index_test.tsx: Looking for root element');
const container = document.getElementById('root');
console.log('index_test.tsx: Root element found:', container);

if (!container) {
  console.error('FATAL: Root container with id="root" not found');
  document.body.innerHTML = '<h1 style="color: red;">FATAL: Root container not found</h1>';
  throw new Error('Root container with id="root" not found');
}

try {
  console.log('index_test.tsx: Creating React root');
  const root = createRoot(container);
  
  console.log('index_test.tsx: Rendering TestApp');
  root.render(
    <React.StrictMode>
      <TestApp />
    </React.StrictMode>
  );
  console.log('index_test.tsx: React render call completed');
} catch (error) {
  console.error('FATAL: Failed to render React app:', error);
  container.innerHTML = `<h1 style="color: red;">Failed to render app: ${error}</h1>`;
  throw error;
}