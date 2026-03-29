"""WebSocket endpoint for realtime updates (admin only)."""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.deps import parse_access_token
from app.realtime import manager

router = APIRouter()


@router.websocket("/ws")
async def events_socket(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    if not token or not token.strip():
        await websocket.close(code=1008)
        return
    user = parse_access_token(token.strip())
    if user is None or user.role != "admin":
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
