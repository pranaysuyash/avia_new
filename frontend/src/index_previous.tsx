import React from 'react';
import { createRoot } from 'react-dom/client';

// Very simple working app to test
const App = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui' }}>
      <h1>🎵 Enterprise Transcription Platform</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' }}>
        
        <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
          <h2>📁 File Upload</h2>
          <p>Upload audio/video files for transcription</p>
          <input type="file" accept="audio/*,video/*" />
          <button style={{ marginTop: '10px', padding: '8px 16px' }}>Upload & Transcribe</button>
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
          <h2>🎯 AI Assistant</h2>
          <p>Get AI-powered insights from your content</p>
          <textarea placeholder="Ask AI about your transcripts..." style={{ width: '100%', height: '60px' }}></textarea>
          <button style={{ marginTop: '10px', padding: '8px 16px' }}>Ask AI</button>
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
          <h2>🔍 Smart Search</h2>
          <p>Search across all transcriptions</p>
          <input type="text" placeholder="Search transcripts..." style={{ width: '100%' }} />
          <button style={{ marginTop: '10px', padding: '8px 16px' }}>Search</button>
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
          <h2>🌍 Multi-Language</h2>
          <p>Support for 15+ languages including RTL</p>
          <select style={{ width: '100%', padding: '8px' }}>
            <option>English</option>
            <option>Spanish</option>
            <option>Arabic</option>
            <option>Chinese</option>
          </select>
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
          <h2>📊 Analytics</h2>
          <p>Usage metrics and insights</p>
          <div style={{ height: '40px', backgroundColor: '#f0f0f0', borderRadius: '4px', margin: '10px 0' }}></div>
          <button style={{ padding: '8px 16px' }}>View Details</button>
        </div>

        <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
          <h2>⚙️ Admin Panel</h2>
          <p>System management and monitoring</p>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <span style={{ padding: '4px 8px', backgroundColor: '#e8f5e8', borderRadius: '12px', fontSize: '12px' }}>✅ System Healthy</span>
            <span style={{ padding: '4px 8px', backgroundColor: '#e8f5e8', borderRadius: '12px', fontSize: '12px' }}>📈 245 Active Users</span>
          </div>
        </div>

      </div>

      <div style={{ marginTop: '30px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h3>🚀 Enterprise Features:</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginTop: '15px' }}>
          <div>✅ Real-time Collaboration</div>
          <div>✅ GDPR Compliance</div>
          <div>✅ Advanced Audio Player</div>
          <div>✅ GraphQL API</div>
          <div>✅ Performance Monitoring</div>
          <div>✅ Distributed Processing</div>
          <div>✅ Content Management</div>
          <div>✅ User Analytics</div>
        </div>
      </div>
    </div>
  );
};

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<App />);
} else {
  console.error('Root container not found');
}