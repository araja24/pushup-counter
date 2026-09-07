"""The replay CLI: a Recording on disk in, an event log and a Rep count out."""

import json

import pytest

from pushform.analysis import replay, synthetic


@pytest.fixture
def recording(tmp_path):
    """Write a Recording in the shape the record screen downloads."""

    def _recording(frames, label="good", name="recording.json"):
        path = tmp_path / name
        path.write_text(json.dumps({"label": label, "frames": frames}), encoding="utf-8")
        return path

    return _recording


def test_it_prints_the_rep_count_for_a_synthetic_recording(recording, capsys):
    path = recording(synthetic.generate_frames(cycles=5))

    exit_code = replay.main([str(path)])

    assert exit_code == 0
    assert "Counted reps: 5" in capsys.readouterr().out


def test_it_logs_every_phase_change_and_rep(recording, capsys):
    path = recording(synthetic.generate_frames(cycles=2))

    replay.main([str(path)])

    lines = capsys.readouterr().out.splitlines()

    assert sum("phase" in line for line in lines) == 4
    assert [line.split()[1] for line in lines if line.strip().startswith("rep ")] == ["1", "2"]


def test_an_unlabelled_recording_still_replays(recording, capsys):
    path = recording(synthetic.generate_frames(cycles=1), label=None)

    assert replay.main([str(path)]) == 0
    assert "Counted reps: 1" in capsys.readouterr().out


def test_a_recording_with_no_reps_reports_zero(recording, capsys):
    path = recording(synthetic.frames_from_angles([170.0] * 30))

    replay.main([str(path)])

    assert "Counted reps: 0" in capsys.readouterr().out


def test_a_missing_recording_reports_the_problem_instead_of_a_traceback(tmp_path, capsys):
    exit_code = replay.main([str(tmp_path / "nope.json")])

    assert exit_code == 1
    assert "nope.json" in capsys.readouterr().err


def test_a_recording_without_frames_reports_the_problem_instead_of_a_traceback(tmp_path, capsys):
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps({"label": "good"}), encoding="utf-8")

    exit_code = replay.main([str(path)])

    assert exit_code == 1
    assert "malformed recording" in capsys.readouterr().err


def test_a_recording_that_is_not_an_envelope_reports_the_problem(tmp_path, capsys):
    path = tmp_path / "bare-list.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    assert replay.main([str(path)]) == 1
    assert "malformed recording" in capsys.readouterr().err


def test_a_recording_with_a_malformed_frame_reports_the_problem(recording, capsys):
    path = recording([{"t": 0, "lm": [[0.0, 0.0, 0.0, 0.9]] * 5}])

    assert replay.main([str(path)]) == 1
    assert "malformed recording" in capsys.readouterr().err


def test_a_recording_of_unreadable_json_reports_the_problem(tmp_path, capsys):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")

    assert replay.main([str(path)]) == 1
    assert "not valid JSON" in capsys.readouterr().err
