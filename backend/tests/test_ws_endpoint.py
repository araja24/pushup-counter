"""The landmark Connection: one socket, several Sets, live State on the wire.

These drive `/ws` exactly as the phone does -- open, stream Frames, start, stop --
so the wire contract is asserted from outside rather than from the Connection's
own vocabulary.
"""

import pytest

from pushform.analysis import synthetic
from pushform.ws.connection import Connection
from pushform.ws.endpoint import answer
from ws_support import drain, kinds, read_until, read_until_counting


def test_a_clean_set_of_five_counts_five_and_summarises(socket):
    socket.send_json({"cmd": "start", "set_id": "set-1"})

    messages = drain(socket, synthetic.generate_frames(cycles=5))

    reps = kinds(messages, "rep")
    assert [rep["index"] for rep in reps] == [1, 2, 3, 4, 5]
    assert all(rep["counted"] is True for rep in reps)
    assert kinds(messages, "state"), "the phone needs live State while the Set runs"
    (summary,) = kinds(messages, "summary")
    assert summary["reps"] == 5
    assert summary["rejected"] == 0
    assert summary["faults"] == {"partial_rom": 0, "hip_sag": 0, "hip_pike": 0}
    assert summary["duration_ms"] > 0
    assert summary["avg_rep_ms"] > 0


def test_a_state_message_carries_the_documented_shape(socket):
    socket.send_json({"cmd": "start", "set_id": "set-1"})
    socket.send_json(synthetic.generate_frames(cycles=1)[0])

    state = socket.receive_json()

    assert set(state) == {
        "type",
        "reps",
        "rejected",
        "phase",
        "elbow_angle",
        "hip_angle",
        "aligned",
        "tracking",
        "stalled",
        "side",
    }
    assert state["phase"] == "UP"
    assert state["stalled"] is False
    assert state["rejected"] == 0
    assert state["aligned"] is True, "the placeholder until the form rules land"


def test_a_rep_message_carries_the_documented_shape(socket):
    socket.send_json({"cmd": "start", "set_id": "set-1"})

    messages = drain(socket, synthetic.generate_frames(cycles=1))

    (rep,) = kinds(messages, "rep")
    assert set(rep) == {
        "type",
        "index",
        "counted",
        "label",
        "reason",
        "source",
        "min_elbow",
        "max_elbow",
        "duration_ms",
        "confidence",
    }
    assert rep["label"] == "unlabelled"
    assert rep["source"] == "none"


def test_frames_before_start_report_idle_and_never_a_rep(clock, socket):
    """Two cycles of push-ups before Start are watched, reported and not counted."""
    clock.step_s = 1.0 / 30.0
    frames = synthetic.generate_frames(cycles=2)

    for frame in frames:
        socket.send_json(frame)
    socket.send_json({"cmd": "start", "set_id": "set-1"})
    before_start = read_until_counting(socket)

    assert len(before_start) >= 20, "the readout stayed live the whole time"
    assert kinds(before_start, "rep") == []
    assert kinds(before_start, "state") == before_start
    assert all(state["phase"] == "IDLE" for state in before_start)
    assert all(state["reps"] == 0 for state in before_start)


def test_a_frame_before_start_still_reports_the_live_elbow_angle(socket):
    socket.send_json(synthetic.generate_frames(cycles=1)[0])

    state = socket.receive_json()

    assert state["phase"] == "IDLE"
    assert state["elbow_angle"] == pytest.approx(170.0, abs=5.0)
    assert state["side"] in {"left", "right"}


def test_reset_mid_set_yields_no_summary_and_the_next_set_counts_from_zero(socket):
    socket.send_json({"cmd": "start", "set_id": "set-1"})
    for frame in synthetic.generate_frames(cycles=3):
        socket.send_json(frame)

    socket.send_json({"cmd": "reset"})
    socket.send_json({"cmd": "start", "set_id": "set-2"})
    messages = drain(socket, synthetic.generate_frames(cycles=2))

    indices = [rep["index"] for rep in kinds(messages, "rep")]
    assert indices == [1, 2, 3, 1, 2], "the discarded Set's Reps, then a fresh count"
    summaries = kinds(messages, "summary")
    assert len(summaries) == 1, "a reset Set is discarded, never summarised"
    assert summaries[0]["reps"] == 2


