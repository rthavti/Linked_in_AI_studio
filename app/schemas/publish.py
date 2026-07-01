from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict


class LinkedInAccountCreate(BaseModel):
    provider_user_id: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class LinkedInAccountUpdate(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class LinkedInAccountRead(BaseModel):
    id: int
    provider_user_id: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublishHistoryRead(BaseModel):
    id: int
    topic_id: int
    linkedin_account_id: Optional[int] = None
    status: str
    response: Optional[str] = None
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OAuthStartResponse(BaseModel):
    authorize_url: str
    state: str


class OAuthCallbackResponse(BaseModel):
    account_id: int


class OAuthHealthRead(BaseModel):
    oauth_configured: bool
    client_id_configured: bool
    client_secret_configured: bool
    redirect_uri_configured: bool
    scopes_configured: bool
    token_secret_configured: bool
    oauth_state_ttl_seconds: int
    retry_delay_seconds: int
    connected: bool
    latest_account_id: Optional[int] = None


class PublishStatusRead(BaseModel):
    connected: bool
    account_count: int
    latest_account_id: Optional[int] = None


class PublishNowResponse(BaseModel):
    success: bool
    response: dict


class PublishMediaRequest(BaseModel):
    media_url: str
    mime_type: str | None = None
    linkedin_account_id: int | None = None


class PublishMediaResponse(BaseModel):
    success: bool
    asset_urn: str


class PublishQueueCreate(BaseModel):
    topic_id: int
    linkedin_account_id: Optional[int] = None
    scheduled_for: Optional[datetime] = None
    max_attempts: int = 3


class PublishQueueRead(BaseModel):
    id: int
    topic_id: int
    linkedin_account_id: Optional[int] = None
    status: str
    attempts: int
    max_attempts: int
    last_error: Optional[str] = None
    scheduled_for: datetime
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
