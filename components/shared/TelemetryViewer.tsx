import React from 'react';
import { getUxEvents, clearUxEvents, UxEvent } from './uxTelemetry';

export const TelemetryViewer: React.FC = () => {
  const [events, setEvents] = React.useState<UxEvent[]>([]);

  const refresh = React.useCallback(() => {
    setEvents(getUxEvents());
  }, []);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  const download = () => {
    const blob = new Blob([JSON.stringify(events, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ux_events.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    clearUxEvents();
    refresh();
  };

  return (
    <div className="p-4 border rounded-md">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">UX Telemetry (Local)</h3>
        <div className="space-x-2">
          <button className="px-3 py-1 border rounded" onClick={refresh}>Refresh</button>
          <button className="px-3 py-1 border rounded" onClick={download}>Download JSON</button>
          <button className="px-3 py-1 border rounded" onClick={handleClear}>Clear</button>
        </div>
      </div>
      {events.length === 0 ? (
        <p className="text-sm text-gray-500">No events recorded yet.</p>
      ) : (
        <div className="overflow-auto max-h-80 border rounded">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Event</th>
                <th className="text-left p-2">Payload</th>
              </tr>
            </thead>
            <tbody>
              {events.slice().reverse().map((e, i) => (
                <tr key={i} className="border-t">
                  <td className="p-2">{new Date(e.ts).toLocaleString()}</td>
                  <td className="p-2">{e.event}</td>
                  <td className="p-2"><pre className="whitespace-pre-wrap">{JSON.stringify(e)}</pre></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TelemetryViewer;

