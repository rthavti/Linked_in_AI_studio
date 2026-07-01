import secrets
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import httpx

from app.ai.linkedin_client import LinkedInClient
from app.config.settings import settings
from app.logger import logger
from app.models.topic import TopicStatus
from app.repositories.linkedin_account_repository import LinkedInAccountRepository
from app.repositories.oauth_state_repository import OAuthStateRepository
from app.repositories.publish_history_repository import PublishHistoryRepository
from app.repositories.publish_queue_repository import PublishQueueRepository
from app.repositories.topic_repository import TopicRepository
from app.services.token_service import TokenService


PUBLISHABLE_STATUSES = {
    TopicStatus.APPROVED,
    TopicStatus.SCHEDULED,
}


class PublishService:

    def __init__(self, db_session, client: LinkedInClient | None = None):
        self.db = db_session
        self.client = client or LinkedInClient()
        self.topic_repo = TopicRepository(db_session)
        self.account_repo = LinkedInAccountRepository(db_session)
        self.history_repo = PublishHistoryRepository(db_session)
        self.oauth_state_repo = OAuthStateRepository(db_session)
        self.queue_repo = PublishQueueRepository(db_session)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc).replace(microsecond=0)

    @staticmethod
    def _as_aware(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def start_oauth(self) -> dict:
        state = secrets.token_urlsafe(32)
        expires_at = self._utcnow() + timedelta(
            seconds=settings.LINKEDIN_OAUTH_STATE_TTL_SECONDS
        )
        self.oauth_state_repo.create(state, expires_at)
        logger.info("Created LinkedIn OAuth state.")
        return {
            "authorize_url": self.client.get_authorize_url(state),
            "state": state,
        }

    def _validate_oauth_state(self, state: str) -> None:
        oauth_state = self.oauth_state_repo.get_by_state(state)
        if oauth_state is None:
            raise ValueError("Invalid LinkedIn OAuth state.")
        if oauth_state.used:
            raise ValueError("LinkedIn OAuth state has already been used.")
        expires_at = self._as_aware(oauth_state.expires_at)
        if expires_at is None or expires_at <= self._utcnow():
            raise ValueError("LinkedIn OAuth state has expired.")
        self.oauth_state_repo.mark_used(oauth_state)

    def handle_callback(self, code: str, state: str) -> dict:
        self._validate_oauth_state(state)
        token_resp = self.client.exchange_code_for_token(code)
        access_token = token_resp.get("access_token")
        refresh_token = token_resp.get("refresh_token")
        expires_in = token_resp.get("expires_in")
        expires_at = None
        if expires_in is not None:
            expires_at = self._utcnow() + timedelta(seconds=int(expires_in))

        if not access_token:
            raise ValueError("LinkedIn OAuth callback did not return access token.")

        profile = self.client.get_profile(access_token)
        provider_user_id = profile.get("id")
        if not provider_user_id:
            raise ValueError("LinkedIn profile response did not include an id.")

        account = self.account_repo.create_or_update(
            provider_user_id,
            TokenService.encrypt(access_token),
            TokenService.encrypt(refresh_token),
            expires_at,
        )
        logger.info("LinkedIn account connected: %s", account.id)
        return {"account_id": account.id}

    def _get_valid_access_token(self, account):
        if account is None:
            return None

        access_token = TokenService.decrypt(account.access_token)
        expires_at = self._as_aware(account.expires_at)
        if expires_at is not None and expires_at <= self._utcnow():
            refresh_token = TokenService.decrypt(account.refresh_token)
            if not refresh_token:
                raise ValueError(
                    "LinkedIn access token expired and no refresh token is available."
                )
            refresh_resp = self.client.refresh_access_token(refresh_token)
            new_access_token = refresh_resp.get("access_token")
            if not new_access_token:
                raise ValueError("LinkedIn token refresh did not return access token.")
            new_refresh_token = refresh_resp.get("refresh_token") or refresh_token
            expires_in = refresh_resp.get("expires_in")
            new_expires_at = None
            if expires_in is not None:
                new_expires_at = self._utcnow() + timedelta(seconds=int(expires_in))
            account = self.account_repo.create_or_update(
                account.provider_user_id,
                TokenService.encrypt(new_access_token),
                TokenService.encrypt(new_refresh_token),
                new_expires_at,
            )
            access_token = new_access_token

        return access_token

    def get_status(self) -> dict:
        accounts = self.account_repo.get_all()
        latest = accounts[0] if accounts else None
        return {
            "connected": latest is not None,
            "account_count": len(accounts),
            "latest_account_id": latest.id if latest else None,
        }

    def get_oauth_health(self) -> dict:
        status = self.get_status()
        client_id = bool(settings.LINKEDIN_CLIENT_ID.strip())
        client_secret = bool(settings.LINKEDIN_CLIENT_SECRET.strip())
        redirect_uri = bool(settings.LINKEDIN_REDIRECT_URI.strip())
        scopes = bool(settings.LINKEDIN_SCOPES.strip())
        token_secret = bool((settings.LINKEDIN_TOKEN_SECRET or settings.LINKEDIN_CLIENT_SECRET or '').strip())

        return {
            "oauth_configured": all([client_id, client_secret, redirect_uri, scopes, token_secret]),
            "client_id_configured": client_id,
            "client_secret_configured": client_secret,
            "redirect_uri_configured": redirect_uri,
            "scopes_configured": scopes,
            "token_secret_configured": token_secret,
            "oauth_state_ttl_seconds": settings.LINKEDIN_OAUTH_STATE_TTL_SECONDS,
            "retry_delay_seconds": settings.PUBLISH_RETRY_DELAY_SECONDS,
            "connected": status["connected"],
            "latest_account_id": status["latest_account_id"],
        }

    def get_accounts(self):
        return self.account_repo.get_all()

    def get_account(self, account_id: int):
        return self.account_repo.get_by_id(account_id)

    def create_account(
        self,
        provider_user_id: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at=None,
    ):
        return self.account_repo.create_or_update(
            provider_user_id,
            TokenService.encrypt(access_token),
            TokenService.encrypt(refresh_token),
            expires_at,
        )

    def update_account(
        self,
        account_id: int,
        access_token: str,
        refresh_token: str | None = None,
        expires_at=None,
    ):
        account = self.account_repo.get_by_id(account_id)
        if account is None:
            raise ValueError("LinkedIn account not found.")

        account.access_token = TokenService.encrypt(access_token)
        if refresh_token is not None:
            account.refresh_token = TokenService.encrypt(refresh_token)
        if expires_at is not None:
            account.expires_at = expires_at

        return self.account_repo.update(account)

    def disconnect_account(self, account_id: int) -> bool:
        return self.account_repo.disconnect(account_id)

    def delete_account(self, account_id: int) -> bool:
        return self.account_repo.delete(account_id)

    def get_publish_history_by_topic(self, topic_id: int):
        return self.history_repo.get_by_topic(topic_id)

    def get_all_publish_history(self):
        return self.history_repo.get_all()

    def get_queue(self):
        return self.queue_repo.get_all()

    def enqueue_topic(
        self,
        topic_id: int,
        linkedin_account_id: int | None = None,
        scheduled_for: datetime | None = None,
        max_attempts: int = 3,
    ):
        topic = self.topic_repo.get_by_id(topic_id)
        if topic is None:
            raise ValueError("Topic not found.")
        self._validate_publishable_topic(topic)
        if linkedin_account_id is not None and self.account_repo.get_by_id(linkedin_account_id) is None:
            raise ValueError("LinkedIn account not found.")
        item = self.queue_repo.create(
            topic_id,
            linkedin_account_id,
            scheduled_for,
            max_attempts,
        )
        topic.status = TopicStatus.SCHEDULED
        self.topic_repo.update(topic)
        return item

    def _resolve_account(self, linkedin_account_id: int | None):
        if linkedin_account_id is not None:
            account = self.account_repo.get_by_id(linkedin_account_id)
            if account is None:
                raise ValueError("LinkedIn account not found.")
            return account
        account = self.account_repo.get_latest()
        if account is None:
            raise ValueError("No LinkedIn account configured.")
        return account

    def attach_media_to_topic(
        self,
        topic_id: int,
        media_url: str,
        mime_type: str | None = None,
        linkedin_account_id: int | None = None,
    ) -> dict:
        topic = self.topic_repo.get_by_id(topic_id)
        if topic is None:
            raise ValueError("Topic not found.")

        response = httpx.get(media_url, timeout=30)
        response.raise_for_status()
        image_bytes = response.content
        content_type = mime_type or response.headers.get("Content-Type")
        if not content_type:
            raise ValueError("Unable to determine media MIME type.")

        account = self._resolve_account(linkedin_account_id)
        access_token = self._get_valid_access_token(account)
        if not access_token:
            raise ValueError("No LinkedIn access token is available.")

        author_urn = f"urn:li:person:{account.provider_user_id}"
        upload_info = self.client.register_image_upload(
            access_token,
            author_urn,
            content_type,
        )
        upload_url = upload_info.get("upload_url")
        asset_urn = upload_info.get("asset_urn")

        if not upload_url or not asset_urn:
            raise ValueError("LinkedIn asset registration failed.")

        self.client.upload_image(upload_url, image_bytes, content_type)

        topic.media_asset_urn = asset_urn
        topic.media_mime_type = content_type
        self.topic_repo.update(topic)

        return {"success": True, "asset_urn": asset_urn}

    @staticmethod
    def _validate_publishable_topic(topic) -> None:
        if not topic.generated_post or not topic.generated_post.strip():
            raise ValueError("Cannot publish a topic without generated content.")
        if topic.status not in PUBLISHABLE_STATUSES:
            raise ValueError("Topic must be approved or scheduled before publishing.")

    def publish_topic_now(
        self,
        topic_id: int,
        linkedin_account_id: int | None = None,
    ) -> dict:
        topic = self.topic_repo.get_by_id(topic_id)
        if topic is None:
            raise ValueError("Topic not found.")
        self._validate_publishable_topic(topic)

        account = self._resolve_account(linkedin_account_id)
        access_token = self._get_valid_access_token(account)
        if not access_token:
            raise ValueError("No LinkedIn access token is available.")

        author_urn = f"urn:li:person:{account.provider_user_id}"
        try:
            resp = self.client.publish_post(
                access_token,
                author_urn,
                topic.generated_post.strip(),
                asset_urn=topic.media_asset_urn,
            )
            published_at = self._utcnow()
            self.history_repo.create(
                topic.id,
                account.id,
                "PUBLISHED",
                response=str(resp),
                published_at=published_at,
            )
            self.topic_repo.update_generated_post(
                topic.id,
                TopicStatus.PUBLISHED,
                topic.generated_post,
            )
            logger.info("Published topic %s to LinkedIn", topic.id)
            return {"success": True, "response": resp}
        except Exception as exc:
            self.history_repo.create(
                topic.id,
                account.id,
                "FAILED",
                error_message=str(exc),
            )
            logger.exception("Publish failed for topic %s", topic.id)
            raise

    def process_queue_item(self, queue_id: int) -> dict:
        item = self.queue_repo.get_by_id(queue_id)
        if item is None:
            raise ValueError("Publish queue item not found.")
        if item.status == "PUBLISHED":
            return {"success": True, "response": {"message": "Already published."}}

        item.status = "PROCESSING"
        self.queue_repo.update(item)

        try:
            result = self.publish_topic_now(item.topic_id, item.linkedin_account_id)
            item.status = "PUBLISHED"
            item.published_at = self._utcnow()
            item.last_error = None
            self.queue_repo.update(item)
            return result
        except Exception as exc:
            item.attempts += 1
            item.last_error = str(exc)
            if item.attempts >= item.max_attempts:
                item.status = "FAILED"
            else:
                item.status = "RETRY"
                item.scheduled_for = self._utcnow() + timedelta(
                    seconds=settings.PUBLISH_RETRY_DELAY_SECONDS
                )
            self.queue_repo.update(item)
            raise

    def process_due_queue(self, limit: int = 10) -> int:
        ready_items = self.queue_repo.get_ready(self._utcnow(), limit)
        processed = 0
        for item in ready_items:
            try:
                self.process_queue_item(item.id)
                processed += 1
            except Exception:
                logger.exception("Publish queue item failed: %s", item.id)
        return processed
