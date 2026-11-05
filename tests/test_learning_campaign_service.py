from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.db.models  # noqa: F401
from app.db.models.learning_campaign import LearningCampaign
from app.db.models.learning_campaign_item import LearningCampaignItem
from app.models.topic import Category
from app.models.topic import Priority
from app.models.topic import TopicStatus
from app.repositories.learning_campaign_repository import LearningCampaignRepository
from app.services.learning_campaign_service import LearningCampaignService


def create_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def test_failed_day_does_not_pause_campaign(monkeypatch):
    session = create_session()
    service = LearningCampaignService(session)

    campaign = LearningCampaign(
        name="FDE learning series",
        status="ACTIVE",
        timezone="Asia/Kolkata",
        publish_time="09:00",
        start_date="2026-07-01",
        auto_approve=True,
        auto_publish=True,
        auto_generate_images=False,
        image_count=1,
        visual_style="auto",
        max_attempts=3,
        min_words=120,
        max_words=320,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    item = LearningCampaignItem(
        campaign_id=campaign.id,
        day_number=6,
        topic="Day 6",
        category=Category.AI,
        priority=Priority.MEDIUM,
        status="RETRY",
        attempts=2,
        scheduled_for=datetime.utcnow() - timedelta(minutes=1),
        last_error="Previous failure",
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    def fail_generate_for_topic(*args, **kwargs):
        raise RuntimeError("Content generation failed for campaign item.")

    monkeypatch.setattr(service.generation_service, "generate_for_topic", fail_generate_for_topic)
    monkeypatch.setattr(service.publish_service, "publish_topic_now", lambda *args, **kwargs: None)

    service._process_item(item)

    refreshed_campaign = session.query(LearningCampaign).filter(LearningCampaign.id == campaign.id).first()
    refreshed_item = session.query(LearningCampaignItem).filter(LearningCampaignItem.id == item.id).first()

    assert refreshed_item.status == "FAILED"
    assert refreshed_item.attempts == 3
    assert refreshed_campaign.status == "ACTIVE"
    assert "failed after 3 attempts" in (refreshed_campaign.last_error or "").lower()


def test_process_due_items_skips_blocked_items_and_processes_other_campaign(monkeypatch):
    session = create_session()
    service = LearningCampaignService(session)
    repo = LearningCampaignRepository(session)

    fde_campaign = LearningCampaign(
        name="FDE learning series",
        status="ACTIVE",
        timezone="Asia/Kolkata",
        publish_time="09:00",
        start_date="2026-07-01",
        auto_approve=True,
        auto_publish=True,
        auto_generate_images=False,
        image_count=1,
        visual_style="auto",
        max_attempts=3,
        min_words=120,
        max_words=320,
    )
    other_campaign = LearningCampaign(
        name="New AI engagement series",
        status="ACTIVE",
        timezone="Asia/Kolkata",
        publish_time="16:00",
        start_date="2026-07-01",
        auto_approve=True,
        auto_publish=True,
        auto_generate_images=False,
        image_count=1,
        visual_style="auto",
        max_attempts=3,
        min_words=120,
        max_words=320,
    )
    session.add_all([fde_campaign, other_campaign])
    session.commit()
    session.refresh(fde_campaign)
    session.refresh(other_campaign)

    blocked_previous = LearningCampaignItem(
        campaign_id=other_campaign.id,
        day_number=2,
        topic="Other Day 2",
        category=Category.AI,
        priority=Priority.MEDIUM,
        status="PROCESSING",
        attempts=0,
        scheduled_for=datetime.utcnow() - timedelta(days=20),
    )
    blocked_due = LearningCampaignItem(
        campaign_id=other_campaign.id,
        day_number=3,
        topic="Other Day 3",
        category=Category.AI,
        priority=Priority.MEDIUM,
        status="PENDING",
        attempts=0,
        scheduled_for=datetime.utcnow() - timedelta(days=19),
    )
    fde_due = LearningCampaignItem(
        campaign_id=fde_campaign.id,
        day_number=8,
        topic="FDE Day 8",
        category=Category.AI,
        priority=Priority.MEDIUM,
        status="PENDING",
        attempts=0,
        scheduled_for=datetime.utcnow() - timedelta(days=10),
    )
    session.add_all([blocked_previous, blocked_due, fde_due])
    session.commit()
    session.refresh(blocked_previous)
    session.refresh(blocked_due)
    session.refresh(fde_due)

    def fake_process(item):
        if item.id == blocked_due.id:
            raise AssertionError("Blocked item should be skipped.")
        item.status = "PUBLISHED"
        repo.update_item(item)

    monkeypatch.setattr(service, "_process_item", fake_process)

    processed = service.process_due_items(limit=1)

    refreshed_blocked_due = repo.get_item(blocked_due.id)
    refreshed_fde_due = repo.get_item(fde_due.id)

    assert processed == 1
    assert refreshed_blocked_due.status == "PENDING"
    assert refreshed_fde_due.status == "PUBLISHED"
