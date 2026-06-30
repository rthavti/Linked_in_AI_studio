from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.schedule import (
    ScheduleSettingCreate,
    ScheduleSettingRead,
)
from app.scheduler import schedule_jobs

router = APIRouter(
    prefix="/schedule",
    tags=["Schedule"],
)


@router.get("/settings", response_model=ScheduleSettingRead)
def get_schedule_settings(
    db: Session = Depends(get_db),
):
    repository = ScheduleRepository(db)
    setting = repository.get()

    if setting is None:
        setting = repository.create_default()

    return setting


@router.put("/settings", response_model=ScheduleSettingRead)
def update_schedule_settings(
    payload: ScheduleSettingCreate,
    db: Session = Depends(get_db),
):
    repository = ScheduleRepository(db)
    setting = repository.get()

    if setting is None:
        setting = repository.create_default()

    updated = repository.update(
        setting,
        morning_enabled=payload.morning_enabled,
        morning_time=payload.morning_time,
        evening_enabled=payload.evening_enabled,
        evening_time=payload.evening_time,
    )

    schedule_jobs()

    return updated
