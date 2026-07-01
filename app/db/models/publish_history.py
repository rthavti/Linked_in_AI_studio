from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database import Base


class PublishHistory(Base):
    __tablename__ = "publish_histories"

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

    linkedin_account_id = Column(
        Integer,
        ForeignKey("linkedin_accounts.id"),
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
    )

    response = Column(
        Text,
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
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

    linkedin_account = relationship(
        "LinkedInAccount",
        back_populates="publish_histories",
    )

    def __repr__(self) -> str:
        return f"<PublishHistory(id={self.id}, topic_id={self.topic_id}, status={self.status})>"
