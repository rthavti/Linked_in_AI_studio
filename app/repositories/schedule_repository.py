from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.schedule_setting import ScheduleSetting


class ScheduleRepository:

    def __init__(self, db: Session):
        self._db = db

    def get(self) -> Optional[ScheduleSetting]:
        return (
            self._db.query(ScheduleSetting)
            .order_by(ScheduleSetting.id.asc())
            .first()
        )

    def create_default(self) -> ScheduleSetting:
        setting = ScheduleSetting()
        self._db.add(setting)
        self._db.commit()
        self._db.refresh(setting)
        return setting

    def update(
        self,
        setting: ScheduleSetting,
        morning_enabled: bool,
        morning_time: str,
        evening_enabled: bool,
        evening_time: str,
    ) -> ScheduleSetting:
        setting.morning_enabled = morning_enabled
        setting.morning_time = morning_time
        setting.evening_enabled = evening_enabled
        setting.evening_time = evening_time
        self._db.commit()
        self._db.refresh(setting)
        return setting
