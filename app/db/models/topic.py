"""
SQLAlchemy Topic Model

Author: LinkedIn AI Studio
"""

from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.topic import Category
from app.models.topic import Priority
from app.models.topic import TopicStatus


class Topic(Base):
    __tablename__ = "topics"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    topic = Column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
    )

    category = Column(
        Enum(Category),
        nullable=False,
    )

    priority = Column(
        Enum(Priority),
        nullable=False,
        default=Priority.MEDIUM,
    )

    status = Column(
        Enum(TopicStatus),
        nullable=False,
        default=TopicStatus.NEW,
    )

    generated_post = Column(
        Text,
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    processing_states = relationship(
        "ProcessingState",
        back_populates="topic",
        cascade="all, delete-orphan",
    )

    generation_histories = relationship(
        "GenerationHistory",
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="GenerationHistory.version",
    )

    @property
    def generation_history(self):
        return self.generation_histories

    def __repr__(self) -> str:
        return (
            f"<Topic(id={self.id}, "
            f"topic='{self.topic}', "
            f"status='{self.status}')>"
        )