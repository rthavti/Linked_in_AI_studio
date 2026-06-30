from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.topic_repository import TopicRepository
from app.schemas.content import ContentGenerationResponse
from app.services.generation_service import GenerationService

router = APIRouter(
    prefix="/content",
    tags=["Content"],
)


@router.post(
    "/generate",
    response_model=ContentGenerationResponse,
    responses={
        400: {"description": "Bad request."},
        404: {"description": "No pending topics available for generation."},
        500: {"description": "Content generation failed."},
    },
)
def generate_content(
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_next_pending()

    if topic is None:
        raise HTTPException(
            status_code=404,
            detail="No pending topics available for generation.",
        )

    service = GenerationService(repository, db)
    success = service.generate_for_topic(topic)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Content generation failed.",
        )

    refreshed_topic = repository.get_by_id(topic.id)

    return {
        "success": True,
        "message": "LinkedIn content generated successfully.",
        "topic_id": refreshed_topic.id,
        "status": refreshed_topic.status,
    }
