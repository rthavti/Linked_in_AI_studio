"""
Generation History Repository

Handles generation history persistence.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.generation_history import GenerationHistory


class GenerationHistoryRepository:

    def __init__(self, db: Session):
        self._db = db

    def create(
        self,
        topic_id: int,
        version: int,
        prompt_template: str,
        prompt_version: str,
        model: str,
        temperature: float,
        max_tokens: int,
        status: str,
        generated_post: str | None = None,
        error_message: str | None = None,
        retry_count: int = 0,
        latency_ms: int | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> GenerationHistory:
        history = GenerationHistory(
            topic_id=topic_id,
            version=version,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            status=status,
            generated_post=generated_post,
            error_message=error_message,
            retry_count=retry_count,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        self._db.add(history)
        self._db.commit()
        self._db.refresh(history)
        return history

    def get_by_topic(self, topic_id: int) -> List[GenerationHistory]:
        return (
            self._db.query(GenerationHistory)
            .filter(GenerationHistory.topic_id == topic_id)
            .order_by(GenerationHistory.version.asc())
            .all()
        )

    def get_latest_version(self, topic_id: int) -> int:
        latest = (
            self._db.query(GenerationHistory)
            .filter(GenerationHistory.topic_id == topic_id)
            .order_by(GenerationHistory.version.desc())
            .first()
        )

        return latest.version if latest else 0
