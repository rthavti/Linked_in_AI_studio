"""
Generation History Model

Tracks every AI generation attempt and metadata for a topic.
"""

from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database import Base


class GenerationHistory(Base):
    __tablename__ = "generation_histories"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    topic_id = Column(
        Integer,
        ForeignKey("topics.id"),
        nullable=False,
    )

    version = Column(
        Integer,
        nullable=False,
    )

    prompt_template = Column(
        String(100),
        nullable=False,
    )

    prompt_version = Column(
        String(100),
        nullable=False,
    )

    model = Column(
        String(100),
        nullable=False,
    )

    temperature = Column(
        Float,
        nullable=False,
    )

    max_tokens = Column(
        Integer,
        nullable=False,
    )

    prompt_tokens = Column(
        Integer,
        nullable=True,
    )

    completion_tokens = Column(
        Integer,
        nullable=True,
    )

    total_tokens = Column(
        Integer,
        nullable=True,
    )

    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    latency_ms = Column(
        Integer,
        nullable=True,
    )

    generated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    generated_post = Column(
        Text,
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
    )

    topic = relationship(
        "Topic",
        back_populates="generation_histories",
    )
