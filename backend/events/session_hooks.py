from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.orm import Session

from backend.events.bus import event_bus


PENDING_EVENTS_KEY = "governor_pending_events"


@event.listens_for(Session, "after_commit")
def publish_committed_events(session: Session) -> None:
    events = session.info.pop(PENDING_EVENTS_KEY, [])
    for event_model in events:
        event_bus.publish(event_model)


@event.listens_for(Session, "after_rollback")
def discard_uncommitted_events(session: Session) -> None:
    session.info.pop(PENDING_EVENTS_KEY, [])