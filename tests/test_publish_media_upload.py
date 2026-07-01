from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database import Base
import app.db.models  # noqa: F401
from app.db.models.topic import Topic
from app.models.topic import Category, Priority, TopicStatus
from app.repositories.topic_repository import TopicRepository
from app.services.publish_service import PublishService


class FakeLinkedInClient:
    def __init__(self):
        self.registered_asset = None
        self.uploaded_asset = None
        self.published_asset = None

    def register_image_upload(self, access_token: str, author_urn: str, mime_type: str) -> dict:
        self.registered_asset = {
            "asset_urn": "urn:li:digitalmediaAsset:C4D00AAAAbBCDEFG",
            "upload_url": "https://media-upload.linkedin.com/mock-upload-url",
        }
        return self.registered_asset

    def upload_image(self, upload_url: str, image_bytes: bytes, mime_type: str) -> dict:
        self.uploaded_asset = {
            "upload_url": upload_url,
            "bytes": len(image_bytes),
            "mime_type": mime_type,
        }
        return {"status": 201}

    def publish_post(
        self,
        access_token: str,
        author_urn: str,
        text: str,
        visibility: str = "PUBLIC",
        asset_urn: str | None = None,
    ) -> dict:
        self.published_asset = asset_urn
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


def create_approved_topic(session, text="A ready LinkedIn post."):
    topic = Topic(
        topic=f"Media publish test - {text}",
        category=Category.AI,
        priority=Priority.HIGH,
        status=TopicStatus.APPROVED,
        generated_post=text,
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def test_attach_media_to_topic_downloads_uploads_and_saves_asset(monkeypatch):
    settings.LINKEDIN_TOKEN_SECRET = "test-token-secret"
    session = create_in_memory_session()
    client = FakeLinkedInClient()
    service = PublishService(session, client=client)

    account = service.create_account("mock_person_id", "mock_access", "mock_refresh")
    topic = create_approved_topic(session)

    class DummyResponse:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = b"PNGDATA"

        def raise_for_status(self):
            return None

    monkeypatch.setattr("app.services.publish_service.httpx.get", lambda url, timeout: DummyResponse())

    result = service.attach_media_to_topic(topic.id, "https://example.com/image.png")

    assert result["success"] is True
    assert result["asset_urn"] == "urn:li:digitalmediaAsset:C4D00AAAAbBCDEFG"

    refreshed_topic = TopicRepository(session).get_by_id(topic.id)
    assert refreshed_topic.media_asset_urn == "urn:li:digitalmediaAsset:C4D00AAAAbBCDEFG"
    assert refreshed_topic.media_mime_type == "image/png"
    assert client.uploaded_asset["mime_type"] == "image/png"


def test_publish_topic_now_includes_media_asset_urn():
    settings.LINKEDIN_TOKEN_SECRET = "test-token-secret"
    session = create_in_memory_session()
    client = FakeLinkedInClient()
    service = PublishService(session, client=client)

    account = service.create_account("mock_person_id", "mock_access", "mock_refresh")
    topic = create_approved_topic(session)
    topic.media_asset_urn = "urn:li:digitalmediaAsset:C4D00AAAAbBCDEFG"
    session.commit()

    response = service.publish_topic_now(topic.id)

    assert response["success"] is True
    assert client.published_asset == "urn:li:digitalmediaAsset:C4D00AAAAbBCDEFG"
    refreshed_topic = TopicRepository(session).get_by_id(topic.id)
    assert refreshed_topic.status == TopicStatus.PUBLISHED
