from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.publish_queue import PublishQueue


class PublishQueueRepository:

    def __init__(self, db: Session):
        self._db = db

    def create(
        self,
        topic_id: int,
        linkedin_account_id: int | None = None,
        scheduled_for: datetime | None = None,
        max_attempts: int = 3,
    ) -> PublishQueue:
        item = PublishQueue(
            topic_id=topic_id,
            linkedin_account_id=linkedin_account_id,
            scheduled_for=scheduled_for or datetime.utcnow(),
            max_attempts=max_attempts,
            status="PENDING",
        )
        self._db.add(item)
        self._db.commit()
        self._db.refresh(item)
        return item

    def get_by_id(self, queue_id: int) -> PublishQueue | None:
        return (
            self._db.query(PublishQueue)
            .filter(PublishQueue.id == queue_id)
            .first()
        )

    def get_all(self) -> list[PublishQueue]:
        return (
            self._db.query(PublishQueue)
            .order_by(PublishQueue.created_at.desc())
            .all()
        )

    def get_ready(self, now: datetime, limit: int = 10) -> list[PublishQueue]:
        return (
            self._db.query(PublishQueue)
            .filter(PublishQueue.status.in_(["PENDING", "RETRY"]))
            .filter(PublishQueue.scheduled_for <= now)
            .order_by(PublishQueue.scheduled_for.asc())
            .limit(limit)
            .all()
        )

    def update(self, item: PublishQueue) -> PublishQueue:
        self._db.commit()
        self._db.refresh(item)
        return item
