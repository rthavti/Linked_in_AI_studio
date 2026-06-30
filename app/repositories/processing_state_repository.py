"""
Processing State Repository

Repository layer for ProcessingState persistence using SQLAlchemy.

Author: LinkedIn AI Studio
"""

from typing import List

from sqlalchemy.orm import Session

from app.db.models.processing_state import ProcessingState


class ProcessingStateRepository:
    """
    Repository responsible for all ProcessingState database operations.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def add_processing_step(self, processing_state: ProcessingState) -> None:
        """
        Record a completed workflow step.
        """
        self._db.add(processing_state)
        self._db.commit()

    def get_processing_history(self, topic_id: int) -> List[ProcessingState]:
        """
        Return processing history for a topic.
        """
        return self._db.query(ProcessingState).filter(ProcessingState.topic_id == topic_id).order_by(ProcessingState.timestamp).all()