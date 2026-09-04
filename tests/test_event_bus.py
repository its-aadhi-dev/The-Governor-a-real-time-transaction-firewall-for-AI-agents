import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from backend.events.bus import EventBus, EventMessage
from backend.events.session_hooks import (
    discard_uncommitted_events,
    publish_committed_events,
)


def make_event():
    return type(
        "Event",
        (),
        {
            "event_id": "evt-1",
            "transaction_id": "txn-1",
            "event_type": "GOVERNOR_ALLOW",
            "actor_id": "governor",
            "sequence_number": 1,
            "payload": {"decision": "ALLOW"},
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        },
    )()


def test_event_message_serializes_model():
    message = EventMessage.from_model(make_event())

    assert message.to_dict() == {
        "event_id": "evt-1",
        "transaction_id": "txn-1",
        "event_type": "GOVERNOR_ALLOW",
        "actor_id": "governor",
        "sequence_number": 1,
        "payload": {"decision": "ALLOW"},
        "created_at": "2026-01-01T00:00:00+00:00",
    }


def test_event_bus_delivers_to_transaction_subscriber():
    async def scenario():
        bus = EventBus()
        subscription = bus.subscribe("txn-1")
        _, queue = subscription

        bus.publish(make_event())
        message = await asyncio.wait_for(queue.get(), timeout=1)

        assert message.event_type == "GOVERNOR_ALLOW"
        bus.unsubscribe("txn-1", subscription)

    asyncio.run(scenario())


def test_commit_publishes_pending_events():
    session = Mock()
    event = make_event()
    session.info = {"governor_pending_events": [event]}

    with patch("backend.events.session_hooks.event_bus.publish") as publish:
        publish_committed_events(session)

    publish.assert_called_once_with(event)
    assert session.info == {}


def test_rollback_discards_pending_events():
    session = Mock()
    session.info = {"governor_pending_events": [make_event()]}

    discard_uncommitted_events(session)

    assert session.info == {}