"""Start, stop and reset: one Set from IDLE back to IDLE."""

import pytest

from pushform.analysis import synthetic
from pushform.analysis.events import Phase, RepCompleted, Summary
from pushform.analysis.orchestrator import Orchestrator


def test_frames_before_start_are_ignored_and_the_phase_stays_idle():
    orchestrator = Orchestrator()
    frames = synthetic.generate_frames(cycles=2)

    events = [event for frame in frames for event in orchestrator.process(frame)]

    assert events == []
    assert orchestrator.state.phase is Phase.IDLE
    assert orchestrator.state.reps == 0


def test_a_started_set_begins_locked_out_with_nothing_counted():
    orchestrator = Orchestrator()

    orchestrator.start("set-1")

    assert orchestrator.state.phase is Phase.UP
    assert orchestrator.state.reps == 0
    assert orchestrator.set_id == "set-1"


def test_stopping_emits_a_summary_of_the_set(run_set):
    frames = synthetic.generate_frames(cycles=4, cycle_ms=1500, fps=30)
    orchestrator, events = run_set(frames)
    reps = [event for event in events if isinstance(event, RepCompleted)]

    (summary,) = orchestrator.stop()

    assert isinstance(summary, Summary)
    assert summary.reps == 4
    assert summary.rejected == 0
    assert set(summary.faults.values()) == {0}
    assert summary.duration_ms == frames[-1]["t"] - frames[0]["t"]
    assert summary.avg_rep_ms == pytest.approx(
        sum(rep.duration_ms for rep in reps) / len(reps)
    )


def test_a_set_with_no_reps_summarises_as_zero(run_set):
    orchestrator, _ = run_set(synthetic.frames_from_angles([170.0] * 30))

    (summary,) = orchestrator.stop()

    assert summary.reps == 0
    assert summary.avg_rep_ms == 0.0


def test_stopping_leaves_the_phase_idle_and_ignores_later_frames(run_set):
    orchestrator, _ = run_set(synthetic.generate_frames(cycles=2))
    orchestrator.stop()

    later = [
        event for frame in synthetic.generate_frames(cycles=2) for event in orchestrator.process(frame)
    ]

    assert later == []
    assert orchestrator.state.phase is Phase.IDLE
    assert orchestrator.state.reps == 2


def test_stopping_a_set_that_never_started_emits_nothing():
    assert Orchestrator().stop() == []


def test_reset_emits_no_summary_and_zeroes_the_count(run_set):
    orchestrator, _ = run_set(synthetic.generate_frames(cycles=3))
    assert orchestrator.state.reps == 3

    assert orchestrator.reset() is None
    assert orchestrator.state.reps == 0
    assert orchestrator.state.phase is Phase.IDLE
    assert orchestrator.set_id is None


def test_a_second_set_starts_from_zero(run_set):
    orchestrator, _ = run_set(synthetic.generate_frames(cycles=3))
    orchestrator.stop()

    orchestrator.start("set-2")
    for frame in synthetic.generate_frames(cycles=1):
        orchestrator.process(frame)

    assert orchestrator.state.reps == 1
    assert orchestrator.set_id == "set-2"


def test_a_reset_set_counts_again_from_the_first_lockout(run_set):
    orchestrator, _ = run_set(synthetic.generate_frames(cycles=3))
    orchestrator.reset()

    orchestrator.start("set-3")
    for frame in synthetic.generate_frames(cycles=2):
        orchestrator.process(frame)

    assert orchestrator.state.reps == 2


def test_the_state_snapshot_reports_the_current_frame(run_set):
    frames = synthetic.generate_frames(cycles=1, hip_deviation_deg=0.0)

    orchestrator, _ = run_set(frames)
    state = orchestrator.state

    assert state.phase is Phase.UP
    assert state.elbow_angle == pytest.approx(170.0, abs=5.0)
    assert state.hip_angle == pytest.approx(180.0, abs=1.0)
    assert state.side == "left"
    assert state.tracking is True
    assert state.aligned is None
    assert state.stalled is False
    assert state.rejected == 0
