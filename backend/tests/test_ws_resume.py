"""Resume: a dropped Connection does not cost the user their Set.

Every test here opens two Connections against one app, exactly as a phone that
loses Wi-Fi mid-Set does, and winds the clock by hand between them.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from pushform.analysis import synthetic
from pushform.analysis.geometry import Frame
from pushform.app import create_app


class Clock:
    """A wall clock the test winds on by hand, so the window is tested without sleeping."""

    def __init__(self) -> None:
        self.seconds = 0.0

    def __call__(self) -> float:
        return self.seconds


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def client(clock: Clock) -> Iterator[TestClient]:
    with TestClient(create_app(now=clock)) as test_client:
        yield test_client


def after_gap(frames: list[Frame], gap_ms: int = 20_000) -> list[Frame]:
    """The same Frames, stamped as if they arrived after a break in the wire."""
    return [{**frame, "t": frame["t"] + gap_ms} for frame in frames]


def read_until(ws, kind: str) -> list[dict]:
    """Read back messages up to the first of that kind.

    An unexpected refusal ends the read rather than leaving the test waiting for
    a message the backend is never going to send.
    """
    messages = []
    while True:
        message = ws.receive_json()
        messages.append(message)
        if message["type"] == kind:
            return messages
        if message["type"] == "error":
            raise AssertionError(f"the backend refused: {message}")


def drain(ws, frames: list[Frame]) -> list[dict]:
    """Stream Frames, stop the Set, and read everything back up to the Summary."""
    for frame in frames:
        ws.send_json(frame)
    ws.send_json({"cmd": "stop"})
    return read_until(ws, "summary")


def kinds(messages: list[dict], kind: str) -> list[dict]:
    return [message for message in messages if message["type"] == kind]


def count_three(client: TestClient, set_id: str = "set-1") -> None:
    """Open a Connection, count three Reps, and drop it mid-Set."""
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "start", "set_id": set_id})
        for frame in synthetic.generate_frames(cycles=3):
            ws.send_json(frame)
        reps = []
        while len(reps) < 3:
            reps = kinds(read_until(ws, "rep"), "rep") + reps


def test_a_set_resumed_inside_the_window_counts_on_from_where_it_dropped(clock, client):
    count_three(client)

    clock.seconds = 4.0
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "resume", "set_id": "set-1"})
        adopted = ws.receive_json()
        messages = drain(ws, after_gap(synthetic.generate_frames(cycles=2)))

    assert adopted["type"] == "state"
    assert adopted["reps"] == 3, "the count survived the drop"
    assert [rep["index"] for rep in kinds(messages, "rep")] == [4, 5]
    assert kinds(messages, "summary")[0]["reps"] == 5


def test_a_set_resumed_after_the_window_says_it_expired_and_counts_from_zero(clock, client):
    count_three(client)

    clock.seconds = 10.5
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "resume", "set_id": "set-1"})
        refusal = ws.receive_json()
        fresh = ws.receive_json()
        messages = drain(ws, after_gap(synthetic.generate_frames(cycles=2)))

    assert refusal["type"] == "error"
    assert refusal["code"] == "set_expired"
    assert refusal["message"]
    assert fresh["reps"] == 0, "a fresh Set under the same id"
    assert kinds(messages, "summary")[0]["reps"] == 2


def test_resuming_a_set_nobody_has_heard_of_says_so_and_leaves_the_socket_open(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "resume", "set_id": "set-nobody-parked"})
        refusal = ws.receive_json()
        fresh = ws.receive_json()
        messages = drain(ws, synthetic.generate_frames(cycles=1))

    assert refusal["type"] == "error"
    assert refusal["code"] == "unknown_set"
    assert fresh["type"] == "state"
    assert kinds(messages, "summary")[0]["reps"] == 1, "counting from zero, connection alive"


def test_resume_without_a_set_id_is_refused_like_any_malformed_command(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "resume"})
        refusal = ws.receive_json()

    assert refusal["code"] == "malformed"


def test_a_set_that_was_stopped_is_not_left_parked_for_anyone_to_resume(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "start", "set_id": "set-1"})
        drain(ws, synthetic.generate_frames(cycles=1))

    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "resume", "set_id": "set-1"})
        refusal = ws.receive_json()

    assert refusal["code"] == "unknown_set"


def test_the_rep_in_flight_when_the_wire_broke_is_treated_as_tracking_lost(clock, client):
    """The user was on the way down when the socket dropped: that Rep is lost,
    and counting picks up from the next full cycle."""
    descent = synthetic.frames_from_angles([170.0] * 10 + [60.0] * 15)
    ascent = after_gap(synthetic.frames_from_angles([60.0] * 5 + [170.0] * 20))

    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "start", "set_id": "set-1"})
        for frame in descent:
            ws.send_json(frame)
        read_until(ws, "state")

    clock.seconds = 2.0
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"cmd": "resume", "set_id": "set-1"})
        interrupted = drain(ws, ascent)

    assert kinds(interrupted, "rep") == [], "the interrupted Rep is not counted"
    assert kinds(interrupted, "summary")[0]["reps"] == 0
