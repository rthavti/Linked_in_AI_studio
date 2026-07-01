from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class ScheduleSettingCreate(BaseModel):
    morning_enabled: bool = True
    morning_time: str = Field(default="08:00", min_length=5, max_length=5)
    evening_enabled: bool = True
    evening_time: str = Field(default="17:00", min_length=5, max_length=5)

    @field_validator("morning_time", "evening_time")
    def validate_time(cls, value: str) -> str:
        if not value:
            return value

        if not isinstance(value, str):
            raise ValueError("Time must be a string in HH:MM format.")

        if len(value) != 5 or value[2] != ":":
            raise ValueError("Time must be in HH:MM format.")

        hour, minute = value.split(":")

        if not hour.isdigit() or not minute.isdigit():
            raise ValueError("Time must be in HH:MM format.")

        if not (0 <= int(hour) <= 23) or not (0 <= int(minute) <= 59):
            raise ValueError("Time must be in HH:MM format (00:00-23:59).")

        return value

    @model_validator(mode="after")
    def validate_windows(self):
        if (
            self.morning_enabled
            and self.evening_enabled
            and self.morning_time == self.evening_time
        ):
            raise ValueError("Morning and evening times must be different.")

        return self


class ScheduleSettingRead(ScheduleSettingCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
