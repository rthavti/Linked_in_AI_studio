from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.topic import Category
from app.models.topic import Priority


class LearningCampaignItem(Base):
    __tablename__ = "learning_campaign_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    campaign_id = Column(
        Integer,
        ForeignKey("learning_campaigns.id"),
        nullable=False,
        index=True,
    )

    day_number = Column(
        Integer,
        nullable=False,
        index=True,
    )

    topic = Column(
        String(500),
        nullable=False,
    )

    prompt_brief = Column(
        Text,
        nullable=True,
    )

    visual_hint = Column(
        Text,
        nullable=True,
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
        String(32),
        nullable=False,
        default="PENDING",
        index=True,
    )

    scheduled_for = Column(
        TIMESTAMP,
        nullable=False,
        index=True,
    )

    attempts = Column(
        Integer,
        nullable=False,
        default=0,
    )

    topic_id = Column(
        Integer,
        ForeignKey("topics.id"),
        nullable=True,
        index=True,
    )

    published_at = Column(
        TIMESTAMP,
        nullable=True,
    )

    last_error = Column(
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

    campaign = relationship("LearningCampaign", back_populates="items")
    topic_ref = relationship("Topic")
