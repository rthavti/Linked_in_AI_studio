from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class GenerationHistoryRead(BaseModel):
    id: int
    topic_id: int
    version: int
    prompt_template: str
    prompt_version: str
    model: str
    temperature: float
    max_tokens: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    retry_count: int
    latency_ms: int | None = None
    generated_at: datetime
    generated_post: str | None = None
    error_message: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)
