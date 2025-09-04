import React from 'react';
import TelemetryViewer from '../shared/TelemetryViewer';

const TelemetryPanel: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-semibold mb-4">Developer Telemetry Panel</h2>
      <p className="text-sm text-gray-600 mb-4">
        Local UX events recorded via <code>logUxEvent</code>. Use this panel to inspect, download, or clear events.
      </p>
      <TelemetryViewer />
    </div>
  );
};

export default TelemetryPanel;

