from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.events.websocket import event_manager


router = APIRouter(tags=["Events"])


@router.websocket("/events/{transaction_id}")
async def transaction_events(
    websocket: WebSocket,
    transaction_id: str,
):
    try:
        await event_manager.stream_transaction(
            websocket,
            transaction_id,
        )
    except WebSocketDisconnect:
        pass