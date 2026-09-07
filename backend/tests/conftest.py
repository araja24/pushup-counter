import pytest
from fastapi.testclient import TestClient
from ws_support import Clock

from pushform.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from pushform.analysis.events import Event, State
from pushform.analysis.geometry import Frame
from pushform.analysis.orchestrator import Orchestrator
from pushform.app import create_app


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app()) as test_client:
        yield test_client


CAMERA_INTERVAL_S = 1.0 / 30.0
"""One reading of the test clock is one Frame from a phone camera running at
the rate the app asks for. Tests about timing set their own step; the rest get
a Connection whose Frames arrive at an honest, unremarkable pace."""


@pytest.fixture
def clock() -> Clock:
    return Clock(step_s=CAMERA_INTERVAL_S)


@pytest.fixture
def socket(clock: Clock):
    """One open `/ws` Connection on a clock the test controls."""
    with TestClient(create_app(now=clock)) as test_client:
        with test_client.websocket_connect("/ws") as ws:
            yield ws


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


@pytest.fixture
def walk_set():
    """Like ``run_set``, but keeping the State after every single Frame.

    Rules about *when* something may happen -- a Tracked Side that must not
    switch mid-Rep, a Phase that must freeze while the camera cannot see the
    user -- are invisible in a final State. They only show up Frame by Frame.
    """

    def _walk_set(
        frames: list[Frame],
        *,
        config: AnalysisConfig = DEFAULT_CONFIG,
        set_id: str = "test-set",
    ) -> tuple[list[State], list[Event]]:
        orchestrator = Orchestrator(config)
        orchestrator.start(set_id)
        states: list[State] = []
        events: list[Event] = []
        for frame in frames:
            events.extend(orchestrator.process(frame))
            states.append(orchestrator.state)
        return states, events

    return _walk_set