def test_another_set_on_the_same_connection_starts_from_zero(socket):
    socket.send_json({"cmd": "start", "set_id": "set-1"})
    first = drain(socket, synthetic.generate_frames(cycles=3))

    socket.send_json({"cmd": "start", "set_id": "set-2"})
    second = drain(socket, synthetic.generate_frames(cycles=1))

    assert kinds(first, "summary")[0]["reps"] == 3
    assert [rep["index"] for rep in kinds(second, "rep")] == [1]
    assert kinds(second, "summary")[0]["reps"] == 1


@pytest.mark.parametrize(
    ("message", "code"),
    [
        ({"cmd": "fly"}, "unknown_command"),
        ({"cmd": "start"}, "malformed"),
        ({"hello": "there"}, "malformed"),
        ([1, 2, 3], "malformed"),
    ],
)
def test_a_bad_message_is_refused_and_the_connection_stays_open(socket, message, code):
    socket.send_json(message)
    error = socket.receive_json()

    assert error["type"] == "error"
    assert error["code"] == code
    assert error["message"]

    socket.send_json({"cmd": "start", "set_id": "set-1"})
    messages = drain(socket, synthetic.generate_frames(cycles=1))
    assert kinds(messages, "summary")[0]["reps"] == 1


@pytest.mark.parametrize("command", ["stop", "reset"])
def test_ending_a_set_that_is_not_running_says_so_in_its_own_words(socket, command):
    """A phone that stops twice has sent nothing malformed; it is simply late."""
    socket.send_json({"cmd": command})

    error = socket.receive_json()

    assert error["type"] == "error"
    assert error["code"] == "no_active_set"


def test_binary_data_is_refused_and_the_connection_stays_open(socket):
    """Landmarks arrive as JSON text. Bytes must not take the Connection down."""
    socket.send_bytes(bytes([0, 1, 2]))

    error = socket.receive_json()

    assert error["type"] == "error"
    assert error["code"] == "malformed"

    socket.send_json({"cmd": "start", "set_id": "set-1"})
    messages = drain(socket, synthetic.generate_frames(cycles=1))
    assert kinds(messages, "summary")[0]["reps"] == 1


def test_a_message_that_is_not_json_is_refused_and_the_connection_stays_open(socket):
    socket.send_text("not json at all")
    error = socket.receive_json()

    assert error == {
        "type": "error",
        "code": "malformed",
        "message": error["message"],
    }

    socket.send_json({"cmd": "start", "set_id": "set-1"})
    messages = drain(socket, synthetic.generate_frames(cycles=1))
    assert kinds(messages, "summary")[0]["reps"] == 1


def test_a_malformed_frame_is_refused_and_the_connection_stays_open(socket):
    socket.send_json({"cmd": "start", "set_id": "set-1"})
    socket.send_json({"t": 0, "lm": [[0.0, 0.0, 0.0, 0.9]] * 5})

    error = read_until(socket, "error")[-1]

    assert error["code"] == "malformed"

    messages = drain(socket, synthetic.generate_frames(cycles=1))
    assert kinds(messages, "summary")[0]["reps"] == 1


def test_state_messages_are_throttled_to_fifteen_a_second(clock, socket):
    """Thirty Frames a second for two seconds is about thirty State messages."""
    clock.step_s = 1.0 / 30.0
    frames = synthetic.frames_from_angles([170.0] * 60, fps=30)

    socket.send_json({"cmd": "start", "set_id": "set-1"})
    messages = drain(socket, frames)

    states = kinds(messages, "state")
    assert 25 <= len(states) <= 32, f"{len(states)} State messages for 60 Frames"


def test_a_receive_carrying_a_null_text_field_is_refused_rather_than_crashing():
    """ASGI allows {"type": "websocket.receive", "text": None, "bytes": ...}.

    A "text" in message guard passes that shape straight to the JSON parser,
    which raises on None and takes the whole Connection down. Only a real string
    is a message this endpoint can read.
    """
    connection = Connection(now=lambda: 0.0)

    replies = answer(
        connection, {"type": "websocket.receive", "text": None, "bytes": bytes([0, 1])}
    )

    assert [reply["type"] for reply in replies] == ["error"]
    assert [reply["code"] for reply in replies] == ["malformed"]
