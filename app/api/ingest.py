"""
Excel Ingestion API
"""

from pathlib import Path
import shutil
import tempfile

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ingest import (
    IngestResponse,
    TrendingGenerateRequest,
    TrendingGenerateResponse,
)
from app.services.trending_service import TrendingService
from app.workflows.ingest_workflow import IngestWorkflow

router = APIRouter(
    prefix="/ingest",
    tags=["Ingestion"],
)


@router.post(
    "/upload",
    response_model=IngestResponse,
    responses={
        400: {"description": "Invalid upload request."},
        500: {"description": "Internal server error."},
    },
)
async def upload_topics(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in [".xlsx", ".xls"]:

        raise HTTPException(
            status_code=400,
            detail="Only Excel files are supported.",
        )

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension,
    )

    temp_path = Path(temp_file.name)

    temp_file.close()

    try:

        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        workflow = IngestWorkflow(db)

        summary, rows = workflow.execute(temp_path)

        return IngestResponse(
            success=True,
            message="Topics imported successfully.",
            summary=summary,
            rows=rows,
        )

    finally:

        await file.close()

        if temp_path.exists():
            temp_path.unlink()


@router.post(
    "/trending",
    response_model=TrendingGenerateResponse,
    responses={
        400: {"description": "Invalid request or no trend results found."},
        500: {"description": "Trending generation failed."},
    },
)
def generate_trending_topic(
    payload: TrendingGenerateRequest,
    db: Session = Depends(get_db),
):
    service = TrendingService(db)
    try:
        return service.generate_trending_topic(
            engagement_type=payload.engagement_type,
            category=payload.category,
            priority=payload.priority,
            keyword=payload.keyword,
            max_items=payload.max_items,
            image_count=payload.image_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))