"""What a socket is refused for, before anything it says is read as a message.

Two rules, neither about push-ups: who may open a Connection, and how much one
message may weigh. Both are answered from the raw request and the raw frame,
which is why they live outside :class:`~pushform.ws.connection.Connection` --
by the time it sees a message the socket is already open and the bytes are
already in memory.
"""

from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.types import Message

__all__ = ["MAX_MESSAGE_BYTES", "POLICY_VIOLATION", "origin_allowed", "oversized"]

MAX_MESSAGE_BYTES = 8192
"""A Frame of 33 Landmarks is a few hundred bytes. Eight kilobytes leaves room
for a generous set_id and none for anything else."""

POLICY_VIOLATION = 1008
"""The WebSocket close code for "you broke a rule of this endpoint"."""


def origin_allowed(headers: Headers) -> bool:
    """Whether the upgrade may proceed, judged on where the page came from.

    An absent Origin is allowed. Only browsers set it, and it is the browser
    the rule protects: a header nobody sends proves nothing either way, and
    refusing on it would lock out every native and command-line client.

    A present Origin has to name the same host the request was addressed to.
    One service serves both the page and this socket (ADR-0007), so a page on
    any other host is not a page of ours. Same host, not same scheme: the app
    is served over http in development and https in the field.
    """
    origin = headers.get("origin")
    if origin is None:
        return True
    host = headers.get("host")
    return host is not None and urlsplit(origin).netloc.lower() == host.lower()


def oversized(incoming: Message) -> bool:
    """Whether one raw socket message is too big to be anything this app sends.

    Measured on the bytes actually received rather than on anything parsed out
    of them: the point is to stop before the parsing.
    """
    text = incoming.get("text")
    if isinstance(text, str):
        return len(text.encode("utf-8")) > MAX_MESSAGE_BYTES
    data = incoming.get("bytes")
    return isinstance(data, bytes | bytearray) and len(data) > MAX_MESSAGE_BYTES
