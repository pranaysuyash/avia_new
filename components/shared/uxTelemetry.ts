// Minimal UX telemetry utility: buffers events in localStorage and logs to console.

export type UxEvent = {
  ts: number;
  event: string;
  [key: string]: unknown;
};

const STORAGE_KEY = 'ux_events_buffer';

export function logUxEvent(event: string, payload: Record<string, unknown> = {}): void {
  try {
    const ts = Date.now();
    const ev: UxEvent = { ts, event, ...payload };
    // Console log for dev visibility
    // eslint-disable-next-line no-console
    console.debug('[UX]', ev);
    // If running in Electron, forward to main process for durable logging
    try {
      // @ts-ignore
      if (typeof window !== 'undefined' && window.electronAPI && typeof window.electronAPI.logUxEvent === 'function') {
        // @ts-ignore
        window.electronAPI.logUxEvent(ev);
      }
    } catch {}
    if (typeof window === 'undefined') return;
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const arr: UxEvent[] = raw ? JSON.parse(raw) : [];
    arr.push(ev);
    // Keep buffer bounded
    const bounded = arr.slice(-500);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(bounded));
  } catch (_) {
    // best effort only
  }
}

export function getUxEvents(): UxEvent[] {
  try {
    if (typeof window === 'undefined') return [];
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (_) {
    return [];
  }
}

export function clearUxEvents(): void {
  try {
    if (typeof window === 'undefined') return;
    window.localStorage.removeItem(STORAGE_KEY);
  } catch (_) {
    // noop
  }
}
