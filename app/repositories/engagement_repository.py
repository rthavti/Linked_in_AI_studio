from datetime import datetime
from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.engagement_comment_history import EngagementCommentHistory
from app.db.models.engagement_setting import EngagementSetting


class EngagementRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_settings(self) -> EngagementSetting | None:
        return self._db.query(EngagementSetting).order_by(EngagementSetting.id.asc()).first()

    def create_settings(self, settings: EngagementSetting) -> EngagementSetting:
        self._db.add(settings)
        self._db.commit()
        self._db.refresh(settings)
        return settings

    def update_settings(self, settings: EngagementSetting) -> EngagementSetting:
        self._db.commit()
        self._db.refresh(settings)
        return settings

    def create_history(self, history: EngagementCommentHistory) -> EngagementCommentHistory:
        self._db.add(history)
        self._db.commit()
        self._db.refresh(history)
        return history

    def update_history(self, history: EngagementCommentHistory) -> EngagementCommentHistory:
        self._db.commit()
        self._db.refresh(history)
        return history

    def get_history_by_id(self, history_id: int) -> EngagementCommentHistory | None:
        return (
            self._db.query(EngagementCommentHistory)
            .filter(EngagementCommentHistory.id == history_id)
            .first()
        )

    def list_history(self, status: str | None = None, limit: int = 100) -> list[EngagementCommentHistory]:
        query = self._db.query(EngagementCommentHistory)
        if status:
            query = query.filter(EngagementCommentHistory.status == status)
        return query.order_by(EngagementCommentHistory.created_at.desc()).limit(limit).all()

    def exists_for_post(self, post_url: str) -> bool:
        return (
            self._db.query(EngagementCommentHistory)
            .filter(
                EngagementCommentHistory.post_url == post_url,
                EngagementCommentHistory.status.in_([
                    "REVIEW_PENDING",
                    "APPROVED",
                    "POSTED",
                    "AUTO_POSTED",
                ]),
            )
            .first()
            is not None
        )

    def author_commented_recently(self, author: str, cooldown_hours: int) -> bool:
        if not author:
            return False
        since = datetime.utcnow() - timedelta(hours=max(1, cooldown_hours))
        return (
            self._db.query(EngagementCommentHistory)
            .filter(
                EngagementCommentHistory.post_author == author,
                EngagementCommentHistory.status.in_(["POSTED", "AUTO_POSTED"]),
                EngagementCommentHistory.posted_at.isnot(None),
                EngagementCommentHistory.posted_at >= since,
            )
            .first()
            is not None
        )

    def count_posted_today(self) -> int:
        return (
            self._db.query(func.count(EngagementCommentHistory.id))
            .filter(
                EngagementCommentHistory.status.in_(["POSTED", "AUTO_POSTED"]),
                func.date(EngagementCommentHistory.posted_at) == func.date(func.now()),
            )
            .scalar()
            or 0
        )

    def analytics_summary(self, days: int = 1) -> dict:
        days = max(1, days)
        since = datetime.utcnow() - timedelta(days=days)

        rows = (
            self._db.query(EngagementCommentHistory)
            .filter(EngagementCommentHistory.created_at >= since)
            .all()
        )

        total_generated = len([r for r in rows if r.generated_comment])
        posted = len([r for r in rows if r.status in {"POSTED", "AUTO_POSTED"}])
        accepted = len([r for r in rows if r.status in {"APPROVED", "POSTED", "AUTO_POSTED"}])
        edited = len([r for r in rows if r.posted_comment and r.generated_comment and r.posted_comment.strip() != r.generated_comment.strip()])
        replies = sum(int(r.replies_received or 0) for r in rows)
        likes = sum(int(r.likes_received or 0) for r in rows)

        topic_scores: dict[str, int] = {}
        style_scores: dict[str, int] = {}
        for row in rows:
            if row.status in {"POSTED", "AUTO_POSTED"}:
                topic_scores[row.topic] = topic_scores.get(row.topic, 0) + int(row.likes_received or 0) + int(row.replies_received or 0)
                style_scores[row.style] = style_scores.get(row.style, 0) + int(row.likes_received or 0) + int(row.replies_received or 0)

        best_topic = max(topic_scores, key=topic_scores.get) if topic_scores else None
        best_style = max(style_scores, key=style_scores.get) if style_scores else None

        return {
            "total_generated": total_generated,
            "comments_posted": posted,
            "accepted": accepted,
            "edited": edited,
            "replies_received": replies,
            "comment_likes": likes,
            "best_topic": best_topic,
            "best_style": best_style,
        }
