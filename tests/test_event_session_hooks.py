from backend.events import session_hooks


class FakeSession:
    def __init__(self, events=None):
        self.info = {"governor_pending_events": events or []}


def test_pending_events_are_published_after_commit(monkeypatch):
    published = []
    monkeypatch.setattr(session_hooks.event_bus, "publish", published.append)

    event = object()
    session = FakeSession([event])

    session_hooks.publish_committed_events(session)

    assert published == [event]
    assert "governor_pending_events" not in session.info


def test_pending_events_are_discarded_after_rollback():
    session = FakeSession([object()])

    session_hooks.discard_uncommitted_events(session)

    assert "governor_pending_events" not in session.info