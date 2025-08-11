import React from 'react';

console.log('TestApp: Component loaded');

const TestApp: React.FC = () => {
  console.log('TestApp: Rendering');
  
  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui' }}>
      <h1 style={{ color: 'green' }}>✅ React is Working!</h1>
      <p>If you see this message, React is successfully rendering.</p>
      <p>Time: {new Date().toLocaleTimeString()}</p>
      <hr />
      <h2>Debug Info:</h2>
      <pre style={{ background: '#f0f0f0', padding: '10px' }}>
        React Version: {React.version}
      </pre>
    </div>
  );
};

export default TestApp;