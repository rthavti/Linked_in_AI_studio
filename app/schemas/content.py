from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from typing import Literal

from app.schemas.topic import TopicRead


class ContentGenerationResponse(BaseModel):
    success: bool
    message: str
    topic: TopicRead

    model_config = ConfigDict(from_attributes=True)


class ContentGenerationRequest(BaseModel):
    generate_images: bool = False
    image_count: int = Field(default=1, ge=1, le=2)
    image_style_hint: str | None = None
    visual_template: Literal[
        "auto",
        "matrix_2x2",
        "tool_comparison",
        "flow_diagram",
        "architecture_diagram",
        "timeline",
        "checklist",
    ] = "auto"
    image_size: Literal["1024x1024", "1536x1024", "1024x1536"] = "1536x1024"


class ContentEnhanceRequest(BaseModel):
    engagement_type: Literal[
        "discussion_starter",
        "how_to_playbook",
        "trend_radar",
        "case_study_breakdown",
        "cta_to_dm",
    ] = "discussion_starter"
    extra_keywords: list[str] = Field(default_factory=list)
    hashtag_count: int = 6


class ContentEnhanceResponse(BaseModel):
    success: bool
    message: str
    topic_id: int
    engagement_type: str
    optimized_post: str
    hooks: list[str]
    hashtags: list[str]


class TopicGeneratedImagesResponse(BaseModel):
    topic_id: int
    image_urls: list[str]
    image_error: str | None = None


class TopicImageGenerateRequest(BaseModel):
    image_count: int = Field(default=1, ge=1, le=2)
    image_style_hint: str | None = None
    visual_template: Literal[
        "auto",
        "matrix_2x2",
        "tool_comparison",
        "flow_diagram",
        "architecture_diagram",
        "timeline",
        "checklist",
    ] = "auto"
    image_size: Literal["1024x1024", "1536x1024", "1024x1536"] = "1536x1024"
