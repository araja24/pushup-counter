"""The orphan store: where a Set waits out a dropped Connection.

Time is injected, so the ten-second window is asserted without sleeping.
"""

import pytest

from pushform.analysis.orchestrator import Orchestrator
from pushform.ws.orphans import ORPHAN_TTL_S, OrphanStore


class Clock:
    """A wall clock the test winds on by hand."""

    def __init__(self) -> None:
        self.seconds = 0.0

    def __call__(self) -> float:
        return self.seconds


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def store(clock: Clock) -> OrphanStore:
    return OrphanStore(now=clock, ttl_s=ORPHAN_TTL_S)


def parked_set() -> Orchestrator:
    orchestrator = Orchestrator()
    orchestrator.start("set-1")
    return orchestrator


def test_the_window_is_ten_seconds():
    assert ORPHAN_TTL_S == 10.0


def test_a_set_parked_moments_ago_comes_back_with_its_orchestrator(clock, store):
    orchestrator = parked_set()
    store.park("set-1", orchestrator)

    clock.seconds = 9.9
    adoption = store.adopt("set-1")

    assert adoption.orchestrator is orchestrator
    assert adoption.expired is False


def test_a_set_parked_longer_than_the_window_is_gone_and_says_it_expired(clock, store):
    store.park("set-1", parked_set())

    clock.seconds = 10.1
    adoption = store.adopt("set-1")

    assert adoption.orchestrator is None
    assert adoption.expired is True


def test_a_set_id_that_was_never_parked_is_unknown_rather_than_expired(store):
    adoption = store.adopt("never-heard-of-it")

    assert adoption.orchestrator is None
    assert adoption.expired is False


def test_a_parked_set_is_handed_over_once_and_only_once(store):
    store.park("set-1", parked_set())

    first = store.adopt("set-1")
    second = store.adopt("set-1")

    assert first.orchestrator is not None
    assert second.orchestrator is None
    assert second.expired is False, "an adopted Set is gone, not expired"


def test_entries_past_the_window_are_dropped_on_access_and_younger_ones_kept(clock, store):
    store.park("old", parked_set())
    clock.seconds = 6.0
    store.park("young", parked_set())

    clock.seconds = 11.0
    assert store.parked == frozenset({"young"}), "the old Set was purged on access"
    assert store.adopt("young").orchestrator is not None


def test_re_parking_a_set_id_restarts_its_window(clock, store):
    store.park("set-1", parked_set())
    clock.seconds = 9.0
    store.park("set-1", parked_set())

    clock.seconds = 15.0
    assert store.adopt("set-1").orchestrator is not None
