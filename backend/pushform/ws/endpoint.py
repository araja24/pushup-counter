"""`/ws`: the socket the phone streams Landmarks down.

All this route knows is how to read a message and write the answers; what a
message means belongs to :class:`~pushform.ws.connection.Connection`.
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.types import Message

from pushform.ws.connection import Connection, error
from pushform.ws.policy import POLICY_VIOLATION, origin_allowed, oversized

router = APIRouter()


@router.websocket("/ws")
async def stream_landmarks(websocket: WebSocket) -> None:
    """Hold one Connection open until the phone goes away.

    Two ways it does not stay open: a page from another site is never let in,
    and a message far too big to be a Frame ends the Connection rather than
    being parsed.
    """
    if not origin_allowed(websocket.headers):
        await websocket.close(code=POLICY_VIOLATION)
        return
    await websocket.accept()
    connection = Connection(now=websocket.app.state.now)
    try:
        while True:
            incoming = await websocket.receive()
            if incoming["type"] == "websocket.disconnect":
                return
            if oversized(incoming):
                await websocket.close(code=POLICY_VIOLATION)
                return
            for reply in answer(connection, incoming):
                await websocket.send_json(reply)
    except WebSocketDisconnect:
        return


def answer(connection: Connection, incoming: Message) -> list[dict]:
    """Turn one raw socket message into the messages to send back.

    Landmarks travel as JSON text. Bytes and unparseable text are refused the
    same way a malformed Frame is: an error message, and the socket stays open.

    ASGI allows a receive to carry ``"text": None`` alongside its bytes, so the
    test is that a real string arrived, not that the key is present.
    """
    if not isinstance(incoming.get("text"), str):
        return [error("malformed", "Send JSON text; binary messages are not read.")]
    try:
        message = json.loads(incoming["text"])
    except json.JSONDecodeError as bad_json:
        return [error("malformed", f"Message is not JSON: {bad_json}")]
    return connection.handle(message)
