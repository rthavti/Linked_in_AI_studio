from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from app.database import Base


class Topic(Base):

    __tablename__ = "topics"

    id = Column(Integer, primary_key=True)

    title = Column(String(500), nullable=False)

    status = Column(String(50), default="PENDING")

    image_path = Column(String(500))

    post_url = Column(String(1000))

    processed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())