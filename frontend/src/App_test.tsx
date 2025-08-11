import React from 'react';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Transcription Platform</h1>
        <p>App is working correctly!</p>
        <div style={{ marginTop: '20px' }}>
          <h2>Features Available:</h2>
          <ul style={{ textAlign: 'left' }}>
            <li>Audio/Video Transcription</li>
            <li>Real-time Processing</li>
            <li>Multi-language Support</li>
            <li>Advanced Analytics</li>
            <li>Enterprise Features</li>
          </ul>
        </div>
      </header>
    </div>
  );
};

export default App;