"""The `config` command: a phone retuning the thresholds its own Sets are judged by.

Thresholds are frozen for the life of a Set on purpose -- a Set retuned halfway
through has no single definition of a Rep, and its Summary would mean nothing.
So the command is answered between Sets and refused during one.
"""

import pytest

from pushform.analysis import synthetic
from ws_support import drain, kinds

# A shallow push-up: 100 degrees at the bottom, nowhere near the 95 the DOWN
# threshold sits at by default. It is a Rep only under a raised threshold.
SHALLOW_SET = dict(cycles=1, elbow_min_deg=100.0, elbow_max_deg=170.0, cycle_ms=2000)

RAISED = {"cmd": "config", "down_threshold": 120.0, "up_threshold": 160.0}


def test_a_shallow_set_counts_nothing_under_the_default_thresholds(socket):
    """The control: without the config command these Frames are not push-ups."""
    socket.send_json({"cmd": "start", "set_id": "set-1"})

    messages = drain(socket, synthetic.generate_frames(**SHALLOW_SET))

    assert kinds(messages, "summary")[0]["reps"] == 0


def test_config_before_a_set_changes_the_thresholds_that_set_is_judged_by(socket):
    socket.send_json(RAISED)
    accepted = socket.receive_json()
    socket.send_json({"cmd": "start", "set_id": "set-1"})

    messages = drain(socket, synthetic.generate_frames(**SHALLOW_SET))

    assert accepted["type"] == "state", "the config was accepted, not refused"
    assert kinds(messages, "summary")[0]["reps"] == 1


def test_the_new_thresholds_outlive_the_set_they_were_set_for(socket):
    """Per-connection tuning: every Set after the command uses it."""
    socket.send_json(RAISED)
    socket.receive_json()
    socket.send_json({"cmd": "start", "set_id": "set-1"})
    drain(socket, synthetic.generate_frames(**SHALLOW_SET))

    socket.send_json({"cmd": "start", "set_id": "set-2"})
    second = drain(socket, synthetic.generate_frames(**SHALLOW_SET))

    assert kinds(second, "summary")[0]["reps"] == 1


def test_config_during_a_set_is_refused_and_the_set_carries_on(socket):
    socket.send_json({"cmd": "start", "set_id": "set-1"})
    socket.send_json(RAISED)
    messages = drain(socket, synthetic.generate_frames(cycles=1))

    refusals = kinds(messages, "error")
    assert [refusal["code"] for refusal in refusals] == ["config_during_set"]
    assert refusals[0]["message"]
    assert kinds(messages, "summary")[0]["reps"] == 1, "the Set was never disturbed"


@pytest.mark.parametrize(
    ("command", "why"),
    [
        ({"cmd": "config", "down_threshold": 160.0, "up_threshold": 95.0}, "down above up"),
        ({"cmd": "config", "down_threshold": 120.0, "up_threshold": 120.0}, "no hysteresis"),
        ({"cmd": "config", "down_threshold": 0.0, "up_threshold": 155.0}, "zero degrees"),
        ({"cmd": "config", "down_threshold": 95.0, "up_threshold": 180.0}, "a straight line"),
        ({"cmd": "config", "down_threshold": -5.0, "up_threshold": 155.0}, "negative"),
        ({"cmd": "config", "down_threshold": "low", "up_threshold": 155.0}, "not a number"),
        ({"cmd": "config", "up_threshold": 155.0}, "half a pair"),
        ({"cmd": "config"}, "no thresholds at all"),
    ],
)
def test_thresholds_that_could_not_count_a_push_up_are_refused(socket, command, why):
    socket.send_json(command)

    refusal = socket.receive_json()

    assert refusal["type"] == "error", why
    assert refusal["code"] == "invalid_config", why
    assert refusal["message"]


def test_a_refused_config_leaves_the_previous_thresholds_alone(socket):
    socket.send_json(RAISED)
    socket.receive_json()
    socket.send_json({"cmd": "config", "down_threshold": 160.0, "up_threshold": 95.0})
    socket.receive_json()

    socket.send_json({"cmd": "start", "set_id": "set-1"})
    messages = drain(socket, synthetic.generate_frames(**SHALLOW_SET))

    assert kinds(messages, "summary")[0]["reps"] == 1, "the raised thresholds survived"
