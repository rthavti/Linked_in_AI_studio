from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import TIMESTAMP
from sqlalchemy import func

from app.database import Base


class EngagementCommentHistory(Base):
    __tablename__ = "engagement_comment_histories"

    id = Column(Integer, primary_key=True, index=True)

    post_url = Column(String(1200), nullable=False, index=True)
    post_urn = Column(String(255), nullable=True, index=True)
    post_author = Column(String(255), nullable=True, index=True)
    post_language = Column(String(32), nullable=True)
    post_content = Column(Text, nullable=False)
    post_published_at = Column(TIMESTAMP, nullable=True)
    post_reaction_count = Column(Integer, nullable=False, default=0)

    topic = Column(String(100), nullable=False, index=True)
    style = Column(String(40), nullable=False, default="professional")
    relevance_score = Column(Integer, nullable=False, default=0)

    generated_comment = Column(Text, nullable=True)
    posted_comment = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="REVIEW_PENDING", index=True)
    skip_reason = Column(Text, nullable=True)

    is_company_page = Column(Boolean, nullable=False, default=False)
    is_sponsored = Column(Boolean, nullable=False, default=False)
    is_recruiter = Column(Boolean, nullable=False, default=False)
    is_repost = Column(Boolean, nullable=False, default=False)

    linkedin_comment_id = Column(String(255), nullable=True)
    posted_at = Column(TIMESTAMP, nullable=True)

    likes_received = Column(Integer, nullable=False, default=0)
    replies_received = Column(Integer, nullable=False, default=0)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<EngagementCommentHistory(id={self.id}, topic={self.topic}, status={self.status})>"
        )
