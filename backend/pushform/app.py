"""Builds the FastAPI application that serves both the API and the frontend."""

from fastapi import FastAPI

from pushform.api import config, health
from pushform.static_site import mount_frontend


def create_app() -> FastAPI:
    app = FastAPI(
        title="PushForm",
        description="Counts push-up reps from pose landmarks sent by a phone.",
        version="0.1.0",
    )
    app.include_router(health.router)
    app.include_router(config.router)
    mount_frontend(app)
    return app


app = create_app()
