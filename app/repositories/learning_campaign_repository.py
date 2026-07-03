from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.learning_campaign import LearningCampaign
from app.db.models.learning_campaign_item import LearningCampaignItem


class LearningCampaignRepository:
    def __init__(self, db: Session):
        self._db = db

    def create_campaign(self, campaign: LearningCampaign) -> LearningCampaign:
        self._db.add(campaign)
        self._db.commit()
        self._db.refresh(campaign)
        return campaign

    def update_campaign(self, campaign: LearningCampaign) -> LearningCampaign:
        self._db.commit()
        self._db.refresh(campaign)
        return campaign

    def get_campaign(self, campaign_id: int) -> LearningCampaign | None:
        return self._db.query(LearningCampaign).filter(LearningCampaign.id == campaign_id).first()

    def get_campaign_by_name(self, name: str) -> LearningCampaign | None:
        return self._db.query(LearningCampaign).filter(LearningCampaign.name == name).first()

    def list_campaigns(self) -> list[LearningCampaign]:
        return self._db.query(LearningCampaign).order_by(LearningCampaign.created_at.desc()).all()

    def create_items(self, items: list[LearningCampaignItem]) -> None:
        self._db.add_all(items)
        self._db.commit()

    def list_items_for_campaign(self, campaign_id: int) -> list[LearningCampaignItem]:
        return (
            self._db.query(LearningCampaignItem)
            .filter(LearningCampaignItem.campaign_id == campaign_id)
            .order_by(LearningCampaignItem.day_number.asc())
            .all()
        )

    def get_item(self, item_id: int) -> LearningCampaignItem | None:
        return self._db.query(LearningCampaignItem).filter(LearningCampaignItem.id == item_id).first()

    def update_item(self, item: LearningCampaignItem) -> LearningCampaignItem:
        self._db.commit()
        self._db.refresh(item)
        return item

    def get_due_items(self, now_utc: datetime, limit: int = 5) -> list[LearningCampaignItem]:
        return (
            self._db.query(LearningCampaignItem)
            .join(LearningCampaign, LearningCampaign.id == LearningCampaignItem.campaign_id)
            .filter(LearningCampaign.status == "ACTIVE")
            .filter(LearningCampaignItem.status.in_(["PENDING", "RETRY"]))
            .filter(LearningCampaignItem.scheduled_for <= now_utc)
            .order_by(LearningCampaignItem.scheduled_for.asc(), LearningCampaignItem.day_number.asc())
            .limit(limit)
            .all()
        )

    def has_unpublished_previous(self, campaign_id: int, day_number: int) -> bool:
        if day_number <= 1:
            return False
        previous = (
            self._db.query(LearningCampaignItem)
            .filter(LearningCampaignItem.campaign_id == campaign_id)
            .filter(LearningCampaignItem.day_number < day_number)
            .filter(LearningCampaignItem.status != "PUBLISHED")
            .first()
        )
        return previous is not None
