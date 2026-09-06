# One Render service serves both the API and the built frontend

FastAPI mounts the Vite build as static files and also serves the WebSocket and REST API, so there is one URL, no CORS, and no cross-origin WebSocket configuration. The alternative of a static host plus a separate API host was rejected as more setup for no benefit at this scale.

## Consequences

Render's free-tier cold start applies to the whole app, mitigated by a "waking up" state in the UI.
