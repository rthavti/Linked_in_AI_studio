from pydantic import BaseModel
from pydantic import ConfigDict

from app.schemas.topic import TopicRead


class ContentGenerationResponse(BaseModel):
    success: bool
    message: str
    topic: TopicRead

    model_config = ConfigDict(from_attributes=True)
