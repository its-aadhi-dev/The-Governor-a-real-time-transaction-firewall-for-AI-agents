from __future__ import annotations

from fastapi import WebSocket

from backend.events.bus import event_bus


class WebSocketEventManager:
    """
    Bridge between FastAPI WebSockets and the EventBus.
    """

    async def stream_transaction(
        self,
        websocket: WebSocket,
        transaction_id: str,
    ) -> None:
        await websocket.accept()
        subscription = event_bus.subscribe(transaction_id)

        try:
            while True:
                _, queue = subscription
                event = await queue.get()
                await websocket.send_json(event.to_dict())
        finally:
            event_bus.unsubscribe(transaction_id, subscription)


event_manager = WebSocketEventManager()