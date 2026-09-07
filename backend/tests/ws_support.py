"""Shared plumbing for the tests that drive `/ws` exactly as the phone does.

Every socket test opens a real app, streams Frames and reads messages back, so
the wire contract is asserted from outside rather than from the Connection's
own vocabulary. What differs between them is only which rule they are after.
"""

__all__ = ["Clock", "drain", "kinds", "read_until", "read_until_counting"]


class Clock:
    """A wall clock the test winds on, so timing is tested without sleeping."""

    def __init__(self, step_s: float = 0.0) -> None:
        self.seconds = 0.0
        self.step_s = step_s
        """Seconds every reading moves the clock on. Set it before sending anything."""

    def __call__(self) -> float:
        now = self.seconds
        self.seconds += self.step_s
        return now


def drain(ws, frames: list[dict]) -> list[dict]:
    """Stream Frames, stop the Set, and read everything back up to the Summary."""
    for frame in frames:
        ws.send_json(frame)
    ws.send_json({"cmd": "stop"})
    return read_until(ws, "summary")


def read_until(ws, kind: str) -> list[dict]:
    messages = []
    while True:
        message = ws.receive_json()
        messages.append(message)
        if message["type"] == kind:
            return messages


def read_until_counting(ws) -> list[dict]:
    """Everything said before the Set started, up to but not including the first
    State that is counting."""
    before = []
    while True:
        message = ws.receive_json()
        if message["type"] == "state" and message["phase"] != "IDLE":
            return before
        before.append(message)


def kinds(messages: list[dict], kind: str) -> list[dict]:
    return [message for message in messages if message["type"] == kind]
