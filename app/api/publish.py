import httpx

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.publish import (
    LinkedInAccountCreate,
    LinkedInAccountRead,
    LinkedInAccountUpdate,
    OAuthCallbackResponse,
    OAuthStartResponse,
    PublishHistoryRead,
    PublishMediaRequest,
    PublishMediaResponse,
    PublishNowResponse,
    PublishQueueCreate,
    PublishQueueRead,
    PublishStatusRead,
)
from app.services.publish_service import PublishService

router = APIRouter(
    prefix="/publish",
    tags=["Publish"],
)


def _raise_http_error(exc: Exception) -> None:
    detail = str(exc)
    status_code = 400
    if "not found" in detail.lower():
        status_code = 404
    raise HTTPException(status_code=status_code, detail=detail)


@router.get("/connect", response_model=OAuthStartResponse)
@router.get("/linkedin/connect", response_model=OAuthStartResponse)
def linkedin_connect(
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    try:
        return service.start_oauth()
    except ValueError as exc:
        _raise_http_error(exc)


@router.get("/callback", response_model=OAuthCallbackResponse)
@router.get("/linkedin/callback", response_model=OAuthCallbackResponse)
def linkedin_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    try:
        return service.handle_callback(code, state)
    except ValueError as exc:
        _raise_http_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/status", response_model=PublishStatusRead)
def get_publish_status(
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    return service.get_status()


@router.get("/accounts", response_model=list[LinkedInAccountRead])
def list_linkedin_accounts(
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    return service.get_accounts()


@router.post("/accounts", response_model=LinkedInAccountRead)
def create_linkedin_account(
    payload: LinkedInAccountCreate,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    try:
        return service.create_account(
            payload.provider_user_id,
            payload.access_token,
            payload.refresh_token,
            payload.expires_at,
        )
    except ValueError as exc:
        _raise_http_error(exc)


@router.get("/accounts/{account_id}", response_model=LinkedInAccountRead)
def get_linkedin_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="LinkedIn account not found.")
    return account


@router.put("/accounts/{account_id}", response_model=LinkedInAccountRead)
def update_linkedin_account(
    account_id: int,
    payload: LinkedInAccountUpdate,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    try:
        return service.update_account(
            account_id,
            payload.access_token,
            payload.refresh_token,
            payload.expires_at,
        )
    except ValueError as exc:
        _raise_http_error(exc)


@router.post("/accounts/{account_id}/disconnect")
@router.post("/disconnect")
def disconnect_linkedin_account(
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    if account_id is None:
        status = service.get_status()
        account_id = status["latest_account_id"]
    if account_id is None or not service.disconnect_account(account_id):
        raise HTTPException(status_code=404, detail="LinkedIn account not found.")
    return {"success": True}


@router.delete("/accounts/{account_id}")
def delete_linkedin_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    if not service.delete_account(account_id):
        raise HTTPException(status_code=404, detail="LinkedIn account not found.")
    return {"success": True}


@router.get("/history", response_model=list[PublishHistoryRead])
def list_publish_history(
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    return service.get_all_publish_history()


@router.get("/history/topics/{topic_id}", response_model=list[PublishHistoryRead])
def get_publish_history_for_topic(
    topic_id: int,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    return service.get_publish_history_by_topic(topic_id)


@router.post("/topics/{topic_id}/now", response_model=PublishNowResponse)
def publish_now(
    topic_id: int,
    linkedin_account_id: int | None = None,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    try:
        return service.publish_topic_now(topic_id, linkedin_account_id)
    except ValueError as exc:
        _raise_http_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/topics/{topic_id}/media", response_model=PublishMediaResponse)
def attach_media(
    topic_id: int,
    payload: PublishMediaRequest,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    try:
        return service.attach_media_to_topic(
            topic_id,
            payload.media_url,
            payload.mime_type,
            payload.linkedin_account_id,
        )
    except ValueError as exc:
        _raise_http_error(exc)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/queue", response_model=PublishQueueRead)
def enqueue_publish(
    payload: PublishQueueCreate,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    try:
        return service.enqueue_topic(
            payload.topic_id,
            payload.linkedin_account_id,
            payload.scheduled_for,
            payload.max_attempts,
        )
    except ValueError as exc:
        _raise_http_error(exc)


@router.get("/queue", response_model=list[PublishQueueRead])
def list_publish_queue(
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    return service.get_queue()


@router.post("/queue/{queue_id}/retry", response_model=PublishNowResponse)
@router.post("/retry/{queue_id}", response_model=PublishNowResponse)
def retry_publish_queue_item(
    queue_id: int,
    db: Session = Depends(get_db),
):
    service = PublishService(db)
    try:
        return service.process_queue_item(queue_id)
    except ValueError as exc:
        _raise_http_error(exc)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
