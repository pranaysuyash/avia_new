// React Native UX telemetry utility for the mobile app
// Uses AsyncStorage if available; falls back to in-memory buffer

export type UxEvent = {
  ts: number;
  event: string;
  [key: string]: unknown;
};

const STORAGE_KEY = 'ux_events_buffer';

let AsyncStorage: any;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  AsyncStorage = require('@react-native-async-storage/async-storage').default;
} catch (_) {
  AsyncStorage = null;
}

const mem: UxEvent[] = [];

export async function logUxEvent(event: string, payload: Record<string, unknown> = {}): Promise<void> {
  const ev: UxEvent = { ts: Date.now(), event, ...payload };
  try {
    // eslint-disable-next-line no-console
    console.debug('[UX]', ev);
    if (!AsyncStorage) {
      mem.push(ev);
      if (mem.length > 500) mem.shift();
      return;
    }
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const arr: UxEvent[] = raw ? JSON.parse(raw) : [];
    arr.push(ev);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(arr.slice(-500)));
  } catch (_) {
    // best effort only
  }
}

export async function getUxEvents(): Promise<UxEvent[]> {
  try {
    if (!AsyncStorage) return [...mem];
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (_) {
    return [];
  }
}

export async function clearUxEvents(): Promise<void> {
  try {
    if (!AsyncStorage) {
      mem.length = 0;
      return;
    }
    await AsyncStorage.removeItem(STORAGE_KEY);
  } catch (_) {}
}

