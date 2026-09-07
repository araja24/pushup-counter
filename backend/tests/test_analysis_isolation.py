"""The analysis core must stay importable without a web stack (ADR-0002).

The dependency runs one way: the API imports analysis so the same code serves
the live WebSocket, the tests and the replay CLI. If that ever inverts, the
segmentation script and the CLI start dragging FastAPI in behind them.
"""

import subprocess
import sys

FORBIDDEN = ("fastapi", "starlette", "pushform.app", "pushform.api")

PROBE = """
import sys
import pushform.analysis
import pushform.analysis.orchestrator
import pushform.analysis.replay
import pushform.analysis.synthetic
print(",".join(name for name in {forbidden!r} if name in sys.modules))
"""


def test_importing_the_analysis_package_pulls_in_no_web_stack():
    result = subprocess.run(
        [sys.executable, "-c", PROBE.format(forbidden=FORBIDDEN)],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == ""


def test_the_api_is_the_side_allowed_to_import_the_analysis_config():
    from pushform.analysis.config import DEFAULT_CONFIG
    from pushform.api import config

    assert config.DEFAULT_CONFIG is DEFAULT_CONFIG
