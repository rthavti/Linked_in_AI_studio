from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pathlib import Path
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database import get_db
from app.repositories.topic_repository import TopicRepository
from app.schemas.content import ContentGenerationResponse
from app.schemas.content import ContentGenerationRequest
from app.schemas.content import ContentEnhanceRequest
from app.schemas.content import ContentEnhanceResponse
from app.schemas.content import TopicImageGenerateRequest
from app.schemas.content import TopicGeneratedImagesResponse
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
    payload: ContentGenerationRequest | None = None,
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
    generate_images = payload.generate_images if payload else False
    image_count = payload.image_count if payload else 1
    image_style_hint = payload.image_style_hint if payload else None
    visual_template = payload.visual_template if payload else "auto"
    image_size = payload.image_size if payload else "1536x1024"

    success = service.generate_for_topic(
        topic,
        generate_images=generate_images,
        image_count=image_count,
        image_style_hint=image_style_hint,
        visual_template=visual_template,
        image_size=image_size,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Content generation failed.",
        )

    refreshed_topic = repository.get_by_id(topic.id)

    return {
        "success": True,
        "message": "LinkedIn content generated successfully.",
        "topic": refreshed_topic,
    }


@router.post(
    "/{topic_id}/enhance",
    response_model=ContentEnhanceResponse,
    responses={
        400: {"description": "Bad request."},
        404: {"description": "Topic not found."},
        500: {"description": "Enhancement failed."},
    },
)
def enhance_content(
    topic_id: int,
    payload: ContentEnhanceRequest,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    service = GenerationService(repository, db)
    try:
        return service.enhance_engagement(
            topic,
            engagement_type=payload.engagement_type,
            extra_keywords=payload.extra_keywords,
            hashtag_count=payload.hashtag_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/{topic_id}/images",
    response_model=TopicGeneratedImagesResponse,
    responses={
        404: {"description": "Topic not found."},
    },
)
def list_generated_images(
    topic_id: int,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    image_error = None
    if topic.error_message and topic.error_message.lower().startswith("image generation failed:"):
        image_error = topic.error_message

    generated_dir = Path(__file__).resolve().parent.parent / "static" / "generated"
    if not generated_dir.exists():
        return {"topic_id": topic_id, "image_urls": [], "image_error": image_error}

    files = sorted(
        generated_dir.glob(f"topic-{topic_id}-*.png"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    image_urls = [
        f"http://{settings.host}:{settings.port}/static/generated/{path.name}"
        for path in files
    ]
    return {"topic_id": topic_id, "image_urls": image_urls, "image_error": image_error}


@router.post(
    "/{topic_id}/generate-images",
    response_model=TopicGeneratedImagesResponse,
    responses={
        404: {"description": "Topic not found."},
        500: {"description": "Image generation failed."},
    },
)
def generate_images_for_topic(
    topic_id: int,
    payload: TopicImageGenerateRequest,
    db: Session = Depends(get_db),
):
    repository = TopicRepository(db)
    topic = repository.get_by_id(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found.")

    service = GenerationService(repository, db)
    try:
        service.generate_images_for_topic(
            topic,
            image_count=payload.image_count,
            image_style_hint=payload.image_style_hint,
            visual_template=payload.visual_template,
            image_size=payload.image_size,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {exc}")

    refreshed = repository.get_by_id(topic_id)
    image_error = None
    if refreshed and refreshed.error_message and refreshed.error_message.lower().startswith("image generation failed:"):
        image_error = refreshed.error_message

    generated_dir = Path(__file__).resolve().parent.parent / "static" / "generated"
    if not generated_dir.exists():
        return {"topic_id": topic_id, "image_urls": [], "image_error": image_error}

    files = sorted(
        generated_dir.glob(f"topic-{topic_id}-*.png"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    image_urls = [
        f"http://{settings.host}:{settings.port}/static/generated/{path.name}"
        for path in files
    ]

    return {"topic_id": topic_id, "image_urls": image_urls, "image_error": image_error}
