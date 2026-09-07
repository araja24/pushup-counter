"""`/ws`: the socket the phone streams Landmarks down.

All this route knows is how to read a message and write the answers; what a
message means belongs to :class:`~pushform.ws.connection.Connection`.
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.types import Message

from pushform.ws.connection import Connection, error

router = APIRouter()


@router.websocket("/ws")
async def stream_landmarks(websocket: WebSocket) -> None:
    """Hold one Connection open until the phone goes away."""
    await websocket.accept()
    connection = Connection(now=websocket.app.state.now, orphans=websocket.app.state.orphans)
    try:
        while True:
            incoming = await websocket.receive()
            if incoming["type"] == "websocket.disconnect":
                return
            for reply in answer(connection, incoming):
                await websocket.send_json(reply)
    except WebSocketDisconnect:
        return
    finally:
        # However the socket ended, a Set in progress waits for the phone to dial back.
        connection.park()


def answer(connection: Connection, incoming: Message) -> list[dict]:
    """Turn one raw socket message into the messages to send back.

    Landmarks travel as JSON text. Bytes and unparseable text are refused the
    same way a malformed Frame is: an error message, and the socket stays open.
    """
    if "text" not in incoming:
        return [error("malformed", "Send JSON text; binary messages are not read.")]
    try:
        message = json.loads(incoming["text"])
    except json.JSONDecodeError as bad_json:
        return [error("malformed", f"Message is not JSON: {bad_json}")]
    return connection.handle(message)
