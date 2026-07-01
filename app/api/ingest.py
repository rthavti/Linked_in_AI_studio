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
)
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