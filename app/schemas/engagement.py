from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class EngagementSettingRead(BaseModel):
    id: int
    enabled: bool
    require_review: bool
    auto_post_enabled: bool
    posts_to_search_per_day: int
    comments_per_day: int
    min_reactions: int
    author_cooldown_hours: int
    style: str
    topics: list[str]
    topic_configs: list["EngagementTopicConfig"]
    blocked_keywords: list[str]
    own_author_identifiers: list[str]
    run_time: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EngagementSettingUpdate(BaseModel):
    enabled: bool | None = None
    require_review: bool | None = None
    auto_post_enabled: bool | None = None
    posts_to_search_per_day: int | None = Field(default=None, ge=1, le=200)
    comments_per_day: int | None = Field(default=None, ge=1, le=100)
    min_reactions: int | None = Field(default=None, ge=0, le=100000)
    author_cooldown_hours: int | None = Field(default=None, ge=1, le=720)
    style: str | None = None
    topics: list[str] | None = None
    topic_configs: list["EngagementTopicConfig"] | None = None
    blocked_keywords: list[str] | None = None
    own_author_identifiers: list[str] | None = None
    run_time: str | None = None


class EngagementTopicConfig(BaseModel):
    topic: str = Field(min_length=1, max_length=120)
    style: str | None = None
    min_reactions: int | None = Field(default=None, ge=0, le=100000)
    posts_to_search: int = Field(default=10, ge=1, le=50)
    comments_per_run: int = Field(default=2, ge=1, le=20)
    auto_post_enabled: bool = False
    require_review: bool = True


class EngagementDirectScanRequest(BaseModel):
    topics: list[EngagementTopicConfig] | None = None


class EngagementCandidatePost(BaseModel):
    post_url: str
    post_content: str
    post_author: str = ""
    post_urn: str | None = None
    post_language: str | None = "en"
    post_published_at: datetime | None = None
    post_reaction_count: int = 0
    is_company_page: bool = False
    is_sponsored: bool = False
    is_recruiter: bool = False
    is_repost: bool = False


class EngagementScanRequest(BaseModel):
    candidates: list[EngagementCandidatePost]
    style: str | None = None
    auto_post: bool = False


class EngagementScanResponse(BaseModel):
    searched: int
    relevant: int
    queued_for_review: int
    posted: int
    skipped: int


class EngagementPostLink(BaseModel):
    label: str
    url: str
    topic: str | None = None
    status: str | None = None


class EngagementDirectScanResponse(EngagementScanResponse):
    searched_by_topic: dict[str, int] = {}
    post_links: list[EngagementPostLink] = Field(default_factory=list)


class EngagementCommentRead(BaseModel):
    id: int
    post_url: str
    post_urn: str | None = None
    post_author: str | None = None
    post_language: str | None = None
    post_content: str
    post_published_at: datetime | None = None
    post_reaction_count: int
    topic: str
    style: str
    relevance_score: int
    generated_comment: str | None = None
    posted_comment: str | None = None
    status: str
    skip_reason: str | None = None
    is_company_page: bool
    is_sponsored: bool
    is_recruiter: bool
    is_repost: bool
    linkedin_comment_id: str | None = None
    posted_at: datetime | None = None
    likes_received: int
    replies_received: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EngagementApproveRequest(BaseModel):
    edited_comment: str | None = None
    post_now: bool = True


class EngagementSkipRequest(BaseModel):
    reason: str | None = None


class EngagementAnalyticsRead(BaseModel):
    total_generated: int
    comments_posted: int
    accepted: int
    edited: int
    replies_received: int
    comment_likes: int
    best_topic: str | None = None
    best_style: str | None = None
