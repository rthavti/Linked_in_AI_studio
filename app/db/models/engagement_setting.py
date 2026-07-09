from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func

from app.database import Base


class EngagementSetting(Base):
    __tablename__ = "engagement_settings"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, nullable=False, default=False)
    require_review = Column(Boolean, nullable=False, default=True)
    auto_post_enabled = Column(Boolean, nullable=False, default=False)

    posts_to_search_per_day = Column(Integer, nullable=False, default=30)
    comments_per_day = Column(Integer, nullable=False, default=5)
    min_reactions = Column(Integer, nullable=False, default=50)
    author_cooldown_hours = Column(Integer, nullable=False, default=72)

    style = Column(String(40), nullable=False, default="professional")
    topics = Column(Text, nullable=False, default="")
    topic_configs_json = Column(Text, nullable=False, default="[]")
    blocked_keywords = Column(Text, nullable=False, default="")
    own_author_identifiers = Column(Text, nullable=False, default="")
    run_time = Column(String(5), nullable=False, default="09:30")

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<EngagementSetting(id={self.id}, enabled={self.enabled})>"
