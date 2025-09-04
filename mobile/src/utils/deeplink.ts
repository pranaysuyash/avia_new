export type DeeplinkParams = Record<string, string | number | boolean | undefined | null>;

export function buildLink(screen: string, params: DeeplinkParams = {}, base: string = 'nerapp://'): string {
  const url = new URL(base + screen);
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    url.searchParams.set(k, String(v));
  });
  return url.toString();
}

