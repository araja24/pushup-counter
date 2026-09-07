"""Where a Set waits out a dropped Connection.

A phone that loses Wi-Fi mid-Set must not lose its count. When a Connection
carrying an active Set goes away, the Set is parked here under its id; the next
Connection sends ``resume`` with that id and carries on with the same
Orchestrator, so the counts and the Phase are exactly where they were left.

The window is short on purpose: an orphan holds the analysis of a Set nobody may
ever come back for, so ten seconds after the drop it is thrown away. Nothing
sweeps in the background -- entries past the window are dropped whenever the
store is touched.

    orphans = OrphanStore(now=time.monotonic)
    orphans.park("set-1", orchestrator)
    adoption = orphans.adopt("set-1")
"""

from collections.abc import Callable
from dataclasses import dataclass

from pushform.analysis.orchestrator import Orchestrator

__all__ = ["ORPHAN_TTL_S", "Adoption", "OrphanStore"]

ORPHAN_TTL_S = 10.0
"""Seconds a dropped Set stays adoptable. Long enough for a phone to notice the
socket died and dial back; short enough that a walked-away user is forgotten."""


@dataclass(frozen=True, slots=True)
class Adoption:
    """The answer to "is this Set still parked?".

    Three answers, not two: the Set is here, the Set was here and has expired, or
    nobody has ever heard of it. The Connection tells the phone which.
    """

    orchestrator: Orchestrator | None = None
    expired: bool = False


@dataclass(frozen=True, slots=True)
class _Parked:
    orchestrator: Orchestrator
    dropped_at_s: float


class OrphanStore:
    """Sets whose Connection dropped, keyed by set id."""

    def __init__(self, now: Callable[[], float], ttl_s: float = ORPHAN_TTL_S) -> None:
        self._now = now
        self._ttl_s = ttl_s
        self._parked: dict[str, _Parked] = {}

    @property
    def parked(self) -> frozenset[str]:
        """The set ids still adoptable, as of now."""
        self._purge()
        return frozenset(self._parked)

    def park(self, set_id: str, orchestrator: Orchestrator) -> None:
        """Hold a dropped Set, replacing anything parked under the same id."""
        self._purge()
        self._parked[set_id] = _Parked(orchestrator, self._now())

    def adopt(self, set_id: str) -> Adoption:
        """Hand the Set over, once. Asking again finds nothing: it has been taken."""
        entry = self._parked.pop(set_id, None)
        self._purge()
        if entry is None:
            return Adoption()
        if self._is_expired(entry):
            return Adoption(expired=True)
        return Adoption(orchestrator=entry.orchestrator)

    def _purge(self) -> None:
        """Forget every Set nobody came back for. Silently: nobody is listening."""
        for set_id in [key for key, entry in self._parked.items() if self._is_expired(entry)]:
            del self._parked[set_id]

    def _is_expired(self, entry: _Parked) -> bool:
        return self._now() - entry.dropped_at_s > self._ttl_s
