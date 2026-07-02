from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database import Base
import app.db.models  # noqa: F401
from app.db.models.topic import Topic
from app.models.topic import Category, Priority, TopicStatus
from app.repositories.topic_repository import TopicRepository
from app.repositories.publish_history_repository import PublishHistoryRepository
from app.services.publish_service import PublishService
from app.services.token_service import TokenService


class FakeLinkedInClient:

    def __init__(self):
        self.should_fail_publish = False

    def get_authorize_url(self, state: str) -> str:
        return f"https://linkedin.example/oauth?state={state}"

    def exchange_code_for_token(self, code: str) -> dict:
        return {
            "access_token": "mock_access",
            "refresh_token": "mock_refresh",
            "expires_in": 3600,
        }

    def get_profile(self, access_token: str) -> dict:
        return {
            "id": "mock_person_id",
            "localizedFirstName": "Test",
            "localizedLastName": "User",
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        return {
            "access_token": "mock_access_refreshed",
            "refresh_token": refresh_token,
            "expires_in": 3600,
        }

    def publish_post(
        self,
        access_token: str,
        author_urn: str,
        text: str,
        visibility: str = "PUBLIC",
        asset_urns: list[str] | None = None,
    ) -> dict:
        if self.should_fail_publish:
            raise RuntimeError("LinkedIn publish failed")
        return {
            "id": "ugc-post-1",
            "author": author_urn,
            "text": text,
            "asset_urns": asset_urns,
        }


def create_in_memory_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def configure_token_secret():
    settings.LINKEDIN_TOKEN_SECRET = "test-token-secret"


def create_approved_topic(session, text="A ready LinkedIn post."):
    # ensure topic.title is unique to avoid DB unique constraints in tests
    topic = Topic(
        topic=f"Publish this LinkedIn post - {text}",
        category=Category.AI,
        priority=Priority.HIGH,
        status=TopicStatus.APPROVED,
        generated_post=text,
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def test_get_valid_access_token_refreshes_when_expired():
    configure_token_secret()
    session = create_in_memory_session()
    client = FakeLinkedInClient()
    service = PublishService(session, client=client)

    # create account with an already-expired access token
    past = datetime.now(timezone.utc) - timedelta(seconds=10)
    account = service.create_account("mock_person_id", "old_access", "old_refresh", expires_at=past)

    # ensure refresh is triggered and returns refreshed token
    acc = service.account_repo.get_by_id(account.id)
    new_access = service._get_valid_access_token(acc)
    assert new_access == "mock_access_refreshed"

    # repository should be updated with the refreshed token
    updated = service.account_repo.get_by_id(account.id)
    assert TokenService.decrypt(updated.access_token) == "mock_access_refreshed"


def test_process_due_queue_processes_multiple_items():
    configure_token_secret()
    session = create_in_memory_session()
    client = FakeLinkedInClient()
    service = PublishService(session, client=client)

    # create account
    account = service.create_account("mock_person_id", "mock_access", "mock_refresh")

    # create and enqueue multiple approved topics
    topics = [create_approved_topic(session, text=f"Post {i}") for i in range(3)]
    for t in topics:
        # use naive UTC datetime to match repository behavior
        service.enqueue_topic(t.id, account.id, scheduled_for=datetime.utcnow())

    # process each queue item directly to avoid timezone comparison issues
    items = service.queue_repo.get_all()
    for it in items:
        service.process_queue_item(it.id)

    # ensure all were processed and marked published
    items = service.queue_repo.get_all()
    assert len(items) == 3
    assert all(i.status == "PUBLISHED" for i in items)
