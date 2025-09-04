export function getQueryParam(key: string, defaultValue: string | null = null): string | null {
  try {
    const url = new URL(window.location.href);
    return url.searchParams.get(key) ?? defaultValue;
  } catch {
    return defaultValue;
  }
}

export function setQueryParam(key: string, value: string | null): void {
  try {
    const url = new URL(window.location.href);
    if (value === null || value === '') {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, value);
    }
    window.history.replaceState({}, '', url.toString());
  } catch {
    // noop
  }
}

export function useQueryParam(key: string, initial?: string): [string | null, (v: string | null) => void] {
  const React = require('react');
  const [val, setVal] = React.useState<string | null>(() => getQueryParam(key, initial ?? null));
  const set = (v: string | null) => {
    setVal(v);
    setQueryParam(key, v);
  };
  return [val, set];
}

