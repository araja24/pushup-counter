import pytest
from fastapi.testclient import TestClient

from pushform.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from pushform.analysis.events import Event
from pushform.analysis.geometry import Frame
from pushform.analysis.orchestrator import Orchestrator
from pushform.app import create_app


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def run_set():
    """Feed Frames through one Set and hand back the Orchestrator and its events.

    Tests drive the analysis exactly as the WebSocket handler will: start a Set,
    push wire-shape Frames, read the events that come back.
    """

    def _run_set(
        frames: list[Frame],
        *,
        config: AnalysisConfig = DEFAULT_CONFIG,
        set_id: str = "test-set",
    ) -> tuple[Orchestrator, list[Event]]:
        orchestrator = Orchestrator(config)
        orchestrator.start(set_id)
        events: list[Event] = []
        for frame in frames:
            events.extend(orchestrator.process(frame))
        return orchestrator, events

    return _run_set
