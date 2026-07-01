from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.topic import TopicStatus
from app.repositories.topic_repository import TopicRepository
from app.schemas.topic import (
    TopicContentUpdate,
    TopicCreate,
    TopicRead,
    TopicRegenerate,
    TopicUpdate,
)
from app.services.generation_service import GenerationService

router = APIRouter(
    prefix="/topics",
    tags=["Topics"],
)


@router.get("/", response_model=List[TopicRead])
def list_topics(
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    return repository.get_all()


@router.post(
    "/",
    response_model=TopicRead,
    responses={
        400: {"description": "Bad request."},
        404: {"description": "Not found."},
        500: {"description": "Internal server error."},
    },
)
def create_topic(
    payload: TopicCreate,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)

    if repository.get_by_topic(payload.topic):
        raise HTTPException(status_code=400, detail="Topic already exists.")

    topic = repository.create(
        topic_text=payload.topic,
        category=payload.category,
        priority=payload.priority,
    )
    repository.commit()
    repository.refresh(topic)

    return topic


@router.get(
    "/{topic_id}",
    response_model=TopicRead,
    responses={
        404: {"description": "Topic not found."},
    },
)
def get_topic(
    topic_id: int,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)

    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    return topic


@router.put(
    "/{topic_id}",
    response_model=TopicRead,
    responses={
        400: {"description": "Bad request."},
        404: {"description": "Not found."},
        500: {"description": "Internal server error."},
    },
)
def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)

    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    existing = repository.get_by_topic(payload.topic)
    if existing and existing.id != topic_id:
        raise HTTPException(status_code=400, detail="Topic already exists.")

    topic.topic = payload.topic
    topic.category = payload.category
    topic.priority = payload.priority

    updated = repository.update(topic)
    return updated


@router.put(
    "/{topic_id}/content",
    response_model=TopicRead,
    responses={
        400: {"description": "Bad request."},
        404: {"description": "Not found."},
        500: {"description": "Internal server error."},
    },
)
def update_topic_content(
    topic_id: int,
    payload: TopicContentUpdate,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)

    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    draft = payload.generated_post.strip()
    if not draft:
        raise HTTPException(status_code=400, detail="Generated content cannot be empty.")

    if not repository.update_generated_post(
        topic_id,
        TopicStatus.READY_FOR_REVIEW,
        draft,
    ):
        raise HTTPException(status_code=500, detail="Unable to update topic content.")

    return repository.get_by_id(topic_id)


@router.post(
    "/{topic_id}/approve",
    response_model=TopicRead,
    responses={
        400: {"description": "Bad request."},
        404: {"description": "Not found."},
        500: {"description": "Internal server error."},
    },
)
def approve_topic(
    topic_id: int,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)

    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    if not topic.generated_post:
        raise HTTPException(
            status_code=400,
            detail="Cannot approve a topic without generated content.",
        )

    if not repository.approve(topic_id):
        raise HTTPException(status_code=500, detail="Unable to approve topic.")

    return repository.get_by_id(topic_id)


@router.post(
    "/{topic_id}/reject",
    response_model=TopicRead,
    responses={
        400: {"description": "Bad request."},
        404: {"description": "Not found."},
        500: {"description": "Internal server error."},
    },
)
def reject_topic(
    topic_id: int,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)

    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    if not repository.reject(topic_id):
        raise HTTPException(status_code=500, detail="Unable to reject topic.")

    return repository.get_by_id(topic_id)


@router.post(
    "/{topic_id}/regenerate",
    response_model=TopicRead,
    responses={
        400: {"description": "Bad request."},
        404: {"description": "Not found."},
        500: {"description": "Internal server error."},
    },
)
def regenerate_topic(
    topic_id: int,
    payload: TopicRegenerate,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)

    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    service = GenerationService(repository, db)

    if not service.generate_for_topic(
        topic,
        template_name=payload.template_name,
        prompt_version=payload.prompt_version,
    ):
        raise HTTPException(status_code=500, detail="Regeneration failed.")

    return repository.get_by_id(topic_id)


@router.delete(
    "/{topic_id}",
    responses={
        404: {"description": "Topic not found."},
    },
)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)

    if not repository.delete(topic_id):
        raise HTTPException(status_code=404, detail="Topic not found.")

    return {"success": True}
