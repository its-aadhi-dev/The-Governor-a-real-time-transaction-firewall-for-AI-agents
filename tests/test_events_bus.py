import asyncio
from datetime import datetime, timezone

from backend.events.bus import EventBus, EventMessage


class FakeEvent:
    event_id = "evt-1"
    transaction_id = "txn-1"
    event_type = "GOVERNOR_ALLOW"
    actor_id = "governor"
    sequence_number = 1
    payload = {"decision": "ALLOW"}
    created_at = datetime.now(timezone.utc)


def test_event_message_serializes():
    message = EventMessage.from_model(FakeEvent())

    assert message.event_id == "evt-1"
    assert message.transaction_id == "txn-1"
    assert message.event_type == "GOVERNOR_ALLOW"
    assert message.sequence_number == 1
    assert message.to_dict()["payload"] == {"decision": "ALLOW"}


def test_subscriber_receives_matching_transaction_event():
    async def scenario():
        bus = EventBus()
        subscription = bus.subscribe("txn-1")
        _, queue = subscription

        bus.publish(FakeEvent())
        message = await asyncio.wait_for(queue.get(), timeout=1)

        assert message.transaction_id == "txn-1"
        assert message.event_type == "GOVERNOR_ALLOW"
        bus.unsubscribe("txn-1", subscription)

    asyncio.run(scenario())


def test_subscriber_does_not_receive_other_transaction():
    async def scenario():
        bus = EventBus()
        subscription = bus.subscribe("txn-1")
        _, queue = subscription

        other_event = type("OtherEvent", (FakeEvent,), {"transaction_id": "txn-2"})()
        bus.publish(other_event)
        await asyncio.sleep(0.05)

        assert queue.empty()
        bus.unsubscribe("txn-1", subscription)

    asyncio.run(scenario())


def test_unsubscribe_removes_subscription():
    async def scenario():
        bus = EventBus()
        subscription = bus.subscribe("txn-1")
        bus.unsubscribe("txn-1", subscription)

        bus.publish(FakeEvent())
        await asyncio.sleep(0.05)

        assert "txn-1" not in bus._subscribers

    asyncio.run(scenario())