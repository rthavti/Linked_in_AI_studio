"""
Topic Repository

Author: LinkedIn AI Studio
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.topic import Topic
from app.models.topic import Category
from app.models.topic import Priority
from app.models.topic import TopicStatus


class TopicRepository:
    """
    Repository responsible for all Topic database operations.
    """

    def __init__(self, db: Session):
        self._db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def insert(self, topic: Topic) -> Topic:
        """
        Insert a Topic object and commit immediately.
        """

        self._db.add(topic)
        self._db.commit()
        self._db.refresh(topic)

        return topic

    def create(
        self,
        topic_text: str,
        category: Category,
        priority: Priority,
    ) -> Topic:
        """
        Create a new Topic.

        NOTE:
        This method intentionally DOES NOT COMMIT.
        It is used by bulk import workflows.
        """

        topic = Topic(
            topic=topic_text,
            category=category,
            priority=priority,
            status=TopicStatus.NEW,
        )

        self._db.add(topic)

        return topic

    def update(self, topic: Topic) -> Topic:

        self._db.commit()
        self._db.refresh(topic)

        return topic

    def delete(self, topic_id: int) -> bool:

        topic = self.get_by_id(topic_id)

        if topic is None:
            return False

        self._db.delete(topic)
        self._db.commit()

        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_id(
        self,
        topic_id: int,
    ) -> Optional[Topic]:

        return (
            self._db.query(Topic)
            .filter(Topic.id == topic_id)
            .first()
        )

    def get_by_topic(
        self,
        topic_text: str,
    ) -> Optional[Topic]:

        return (
            self._db.query(Topic)
            .filter(Topic.topic == topic_text)
            .first()
        )

    def get_all(self) -> List[Topic]:

        return (
            self._db.query(Topic)
            .order_by(Topic.created_at.desc())
            .all()
        )

    def count(self) -> int:

        return self._db.query(Topic).count()

    def find_by_status(
        self,
        status: TopicStatus,
    ) -> List[Topic]:

        return (
            self._db.query(Topic)
            .filter(Topic.status == status)
            .order_by(Topic.created_at.asc())
            .all()
        )

    # ------------------------------------------------------------------
    # Workflow Methods
    # ------------------------------------------------------------------

    def get_next_pending(self) -> Optional[Topic]:
        """
        Returns the oldest topic waiting for generation.
        """

        return (
            self._db.query(Topic)
            .filter(Topic.status == TopicStatus.NEW)
            .order_by(Topic.created_at.asc())
            .first()
        )

    def update_generated_post(
        self,
        topic_id: int,
        status: TopicStatus,
        generated_post: str | None = None,
    ) -> bool:
        """
        Update topic status and optionally store the generated post.
        """

        topic = self.get_by_id(topic_id)

        if topic is None:
            return False

        topic.status = status

        if generated_post is not None:
            generated_post = generated_post.strip()
            topic.generated_post = generated_post or None
            if topic.generated_post is not None:
                topic.error_message = None

        self._db.commit()
        self._db.refresh(topic)

        return True

    def mark_processing(
        self,
        topic_id: int,
    ) -> bool:

        topic = self.get_by_id(topic_id)

        if topic is None:
            return False

        topic.status = TopicStatus.PROCESSING

        self._db.commit()

        return True

    def mark_failed(
        self,
        topic_id: int,
        error_message: str,
    ) -> bool:

        topic = self.get_by_id(topic_id)

        if topic is None:
            return False

        topic.status = TopicStatus.FAILED
        topic.error_message = error_message

        self._db.commit()

        return True

    def approve(
        self,
        topic_id: int,
    ) -> bool:

        topic = self.get_by_id(topic_id)

        if topic is None:
            return False

        topic.status = TopicStatus.APPROVED
        topic.error_message = None

        self._db.commit()

        return True

    def reject(
        self,
        topic_id: int,
        rejection_reason: str | None = None,
    ) -> bool:

        topic = self.get_by_id(topic_id)

        if topic is None:
            return False

        topic.status = TopicStatus.NEW
        topic.error_message = rejection_reason or "Rejected by reviewer."
        topic.generated_post = None

        self._db.commit()

        return True

    # ------------------------------------------------------------------
    # Bulk Operations
    # ------------------------------------------------------------------

    def commit(self) -> None:
        """
        Commit current transaction.
        """

        self._db.commit()

    def rollback(self) -> None:
        """
        Roll back current transaction.
        """

        self._db.rollback()

    def refresh(
        self,
        topic: Topic,
    ) -> None:

        self._db.refresh(topic)