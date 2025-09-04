// React Native UX telemetry utility: buffers events in AsyncStorage and logs to console.
// Mirrors the web API in components/shared/uxTelemetry.ts

import type { } from 'react-native';

export type UxEvent = {
  ts: number;
  event: string;
  [key: string]: unknown;
};

const STORAGE_KEY = 'ux_events_buffer';

let AsyncStorage: any;
try {
  // Lazy require to avoid bundler issues when not on RN
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  AsyncStorage = require('@react-native-async-storage/async-storage').default;
} catch (_) {
  AsyncStorage = null;
}

// In-memory fallback if AsyncStorage is not available
const memBuffer: UxEvent[] = [];

export async function logUxEvent(event: string, payload: Record<string, unknown> = {}): Promise<void> {
  try {
    const ts = Date.now();
    const ev: UxEvent = { ts, event, ...payload };
    // eslint-disable-next-line no-console
    console.debug('[UX]', ev);

    if (!AsyncStorage) {
      memBuffer.push(ev);
      if (memBuffer.length > 500) memBuffer.shift();
      return;
    }

    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const arr: UxEvent[] = raw ? JSON.parse(raw) : [];
    arr.push(ev);
    const bounded = arr.slice(-500);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(bounded));
  } catch (_) {
    // best effort only
  }
}

export async function getUxEvents(): Promise<UxEvent[]> {
  try {
    if (!AsyncStorage) return [...memBuffer];
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (_) {
    return [];
  }
}

export async function clearUxEvents(): Promise<void> {
  try {
    if (!AsyncStorage) {
      memBuffer.length = 0;
      return;
    }
    await AsyncStorage.removeItem(STORAGE_KEY);
  } catch (_) {
    // noop
  }
}

