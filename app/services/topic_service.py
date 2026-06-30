"""
Topic Service
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.topic import Topic
from app.models.topic import TopicStatus
from app.repositories.topic_repository import TopicRepository


class TopicService:

    def __init__(self, db: Session):

        self.repository = TopicRepository(db)

    def create_topic(self, topic: Topic) -> Topic:
        return self.repository.insert(topic)

    def update_topic(self, topic: Topic) -> Topic:
        return self.repository.update(topic)

    def delete_topic(self, topic_id: int) -> bool:
        return self.repository.delete(topic_id)

    def get_topic(self, topic_id: int) -> Optional[Topic]:
        return self.repository.get_by_id(topic_id)

    def get_all_topics(self) -> List[Topic]:
        return self.repository.get_all()

    def get_topics_by_status(
        self,
        status: TopicStatus,
    ) -> List[Topic]:
        return self.repository.find_by_status(status)

    def get_next_pending(self):
        return self.repository.get_next_pending()

    def count_topics(self):
        return self.repository.count()