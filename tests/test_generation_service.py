from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.db.models  # noqa: F401
from app.db.models.topic import Topic
from app.models.topic import Category
from app.models.topic import Priority
from app.models.topic import TopicStatus
from app.repositories.topic_repository import TopicRepository
from app.services.generation_service import GenerationService


def create_in_memory_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def test_generate_for_topic_persists_generated_post_and_history():
    session = create_in_memory_session()
    repository = TopicRepository(session)

    topic = Topic(
        topic="Test LinkedIn Topic",
        category=Category.AI,
        priority=Priority.HIGH,
        status=TopicStatus.NEW,
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)

    with patch("app.services.generation_service.OpenAIClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.generate_post.return_value = {
            "content": "This is a generated LinkedIn post.",
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }

        service = GenerationService(repository, session)
        success = service.generate_for_topic(topic)

    assert success is True

    refreshed_topic = repository.get_by_id(topic.id)
    assert refreshed_topic is not None
    assert refreshed_topic.status == TopicStatus.READY_FOR_REVIEW
    assert refreshed_topic.generated_post == "This is a generated LinkedIn post."

    history_entries = service.history_repository.get_by_topic(topic.id)
    assert len(history_entries) == 1
    assert history_entries[0].generated_post == "This is a generated LinkedIn post."
    assert history_entries[0].status == TopicStatus.READY_FOR_REVIEW
