"""What a Connection refuses: too many Frames, too big a message, the wrong site.

None of these are about push-ups. They are the rules that keep one phone --
or one script pretending to be one -- from costing the backend more than a
phone's worth of work.
"""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from pushform.analysis import synthetic
from pushform.app import create_app
from pushform.ws.connection import Connection
from pushform.ws.policy import MAX_MESSAGE_BYTES, POLICY_VIOLATION
from pushform.ws.rate_limit import MAX_FRAMES_PER_SECOND, FrameRateLimiter
from ws_support import Clock, drain, kinds


def test_the_limiter_takes_forty_frames_in_one_second_and_no_more():
    limiter = FrameRateLimiter()
    hundred_a_second = [index / 100.0 for index in range(MAX_FRAMES_PER_SECOND + 20)]

    admitted = [at for at in hundred_a_second if limiter.allow(at)]

    assert len(admitted) == MAX_FRAMES_PER_SECOND


def test_the_limiter_opens_up_again_as_the_window_slides():
    """A sliding window, not a bucket emptied on the second: a Frame stops
    counting exactly one second after it arrived."""
    limiter = FrameRateLimiter()
    for index in range(MAX_FRAMES_PER_SECOND):
        assert limiter.allow(index / 100.0) is True

    assert limiter.allow(0.5) is False, "still inside the first second's forty"
    assert limiter.allow(1.5) is True, "all forty have aged out"


def test_sixty_frames_a_second_reach_the_analysis_at_forty_a_second():
    """The Connection looks at about forty Frames a second and silently ignores
    the rest -- no error message, because nothing is wrong."""
    clock = Clock(step_s=1.0 / 60.0)
    connection = Connection(now=clock, state_interval_s=0.0)
    two_seconds = synthetic.frames_from_angles([170.0] * 120, fps=60)

    replies = [connection.handle(frame) for frame in two_seconds]

    processed = [reply for reply in replies if reply]
    assert 70 <= len(processed) <= 82, f"{len(processed)} of 120 Frames over two seconds"
    assert kinds([message for reply in replies for message in reply], "error") == []


def test_frames_arriving_twice_as_fast_as_the_limit_still_count_their_reps(clock, socket):
    """Dropping is silent and harmless: the Set performed is the Set counted."""
    clock.step_s = 1.0 / 60.0
    frames = synthetic.generate_frames(cycles=2, cycle_ms=3000, fps=60)

    socket.send_json({"cmd": "start", "set_id": "set-1"})
    messages = drain(socket, frames)

    assert kinds(messages, "error") == []
    assert kinds(messages, "summary")[0]["reps"] == 2


def test_a_message_over_eight_kilobytes_closes_the_socket(socket):
    """A Frame of 33 Landmarks is well under a kilobyte. Anything this size is
    not a phone doing its job, and the Connection is not staying open for it."""
    socket.send_text("x" * (MAX_MESSAGE_BYTES + 1))

    with pytest.raises(WebSocketDisconnect) as closed:
        socket.receive_json()

    assert closed.value.code == POLICY_VIOLATION


def test_a_large_but_legal_message_is_still_answered(socket):
    """The limit must not be so tight that an ordinary message trips it."""
    socket.send_json({"cmd": "start", "set_id": "s" * 4000})

    assert socket.receive_json()["type"] == "state"


def test_a_socket_from_another_site_is_refused_at_the_upgrade(clock):
    """A browser tells us where the page came from. If it is not us, the
    handshake never completes and no Connection is built."""
    with TestClient(create_app(now=clock)) as client:
        with pytest.raises(WebSocketDisconnect) as refused:
            with client.websocket_connect("/ws", headers={"origin": "http://evil.example"}):
                pass  # pragma: no cover - the upgrade is refused before this runs

    assert refused.value.code == POLICY_VIOLATION


def test_a_socket_from_the_serving_host_is_accepted(clock):
    with TestClient(create_app(now=clock)) as client:
        with client.websocket_connect("/ws", headers={"origin": "http://testserver"}) as ws:
            ws.send_json(synthetic.generate_frames(cycles=1)[0])

            assert ws.receive_json()["type"] == "state"


def test_a_socket_that_sends_no_origin_at_all_is_accepted(socket):
    """Only browsers set Origin. A header nobody sends proves nothing either
    way, so refusing on it would lock out every non-browser client."""
    socket.send_json(synthetic.generate_frames(cycles=1)[0])

    assert socket.receive_json()["type"] == "state"
