"""Stall: hovering between the two thresholds without locking out or going down.

Hysteresis means an Elbow Angle parked in the band changes nothing at all --
no Phase, no Rep, no feedback. A user stuck there needs telling, and telling
once, not thirty times a second.
"""

from pushform.analysis import synthetic
from pushform.analysis.events import RepCompleted, Stall, StallCleared

# 125 degrees sits squarely between the DOWN threshold (95) and the UP one
# (155): a half-locked arm the Phase machine is deliberately blind to.
BAND_ANGLE = 125.0
LOCKED_OUT = 170.0


def of_type(events, kind):
    return [event for event in events if isinstance(event, kind)]


def test_holding_between_the_thresholds_for_two_seconds_stalls_once(run_set):
    frames = synthetic.frames_from_angles([LOCKED_OUT] * 5 + [BAND_ANGLE] * 60, fps=30)

    orchestrator, events = run_set(frames)

    assert len(of_type(events, Stall)) == 1, "one prompt, not one a Frame"
    assert orchestrator.state.stalled is True
    assert orchestrator.state.reps == 0


def test_a_brief_pause_between_the_thresholds_is_not_a_stall(run_set):
    """Two thirds of a second in the band is a slow rep, not a stuck one."""
    frames = synthetic.frames_from_angles([LOCKED_OUT] * 5 + [BAND_ANGLE] * 20, fps=30)

    orchestrator, events = run_set(frames)

    assert of_type(events, Stall) == []
    assert orchestrator.state.stalled is False


def test_leaving_the_band_clears_the_stall_and_counts_no_rep(run_set):
    """Locking out after a stall ends the prompt. Nothing went down, so nothing counts."""
    frames = synthetic.frames_from_angles(
        [LOCKED_OUT] * 5 + [BAND_ANGLE] * 60 + [LOCKED_OUT] * 10, fps=30
    )

    orchestrator, events = run_set(frames)

    assert len(of_type(events, Stall)) == 1
    assert len(of_type(events, StallCleared)) == 1
    assert orchestrator.state.stalled is False
    assert of_type(events, RepCompleted) == []


def test_going_down_out_of_a_stall_still_counts_the_rep(run_set):
    """A stall is a prompt, not a penalty: the push-up that follows still counts."""
    frames = synthetic.frames_from_angles(
        [LOCKED_OUT] * 5 + [BAND_ANGLE] * 60 + [70.0] * 25 + [LOCKED_OUT] * 15, fps=30
    )

    orchestrator, events = run_set(frames)

    assert len(of_type(events, Stall)) == 1
    assert orchestrator.state.stalled is False
    assert orchestrator.state.reps == 1


def test_a_set_of_ordinary_push_ups_never_stalls(run_set):
    """The band is crossed twice a Rep; crossing it is not dwelling in it."""
    orchestrator, events = run_set(synthetic.generate_frames(cycles=3))

    assert of_type(events, Stall) == []
    assert orchestrator.state.stalled is False
    assert orchestrator.state.reps == 3
