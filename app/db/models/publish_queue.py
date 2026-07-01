from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database import Base


class PublishQueue(Base):
    __tablename__ = "publish_queue"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    topic_id = Column(
        Integer,
        ForeignKey("topics.id"),
        nullable=False,
        index=True,
    )

    linkedin_account_id = Column(
        Integer,
        ForeignKey("linkedin_accounts.id"),
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
    )

    attempts = Column(
        Integer,
        nullable=False,
        default=0,
    )

    max_attempts = Column(
        Integer,
        nullable=False,
        default=3,
    )

    last_error = Column(
        Text,
        nullable=True,
    )

    scheduled_for = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    published_at = Column(
        TIMESTAMP,
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

    topic = relationship("Topic")
    linkedin_account = relationship("LinkedInAccount")
