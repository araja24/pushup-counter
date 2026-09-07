"""Client-visible tuning constants, served so the phone never hard-codes them.

The values themselves live in :mod:`pushform.analysis.config`, the single home
of every threshold. This router only publishes them; it never defines one.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from pushform.analysis.config import DEFAULT_CONFIG

router = APIRouter(tags=["config"])


class Config(BaseModel):
    """Elbow-angle thresholds that drive phase changes, with hysteresis between them."""

    down_threshold: float = Field(description="Elbow angle in degrees for entering DOWN.")
    up_threshold: float = Field(description="Elbow angle in degrees for entering UP.")


@router.get("/api/config", summary="Default elbow-angle phase thresholds")
def read_config() -> Config:
    return Config(
        down_threshold=DEFAULT_CONFIG.down_threshold_deg,
        up_threshold=DEFAULT_CONFIG.up_threshold_deg,
    )
