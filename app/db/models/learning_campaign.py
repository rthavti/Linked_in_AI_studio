from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database import Base


class LearningCampaign(Base):
    __tablename__ = "learning_campaigns"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(32),
        nullable=False,
        default="ACTIVE",
        index=True,
    )

    timezone = Column(
        String(80),
        nullable=False,
        default="Asia/Kolkata",
    )

    publish_time = Column(
        String(5),
        nullable=False,
        default="09:00",
    )

    start_date = Column(
        String(10),
        nullable=False,
    )

    auto_approve = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    auto_publish = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    auto_generate_images = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    image_count = Column(
        Integer,
        nullable=False,
        default=1,
    )

    visual_style = Column(
        String(40),
        nullable=False,
        default="auto",
    )

    max_attempts = Column(
        Integer,
        nullable=False,
        default=3,
    )

    min_words = Column(
        Integer,
        nullable=False,
        default=120,
    )

    max_words = Column(
        Integer,
        nullable=False,
        default=320,
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

    items = relationship(
        "LearningCampaignItem",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="LearningCampaignItem.day_number",
    )
