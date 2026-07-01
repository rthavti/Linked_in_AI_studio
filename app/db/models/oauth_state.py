from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy import func

from app.database import Base


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    state = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    used = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    expires_at = Column(
        TIMESTAMP,
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )
