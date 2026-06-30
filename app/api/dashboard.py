from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.topic_repository import TopicRepository
from app.models.topic import TopicStatus

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)

    total_topics = repository.count()
    ready = repository.find_by_status(TopicStatus.READY)
    ready_for_review = repository.find_by_status(TopicStatus.READY_FOR_REVIEW)
    approved = repository.find_by_status(TopicStatus.APPROVED)
    scheduled = repository.find_by_status(TopicStatus.SCHEDULED)
    published = repository.find_by_status(TopicStatus.PUBLISHED)
    failed = repository.find_by_status(TopicStatus.FAILED)
    pending = repository.find_by_status(TopicStatus.NEW)

    return {
        "total_topics": total_topics,
        "generated": len(ready) + len(ready_for_review) + len(approved) + len(scheduled) + len(published),
        "failed": len(failed),
        "published": len(published),
        "pending": len(pending),
    }
