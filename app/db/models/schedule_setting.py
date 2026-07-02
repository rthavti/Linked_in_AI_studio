from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy import func

from app.database import Base


class ScheduleSetting(Base):
    __tablename__ = "schedule_settings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    morning_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    morning_time = Column(
        String(5),
        nullable=False,
        default="08:00",
    )

    evening_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    evening_time = Column(
        String(5),
        nullable=False,
        default="17:00",
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ScheduleSetting(id={self.id}, "
            f"morning_enabled={self.morning_enabled}, "
            f"morning_time='{self.morning_time}', "
            f"evening_enabled={self.evening_enabled}, "
            f"evening_time='{self.evening_time}')>"
        )
