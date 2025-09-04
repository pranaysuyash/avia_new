export type UxEvent = {
  ts: number;
  event: string;
  [key: string]: unknown;
};

const STORAGE_KEY = 'ux_events_buffer_renderer';

export function logUxEvent(event: string, payload: Record<string, unknown> = {}): void {
  try {
    const ts = Date.now();
    const ev: UxEvent = { ts, event, ...payload };
    // Forward to Electron main for durable logging when available
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
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(arr.slice(-500)));
  } catch (_) {
    // best effort only
  }
}

export function getUxEvents(): UxEvent[] {
  try {
    if (typeof window === 'undefined') return [];
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function clearUxEvents(): void {
  try {
    if (typeof window === 'undefined') return;
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {}
}

