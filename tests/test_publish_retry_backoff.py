from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
import app.db.models  # noqa: F401
from app.db.models.topic import Topic
from app.models.topic import Category, Priority, TopicStatus
from app.services.publish_service import PublishService


class FakeLinkedInClient:
    def __init__(self):
        self.should_fail_publish = False

    def publish_post(
        self,
        access_token: str,
        author_urn: str,
        text: str,
        visibility: str = "PUBLIC",
        asset_urn: str | None = None,
    ) -> dict:
        if self.should_fail_publish:
            raise RuntimeError("LinkedIn publish failed")
        return {"id": "ugc-post-1", "asset_urn": asset_urn}


def create_in_memory_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def create_approved_topic(session, text="A ready LinkedIn post."):
    topic = Topic(
        topic=f"Retry backoff - {text}",
        category=Category.AI,
        priority=Priority.HIGH,
        status=TopicStatus.APPROVED,
        generated_post=text,
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def test_retry_backoff_sets_scheduled_for():
    # use a small retry delay for test speed
    settings.PUBLISH_RETRY_DELAY_SECONDS = 2
    # ensure token secret is configured for TokenService
    settings.LINKEDIN_TOKEN_SECRET = "test-token-secret"

    session = create_in_memory_session()
    client = FakeLinkedInClient()
    client.should_fail_publish = True
    service = PublishService(session, client=client)

    account = service.create_account("mock_person_id", "mock_access", "mock_refresh")
    topic = create_approved_topic(session)
    item = service.enqueue_topic(topic.id, account.id, max_attempts=2)

    try:
        service.process_queue_item(item.id)
    except RuntimeError:
        pass

    refreshed = service.queue_repo.get_by_id(item.id)
    assert refreshed.status == "RETRY"
    assert refreshed.attempts == 1
    assert refreshed.last_error == "LinkedIn publish failed"
    assert refreshed.scheduled_for is not None

    expected = datetime.now(timezone.utc) + timedelta(seconds=settings.PUBLISH_RETRY_DELAY_SECONDS)
    # normalize scheduled_for to aware UTC if DB returned naive
    sched = refreshed.scheduled_for
    if sched.tzinfo is None:
        sched = sched.replace(tzinfo=timezone.utc)
    # allow a small delta
    delta = abs((sched - expected).total_seconds())
    assert delta < 5
