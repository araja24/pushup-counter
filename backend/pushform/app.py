"""Builds the FastAPI application that serves both the API and the frontend."""

import time
from collections.abc import Callable

from fastapi import FastAPI

from pushform.api import config, health
from pushform.static_site import mount_frontend
from pushform.ws import endpoint
from pushform.ws.orphans import OrphanStore


def create_app(now: Callable[[], float] = time.monotonic) -> FastAPI:
    """Build the app.

    Args:
        now: The wall clock a Connection throttles State messages by, and the
            orphan store times its window by. Tests pass their own so they can
            wind time on without sleeping.
    """
    app = FastAPI(
        title="PushForm",
        description="Counts push-up reps from pose landmarks sent by a phone.",
        version="0.1.0",
    )
    app.state.now = now
    app.state.orphans = OrphanStore(now)
    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(endpoint.router)
    mount_frontend(app)
    return app


app = create_app()
