"""Liveness endpoint: how long this process has been up and which model it loaded."""

import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["health"])

_STARTED_AT = time.monotonic()

NO_MODEL = "none"
"""Reported as the model version until a trained classifier ships."""


class Health(BaseModel):
    """Liveness of the backend process."""

    status: str = Field(description='Always "ok" when the process can answer.')
    uptime_s: float = Field(description="Seconds since this process started serving.")
    model_version: str = Field(
        description=f'Version of the loaded classifier, or "{NO_MODEL}" when none is loaded.'
    )


@router.get("/api/health", summary="Liveness, uptime and loaded model version")
def read_health() -> Health:
    return Health(
        status="ok",
        uptime_s=time.monotonic() - _STARTED_AT,
        model_version=NO_MODEL,
    )
