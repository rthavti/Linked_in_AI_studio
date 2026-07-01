from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database import Base
import app.db.models  # noqa: F401
from app.db.models.topic import Topic
from app.models.topic import Category
from app.models.topic import Priority
from app.models.topic import TopicStatus
from app.repositories.linkedin_account_repository import LinkedInAccountRepository
from app.repositories.publish_history_repository import PublishHistoryRepository
from app.repositories.topic_repository import TopicRepository
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
        asset_urn: str | None = None,
    ) -> dict:
        if self.should_fail_publish:
            raise RuntimeError("LinkedIn publish failed")
        return {
            "id": "ugc-post-1",
            "author": author_urn,
            "text": text,
            "asset_urn": asset_urn,
        }


def create_in_memory_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def configure_token_secret():
    settings.LINKEDIN_TOKEN_SECRET = "test-token-secret"


def create_approved_topic(session):
    topic = Topic(
        topic="Publish this LinkedIn post",
        category=Category.AI,
        priority=Priority.HIGH,
        status=TopicStatus.APPROVED,
        generated_post="A ready LinkedIn post.",
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def test_create_or_update_linkedin_account_encrypts_tokens():
    configure_token_secret()
    session = create_in_memory_session()
    service = PublishService(session, client=FakeLinkedInClient())

    account = service.create_account(
        "urn:li:person:123",
        "token123",
        "refresh123",
        None,
    )

    assert account is not None
    assert account.provider_user_id == "urn:li:person:123"
    assert account.access_token != "token123"
    assert account.refresh_token != "refresh123"
    assert TokenService.decrypt(account.access_token) == "token123"
    assert TokenService.decrypt(account.refresh_token) == "refresh123"

    fetched = LinkedInAccountRepository(session).get_by_id(account.id)
    assert fetched is not None
    assert fetched.provider_user_id == "urn:li:person:123"


def test_handle_callback_validates_state_and_persists_account():
    configure_token_secret()
    session = create_in_memory_session()
    service = PublishService(session, client=FakeLinkedInClient())

    oauth = service.start_oauth()
    result = service.handle_callback("fake_code", oauth["state"])

    assert result["account_id"] is not None

    account = service.account_repo.get_by_id(result["account_id"])
    assert account is not None
    assert account.provider_user_id == "mock_person_id"
    assert TokenService.decrypt(account.access_token) == "mock_access"
    assert TokenService.decrypt(account.refresh_token) == "mock_refresh"
    assert account.expires_at is not None


def test_publish_topic_now_uses_latest_account_and_marks_published():
    configure_token_secret()
    session = create_in_memory_session()
    client = FakeLinkedInClient()
    service = PublishService(session, client=client)
    topic = create_approved_topic(session)
    service.create_account("mock_person_id", "mock_access", "mock_refresh")

    result = service.publish_topic_now(topic.id)

    assert result["success"] is True
    refreshed_topic = TopicRepository(session).get_by_id(topic.id)
    assert refreshed_topic.status == TopicStatus.PUBLISHED

    history = PublishHistoryRepository(session).get_by_topic(topic.id)
    assert len(history) == 1
    assert history[0].status == "PUBLISHED"
    assert history[0].published_at is not None


def test_publish_queue_retries_failed_publish():
    configure_token_secret()
    session = create_in_memory_session()
    client = FakeLinkedInClient()
    client.should_fail_publish = True
    service = PublishService(session, client=client)
    topic = create_approved_topic(session)
    account = service.create_account("mock_person_id", "mock_access", "mock_refresh")
    item = service.enqueue_topic(topic.id, account.id, max_attempts=2)

    try:
        service.process_queue_item(item.id)
    except RuntimeError:
        pass

    refreshed = service.queue_repo.get_by_id(item.id)
    assert refreshed.status == "RETRY"
    assert refreshed.attempts == 1
    assert refreshed.last_error == "LinkedIn publish failed"
