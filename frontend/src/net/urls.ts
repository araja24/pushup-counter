/**
 * Where the phone talks to the backend.
 *
 * One Render service serves both the page and the API (docs/adr/0007), so the
 * bases are always the page's own origin -- nothing to configure per environment.
 */

/** The parts of `window.location` the bases are derived from. */
export interface PageLocation {
  protocol: string
  host: string
}

/** Same-origin bases for REST calls and for the landmark connection. */
export interface ApiBaseUrl {
  http: string
  ws: string
}

export function apiBaseUrl(location: PageLocation): ApiBaseUrl {
  const secure = location.protocol === 'https:'
  return {
    http: `${secure ? 'https' : 'http'}://${location.host}`,
    ws: `${secure ? 'wss' : 'ws'}://${location.host}`,
  }
}
