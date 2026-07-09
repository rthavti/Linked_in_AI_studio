from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.engagement import EngagementAnalyticsRead
from app.schemas.engagement import EngagementApproveRequest
from app.schemas.engagement import EngagementCommentRead
from app.schemas.engagement import EngagementDirectScanRequest
from app.schemas.engagement import EngagementDirectScanResponse
from app.schemas.engagement import EngagementScanRequest
from app.schemas.engagement import EngagementScanResponse
from app.schemas.engagement import EngagementSettingRead
from app.schemas.engagement import EngagementSettingUpdate
from app.schemas.engagement import EngagementSkipRequest
from app.services.engagement_service import EngagementService

router = APIRouter(prefix="/engagement", tags=["Engagement"])


def _raise_http_error(exc: Exception) -> None:
    detail = str(exc)
    status_code = 400
    if "not found" in detail.lower():
        status_code = 404
    raise HTTPException(status_code=status_code, detail=detail)


@router.get("/settings", response_model=EngagementSettingRead)
def get_engagement_settings(db: Session = Depends(get_db)):
    service = EngagementService(db)
    settings = service.get_or_create_settings()
    return service.to_settings_read(settings)


@router.put("/settings", response_model=EngagementSettingRead)
def update_engagement_settings(payload: EngagementSettingUpdate, db: Session = Depends(get_db)):
    service = EngagementService(db)
    try:
        settings = service.update_settings(payload)
        return service.to_settings_read(settings)
    except ValueError as exc:
        _raise_http_error(exc)


@router.post("/scan", response_model=EngagementScanResponse)
def scan_engagement_candidates(payload: EngagementScanRequest, db: Session = Depends(get_db)):
    service = EngagementService(db)
    try:
        return service.scan_candidates(payload)
    except ValueError as exc:
        _raise_http_error(exc)


@router.post("/scan-direct", response_model=EngagementDirectScanResponse)
def scan_engagement_direct(payload: EngagementDirectScanRequest, db: Session = Depends(get_db)):
    service = EngagementService(db)
    try:
        return service.scan_direct_from_linkedin(payload.topics)
    except ValueError as exc:
        _raise_http_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/scan-collector", response_model=EngagementScanResponse)
def scan_engagement_collector(payload: EngagementDirectScanRequest, db: Session = Depends(get_db)):
    service = EngagementService(db)
    try:
        return service.scan_from_collector(payload.topics)
    except ValueError as exc:
        _raise_http_error(exc)


@router.post("/run-daily", response_model=EngagementScanResponse)
def run_daily_engagement_scan(db: Session = Depends(get_db)):
    service = EngagementService(db)
    return service.run_daily_scan()


@router.get("/comments", response_model=list[EngagementCommentRead])
def list_engagement_comments(status: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    service = EngagementService(db)
    return service.list_comments(status=status, limit=limit)


@router.post("/comments/{history_id}/approve", response_model=EngagementCommentRead)
def approve_engagement_comment(history_id: int, payload: EngagementApproveRequest, db: Session = Depends(get_db)):
    service = EngagementService(db)
    try:
        return service.approve_comment(history_id, edited_comment=payload.edited_comment, post_now=payload.post_now)
    except ValueError as exc:
        _raise_http_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/comments/{history_id}/skip", response_model=EngagementCommentRead)
def skip_engagement_comment(history_id: int, payload: EngagementSkipRequest, db: Session = Depends(get_db)):
    service = EngagementService(db)
    try:
        return service.skip_comment(history_id, reason=payload.reason)
    except ValueError as exc:
        _raise_http_error(exc)


@router.get("/analytics", response_model=EngagementAnalyticsRead)
def get_engagement_analytics(days: int = 1, db: Session = Depends(get_db)):
    service = EngagementService(db)
    return service.analytics(days=days)
