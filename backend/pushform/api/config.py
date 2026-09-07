"""Client-visible tuning constants, served so the phone never hard-codes them.

These are the only definitions of the phase thresholds for now; ticket #4 moves
them into the analysis config module.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["config"])

DOWN_THRESHOLD = 95
"""Elbow angle in degrees below which the phase becomes DOWN."""

UP_THRESHOLD = 155
"""Elbow angle in degrees above which the phase becomes UP."""


class Config(BaseModel):
    """Elbow-angle thresholds that drive phase changes, with hysteresis between them."""

    down_threshold: int = Field(description="Elbow angle in degrees for entering DOWN.")
    up_threshold: int = Field(description="Elbow angle in degrees for entering UP.")


@router.get("/api/config", summary="Default elbow-angle phase thresholds")
def read_config() -> Config:
    return Config(down_threshold=DOWN_THRESHOLD, up_threshold=UP_THRESHOLD)
