from pydantic import BaseModel
from pydantic import ConfigDict


class ContentGenerationResponse(BaseModel):
    success: bool
    message: str
    topic_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)
