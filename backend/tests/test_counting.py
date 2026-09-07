"""Counting Reps from synthetic motion: the behaviour ADR-0004 exists to give.

Every test here drives the Orchestrator from outside with wire-shape Frames and
asserts on the events it returns and the State it reports.
"""

import pytest

from pushform.analysis import synthetic
from pushform.analysis.events import Phase, PhaseChanged, RepCompleted

BOUNCE_FPS = 100
"""10 ms per Frame, so a DOWN Phase can be an exact number of milliseconds."""


def reps_of(events):
    return [event for event in events if isinstance(event, RepCompleted)]


def phase_changes(events):
    return [event for event in events if isinstance(event, PhaseChanged)]


def square_down_phase(down_frames: int) -> list[dict]:
    """Locked out, then a hard DOWN Phase of ``down_frames`` Frames, then locked out.

    Square edges keep the median filter's lag identical on the way in and on the
    way out, so the DOWN Phase lasts exactly ``down_frames`` Frames.
    """
    lead, tail = 12, 12
    angles = [170.0] * lead + [80.0] * down_frames + [170.0] * tail
    return synthetic.frames_from_angles(angles, fps=BOUNCE_FPS)


@pytest.mark.parametrize("cycles", [1, 5, 20])
@pytest.mark.parametrize("fps", [30, 15])
def test_clean_cycles_yield_exactly_one_rep_each(run_set, cycles, fps):
    frames = synthetic.generate_frames(cycles=cycles, fps=fps)

    orchestrator, events = run_set(frames)

    reps = reps_of(events)
    assert len(reps) == cycles
    assert [rep.index for rep in reps] == list(range(1, cycles + 1))
    assert orchestrator.state.reps == cycles


def test_a_counted_rep_reports_its_depth_and_its_timing(run_set):
    frames = synthetic.generate_frames(cycles=1, elbow_min_deg=70.0, elbow_max_deg=170.0)

    _, events = run_set(frames)

    (rep,) = reps_of(events)
    assert rep.counted is True
    assert rep.label == "unlabelled"
    assert rep.reason is None
    assert rep.source == "none"
    assert rep.confidence is None
    assert rep.min_elbow == pytest.approx(70.0, abs=2.0)
    assert rep.max_elbow > 155.0
    assert rep.down_ms + rep.up_ms == rep.duration_ms
    assert rep.down_ms > 0
    assert rep.up_ms > 0


def test_a_rep_is_bracketed_by_a_phase_change_in_each_direction(run_set):
    frames = synthetic.generate_frames(cycles=2)

    _, events = run_set(frames)

    assert [change.phase for change in phase_changes(events)] == [
        Phase.DOWN,
        Phase.UP,
        Phase.DOWN,
        Phase.UP,
    ]


def test_an_angle_oscillating_inside_the_band_never_changes_phase(run_set):
    inside_the_band = [100.0, 150.0, 110.0, 145.0, 120.0, 140.0] * 10

    orchestrator, events = run_set(synthetic.frames_from_angles(inside_the_band))

    assert events == []
    assert orchestrator.state.reps == 0
    assert orchestrator.state.phase is Phase.UP


def test_rising_into_the_band_but_not_past_it_does_not_leave_down(run_set):
    angles = [170.0] * 10 + [80.0] * 10 + [100.0, 150.0, 110.0, 145.0, 120.0, 140.0] * 10

    orchestrator, events = run_set(synthetic.frames_from_angles(angles))

    assert [change.phase for change in phase_changes(events)] == [Phase.DOWN]
    assert reps_of(events) == []
    assert orchestrator.state.phase is Phase.DOWN


def test_a_sequence_starting_at_the_bottom_does_not_count_its_first_ascent(run_set):
    frames = synthetic.generate_frames(cycles=1, start_phase="down")

    orchestrator, events = run_set(frames)

    assert reps_of(events) == []
    assert orchestrator.state.reps == 0
    assert phase_changes(events) != []


def test_after_a_bottom_start_every_later_cycle_still_counts(run_set):
    frames = synthetic.generate_frames(cycles=3, start_phase="down")

    orchestrator, _ = run_set(frames)

    assert orchestrator.state.reps == 2


def test_a_down_phase_shorter_than_the_bounce_threshold_is_not_a_rep(run_set):
    _, events = run_set(square_down_phase(down_frames=30))

    assert [change.phase for change in phase_changes(events)] == [Phase.DOWN, Phase.UP]
    assert reps_of(events) == []


def test_a_down_phase_past_the_bounce_threshold_is_a_rep(run_set):
    _, events = run_set(square_down_phase(down_frames=50))

    (rep,) = reps_of(events)
    assert rep.duration_ms == 500


def test_the_median_filter_swallows_a_single_frame_spike_across_the_threshold(run_set):
    angles = [170.0] * 20 + [60.0] + [170.0] * 20

    orchestrator, events = run_set(synthetic.frames_from_angles(angles))

    assert events == []
    assert orchestrator.state.phase is Phase.UP


def test_a_spike_wide_enough_to_survive_the_filter_does_change_phase(run_set):
    angles = [170.0] * 20 + [60.0] * 5 + [170.0] * 20

    _, events = run_set(synthetic.frames_from_angles(angles))

    assert [change.phase for change in phase_changes(events)] == [Phase.DOWN, Phase.UP]


def test_dropped_frames_do_not_lose_reps(run_set):
    frames = synthetic.generate_frames(cycles=4, dropped_frames={7, 8, 33, 61, 62, 63})

    orchestrator, _ = run_set(frames)

    assert orchestrator.state.reps == 4


def test_a_noisy_capture_still_counts_its_cycles(run_set):
    frames = synthetic.generate_frames(cycles=5, noise_deg=3.0, seed=11)

    orchestrator, _ = run_set(frames)

    assert orchestrator.state.reps == 5


@pytest.mark.parametrize("facing", ["left", "right"])
def test_counting_is_the_same_whichever_way_the_body_faces(run_set, facing):
    frames = synthetic.generate_frames(cycles=6, facing=facing)

    orchestrator, _ = run_set(frames)

    assert orchestrator.state.reps == 6
