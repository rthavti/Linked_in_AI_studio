from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict

from app.models.topic import Category
from app.models.topic import Priority


class CampaignItemRead(BaseModel):
    id: int
    day_number: int
    topic: str
    prompt_brief: str | None = None
    visual_hint: str | None = None
    category: Category
    priority: Priority
    status: str
    scheduled_for: datetime
    attempts: int
    topic_id: int | None = None
    published_at: datetime | None = None
    last_error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CampaignRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: str
    timezone: str
    publish_time: str
    start_date: str
    auto_approve: bool
    auto_publish: bool
    auto_generate_images: bool
    image_count: int
    visual_style: str
    max_attempts: int
    min_words: int
    max_words: int
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignDetailRead(CampaignRead):
    items: list[CampaignItemRead]


class CampaignActionResponse(BaseModel):
    success: bool
    message: str
    campaign: CampaignRead
