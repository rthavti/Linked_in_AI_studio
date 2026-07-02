from unittest.mock import patch
import re

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
    assert "This is a generated LinkedIn post." in refreshed_topic.generated_post
    assert "#ai" in refreshed_topic.generated_post.lower()

    history_entries = service.history_repository.get_by_topic(topic.id)
    assert len(history_entries) == 1
    assert "This is a generated LinkedIn post." in history_entries[0].generated_post
    assert history_entries[0].status == TopicStatus.READY_FOR_REVIEW


def test_generate_for_topic_adds_inline_and_trailing_hashtags():
    session = create_in_memory_session()
    repository = TopicRepository(session)

    topic = Topic(
        topic="CI/CD deployment workflow automation",
        category=Category.DEVOPS,
        priority=Priority.HIGH,
        status=TopicStatus.NEW,
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)

    with patch("app.services.generation_service.OpenAIClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.generate_post.return_value = {
            "content": (
                "We redesigned the pipeline for better reliability.\n"
                "Every commit triggered automated builds and tests.\n"
                "Deployments became predictable and secure."
            ),
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }

        service = GenerationService(repository, session)
        success = service.generate_for_topic(topic)

    assert success is True

    refreshed_topic = repository.get_by_id(topic.id)
    assert refreshed_topic is not None
    generated = refreshed_topic.generated_post or ""

    inline_matches = re.findall(r"(?i)#(?:pipeline|automated|deployment|devops|security)", generated)
    assert len(inline_matches) >= 2

    trailing_line = generated.strip().splitlines()[-1]
    trailing_hashtags = re.findall(r"#[A-Za-z0-9_]+", trailing_line)
    assert len(trailing_hashtags) >= 4


def test_enforce_engagement_signature_adds_distinct_structure_per_type():
    base_text = "Teams need a practical way to execute better without overcomplicating workflows."

    discussion = GenerationService._enforce_engagement_signature(base_text, "discussion_starter", "AI")
    assert "?" in discussion.splitlines()[0]

    playbook = GenerationService._enforce_engagement_signature(base_text, "how_to_playbook", "AI")
    assert "1." in playbook
    assert "2." in playbook
    assert "3." in playbook

    trend = GenerationService._enforce_engagement_signature(base_text, "trend_radar", "AI")
    assert "Trend 1:" in trend
    assert "Trend 2:" in trend
    assert "Trend 3:" in trend

    case_study = GenerationService._enforce_engagement_signature(base_text, "case_study_breakdown", "AI")
    assert "Context:" in case_study
    assert "Action:" in case_study
    assert "Result:" in case_study
    assert "Lesson:" in case_study

    cta_dm = GenerationService._enforce_engagement_signature(base_text, "cta_to_dm", "AI")
    assert "DM" in cta_dm


def test_generate_for_topic_optionally_generates_and_attaches_images():
    session = create_in_memory_session()
    repository = TopicRepository(session)

    topic = Topic(
        topic="Image option topic",
        category=Category.AI,
        priority=Priority.MEDIUM,
        status=TopicStatus.NEW,
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)

    with patch("app.services.generation_service.OpenAIClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.generate_post.return_value = {
            "content": "Generated post with optional images.",
            "prompt_tokens": 12,
            "completion_tokens": 18,
            "total_tokens": 30,
        }

        with patch("app.services.generation_service.PublishService") as MockPublishService:
            mock_publish_service = MockPublishService.return_value

            service = GenerationService(repository, session)
            with patch.object(
                GenerationService,
                "_save_images",
                return_value=[
                    "http://127.0.0.1:8000/static/generated/topic-1-a.png",
                    "http://127.0.0.1:8000/static/generated/topic-1-b.png",
                ],
            ):
                success = service.generate_for_topic(
                    topic,
                    generate_images=True,
                    image_count=2,
                )

    assert success is True
    assert mock_publish_service.attach_media_to_topic.call_count == 2
