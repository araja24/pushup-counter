"""Serves the frontend from the same origin as the API (see docs/adr/0007).

When `frontend/dist` exists it is served as a single-page app: unknown paths fall
back to index.html so client-side routes survive a refresh. When it does not
exist -- a fresh clone, or a test run with no build -- a placeholder page stands in
so the backend is still usable on its own.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

PLACEHOLDER_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PushForm</title>
  </head>
  <body>
    <h1>PushForm</h1>
    <p>The frontend has not been built yet. Run <code>npm run build</code> in
      <code>frontend/</code>, then restart the backend.</p>
  </body>
</html>
"""


class SinglePageApp(StaticFiles):
    """Static files that answer any unknown path with index.html.

    Unknown API paths are exempt: a typo there should fail loudly rather than
    quietly return the page with a 200.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as missing:
            if missing.status_code != 404 or scope["path"].startswith("/api/"):
                raise
            return await super().get_response("index.html", scope)


def mount_frontend(app: FastAPI, dist: Path = FRONTEND_DIST) -> None:
    """Attach the built frontend at `/`, or a placeholder when there is no build."""
    if dist.is_dir():
        app.mount("/", SinglePageApp(directory=dist, html=True), name="frontend")
        return

    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    def read_placeholder() -> str:
        return PLACEHOLDER_PAGE
