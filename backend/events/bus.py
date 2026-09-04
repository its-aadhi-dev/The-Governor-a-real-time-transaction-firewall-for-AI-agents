from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EventMessage:
    event_id: str
    transaction_id: str
    event_type: str
    actor_id: str | None
    sequence_number: int
    payload: dict[str, Any]
    created_at: str

    @classmethod
    def from_model(cls, event) -> "EventMessage":
        return cls(
            event_id=event.event_id,
            transaction_id=event.transaction_id,
            event_type=event.event_type,
            actor_id=event.actor_id,
            sequence_number=event.sequence_number,
            payload=dict(event.payload or {}),
            created_at=event.created_at.isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "transaction_id": self.transaction_id,
            "event_type": self.event_type,
            "actor_id": self.actor_id,
            "sequence_number": self.sequence_number,
            "payload": self.payload,
            "created_at": self.created_at,
        }


class EventBus:
    """
    In-process real-time event distribution.

    Database persistence remains authoritative. Events are published only
    after the SQLAlchemy transaction commits.
    """

    def __init__(self) -> None:
        self._subscribers: dict[
            str,
            set[tuple[asyncio.AbstractEventLoop, asyncio.Queue[EventMessage]]],
        ] = defaultdict(set)

    def subscribe(
        self,
        transaction_id: str,
    ) -> tuple[asyncio.AbstractEventLoop, asyncio.Queue[EventMessage]]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[EventMessage] = asyncio.Queue()
        self._subscribers[transaction_id].add((loop, queue))
        return loop, queue

    def unsubscribe(
        self,
        transaction_id: str,
        subscription: tuple[
            asyncio.AbstractEventLoop,
            asyncio.Queue[EventMessage],
        ],
    ) -> None:
        subscribers = self._subscribers.get(transaction_id)
        if not subscribers:
            return
        subscribers.discard(subscription)
        if not subscribers:
            self._subscribers.pop(transaction_id, None)

    def publish(self, event) -> None:
        message = EventMessage.from_model(event)
        subscribers = list(self._subscribers.get(message.transaction_id, set()))

        for loop, queue in subscribers:
            if loop.is_closed():
                continue
            loop.call_soon_threadsafe(queue.put_nowait, message)


event_bus = EventBus()