from pathlib import Path
import shutil
import tempfile

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.campaign import CampaignActionResponse
from app.schemas.campaign import CampaignDetailRead
from app.schemas.campaign import CampaignRead
from app.services.learning_campaign_service import LearningCampaignService


router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("/upload", response_model=CampaignDetailRead)
async def upload_campaign(
    name: str = Form(...),
    publish_time: str = Form("09:00"),
    timezone: str = Form("Asia/Kolkata"),
    start_date: str | None = Form(None),
    description: str | None = Form(None),
    auto_approve: bool = Form(True),
    auto_publish: bool = Form(True),
    auto_generate_images: bool = Form(True),
    image_count: int = Form(1),
    visual_style: str = Form("auto"),
    max_attempts: int = Form(3),
    min_words: int = Form(120),
    max_words: int = Form(320),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    extension = Path(file.filename).suffix.lower()
    if extension not in [".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Only Excel files are supported.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    tmp_path = Path(tmp.name)
    tmp.close()

    try:
        with tmp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        service = LearningCampaignService(db)
        campaign = service.create_campaign_from_excel(
            name=name,
            file_path=tmp_path,
            publish_time=publish_time,
            timezone_name=timezone,
            start_date_raw=start_date,
            description=description,
            auto_approve=auto_approve,
            auto_publish=auto_publish,
            auto_generate_images=auto_generate_images,
            image_count=image_count,
            visual_style=visual_style,
            max_attempts=max_attempts,
            min_words=min_words,
            max_words=max_words,
        )
        items = service.list_campaign_items(campaign.id)
        return CampaignDetailRead.model_validate({**campaign.__dict__, "items": items})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        await file.close()
        if tmp_path.exists():
            tmp_path.unlink()


@router.get("/", response_model=list[CampaignRead])
def list_campaigns(db: Session = Depends(get_db)):
    service = LearningCampaignService(db)
    return service.list_campaigns()


@router.get("/{campaign_id}", response_model=CampaignDetailRead)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    service = LearningCampaignService(db)
    campaign = service.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    items = service.list_campaign_items(campaign_id)
    return CampaignDetailRead.model_validate({**campaign.__dict__, "items": items})


@router.post("/{campaign_id}/pause", response_model=CampaignActionResponse)
def pause_campaign(campaign_id: int, db: Session = Depends(get_db)):
    service = LearningCampaignService(db)
    try:
        campaign = service.set_campaign_status(campaign_id, "PAUSED")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "success": True,
        "message": "Campaign paused.",
        "campaign": campaign,
    }


@router.post("/{campaign_id}/resume", response_model=CampaignActionResponse)
@router.post("/{campaign_id}/start", response_model=CampaignActionResponse)
def resume_campaign(campaign_id: int, db: Session = Depends(get_db)):
    service = LearningCampaignService(db)
    try:
        campaign = service.set_campaign_status(campaign_id, "ACTIVE")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "success": True,
        "message": "Campaign activated.",
        "campaign": campaign,
    }
