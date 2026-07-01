from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.publish_history import PublishHistory


class PublishHistoryRepository:

    def __init__(self, db: Session):
        self._db = db

    def create(
        self,
        topic_id: int,
        linkedin_account_id: int | None,
        status: str,
        response: str | None = None,
        error_message: str | None = None,
        published_at: datetime | None = None,
    ):
        history = PublishHistory(
            topic_id=topic_id,
            linkedin_account_id=linkedin_account_id,
            status=status,
            response=response,
            error_message=error_message,
            published_at=published_at,
        )
        self._db.add(history)
        self._db.commit()
        self._db.refresh(history)
        return history

    def get_by_id(self, history_id: int):
        return self._db.query(PublishHistory).filter(PublishHistory.id == history_id).first()

    def get_by_topic(self, topic_id: int):
        return (
            self._db.query(PublishHistory)
            .filter(PublishHistory.topic_id == topic_id)
            .order_by(PublishHistory.created_at.desc())
            .all()
        )

    def get_all(self):
        return self._db.query(PublishHistory).order_by(PublishHistory.created_at.desc()).all()
