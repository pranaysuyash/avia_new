import React from 'react';
import { getUxEvents, UxEvent } from '../../services/uxTelemetry';

export const DevTelemetryOverlay: React.FC = () => {
  const [events, setEvents] = React.useState<UxEvent[]>([]);
  const [expanded, setExpanded] = React.useState(false);

  const refresh = React.useCallback(() => {
    try { setEvents(getUxEvents().slice(-100).reverse()); } catch { setEvents([]); }
  }, []);

  React.useEffect(() => {
    refresh();
    const id = setInterval(refresh, 2000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <div style={{ position: 'fixed', right: 12, bottom: 12, zIndex: 9999 }}>
      <div style={{ background: '#111827', color: '#e5e7eb', padding: 8, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontSize: 12, fontWeight: 600 }}>UX Telemetry ({events.length})</div>
          <div>
            <button onClick={() => setExpanded(!expanded)} style={{ color: '#93c5fd', fontSize: 12, marginRight: 8 }}>{expanded ? 'Hide' : 'Show'}</button>
            <button onClick={refresh} style={{ color: '#a7f3d0', fontSize: 12 }}>Refresh</button>
          </div>
        </div>
        {expanded && (
          <div style={{ maxHeight: 280, overflowY: 'auto', marginTop: 8 }}>
            {events.map((ev, idx) => (
              <div key={idx} style={{ fontSize: 11, borderTop: '1px solid #374151', paddingTop: 4, marginTop: 4 }}>
                <div><strong>{new Date(ev.ts).toLocaleTimeString()}</strong> — {ev.event}</div>
                <div style={{ color: '#9ca3af' }}>{JSON.stringify(ev)}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DevTelemetryOverlay;

