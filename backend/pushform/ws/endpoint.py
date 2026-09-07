"""`/ws`: the socket the phone streams Landmarks down.

All this route knows is how to read a message and write the answers; what a
message means belongs to :class:`~pushform.ws.connection.Connection`.
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from pushform.ws.connection import Connection, error

router = APIRouter()


@router.websocket("/ws")
async def stream_landmarks(websocket: WebSocket) -> None:
    """Hold one Connection open until the phone goes away."""
    await websocket.accept()
    connection = Connection(now=websocket.app.state.now)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                message = json.loads(text)
            except json.JSONDecodeError as bad_json:
                outgoing = [error("malformed", f"Message is not JSON: {bad_json}")]
            else:
                outgoing = connection.handle(message)
            for reply in outgoing:
                await websocket.send_json(reply)
    except WebSocketDisconnect:
        return
