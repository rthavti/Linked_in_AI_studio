from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database import Base


class LinkedInAccount(Base):
    __tablename__ = "linkedin_accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    provider_user_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    access_token = Column(
        Text,
        nullable=False,
    )

    refresh_token = Column(
        Text,
        nullable=True,
    )

    expires_at = Column(
        TIMESTAMP,
        nullable=True,
    )

    disconnected_at = Column(
        TIMESTAMP,
        nullable=True,
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    publish_histories = relationship(
        "PublishHistory",
        back_populates="linkedin_account",
    )

    def __repr__(self) -> str:
        return f"<LinkedInAccount(id={self.id}, provider_user_id={self.provider_user_id})>"
