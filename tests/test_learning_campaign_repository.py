from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.db.models  # noqa: F401
from app.db.models.learning_campaign import LearningCampaign
from app.db.models.learning_campaign_item import LearningCampaignItem
from app.models.topic import Category
from app.models.topic import Priority
from app.repositories.learning_campaign_repository import LearningCampaignRepository


def create_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


def test_failed_previous_item_does_not_block_later_items():
    session = create_session()
    repo = LearningCampaignRepository(session)

    campaign = LearningCampaign(
        name="FDE learning series",
        status="ACTIVE",
        timezone="Asia/Kolkata",
        publish_time="09:00",
        start_date="2026-07-01",
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    day_1 = LearningCampaignItem(
        campaign_id=campaign.id,
        day_number=1,
        topic="Day 1",
        category=Category.AI,
        priority=Priority.MEDIUM,
        status="FAILED",
        scheduled_for=datetime.utcnow() - timedelta(days=1),
    )
    day_2 = LearningCampaignItem(
        campaign_id=campaign.id,
        day_number=2,
        topic="Day 2",
        category=Category.AI,
        priority=Priority.MEDIUM,
        status="PENDING",
        scheduled_for=datetime.utcnow() - timedelta(minutes=5),
    )

    session.add_all([day_1, day_2])
    session.commit()

    assert repo.has_unpublished_previous(campaign.id, 2) is False
