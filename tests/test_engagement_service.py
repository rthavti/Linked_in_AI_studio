from datetime import datetime
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.db.models  # noqa: F401
from app.services.engagement_service import EngagementService
from app.services.token_service import TokenService
from app.repositories.linkedin_account_repository import LinkedInAccountRepository
from app.config.settings import settings


class FakeAIClient:
    def generate_post(self, prompt: str, system_prompt: str) -> dict:
        return {
            "content": "Strong point on automotive software safety. We found CI-driven traceability checks reduce integration risk and improve validation velocity. How are you linking requirements, generated artifacts, and test evidence across releases?"
        }


class FakeLinkedInClient:
    def refresh_access_token(self, refresh_token: str) -> dict:
        return {
            "access_token": "new-token",
            "refresh_token": refresh_token,
            "expires_in": 3600,
        }

    def comment_on_post(self, access_token: str, post_urn: str, author_urn: str, comment_text: str) -> dict:
        return {"id": "comment-1"}

    def is_post_accessible(self, access_token: str, post_urn: str) -> bool:
        return True


def create_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


class Candidate:
    def __init__(self, **kwargs):
        self.post_url = kwargs["post_url"]
        self.post_content = kwargs["post_content"]
        self.post_author = kwargs.get("post_author", "")
        self.post_urn = kwargs.get("post_urn")
        self.post_language = kwargs.get("post_language", "en")
        self.post_published_at = kwargs.get("post_published_at")
        self.post_reaction_count = kwargs.get("post_reaction_count", 0)
        self.is_company_page = kwargs.get("is_company_page", False)
        self.is_sponsored = kwargs.get("is_sponsored", False)
        self.is_recruiter = kwargs.get("is_recruiter", False)
        self.is_repost = kwargs.get("is_repost", False)


class Payload:
    def __init__(self, candidates, style=None, auto_post=False):
        self.candidates = candidates
        self.style = style
        self.auto_post = auto_post


def test_scan_candidates_queues_relevant_comment():
    session = create_session()
    service = EngagementService(session, ai_client=FakeAIClient(), linkedin_client=FakeLinkedInClient())

    payload = Payload(
        candidates=[
            Candidate(
                post_url="https://www.linkedin.com/feed/update/urn:li:share:1234567890123456789",
                post_urn="urn:li:share:1234567890123456789",
                post_author="Senior Automotive Engineer",
                post_content="AUTOSAR and CI/CD strategy for functional safety in SDV platforms.",
                post_published_at=datetime.utcnow() - timedelta(hours=2),
                post_reaction_count=124,
                post_language="en",
            )
        ],
        style="technical",
        auto_post=False,
    )

    result = service.scan_candidates(payload)

    assert result["searched"] == 1
    assert result["relevant"] == 1
    assert result["queued_for_review"] == 1
    comments = service.list_comments()
    assert len(comments) == 1
    assert comments[0].status == "REVIEW_PENDING"
    assert comments[0].generated_comment is not None


def test_approve_comment_posts_to_linkedin_when_requested():
    settings.LINKEDIN_TOKEN_SECRET = "test-token-secret"

    session = create_session()
    service = EngagementService(session, ai_client=FakeAIClient(), linkedin_client=FakeLinkedInClient())

    account_repo = LinkedInAccountRepository(session)
    account_repo.create_or_update(
        provider_user_id="mock-user-id",
        access_token=TokenService.encrypt("access-token"),
        refresh_token=TokenService.encrypt("refresh-token"),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )

    payload = Payload(
        candidates=[
            Candidate(
                post_url="https://www.linkedin.com/feed/update/urn:li:share:2234567890123456789",
                post_urn="urn:li:share:2234567890123456789",
                post_author="FDE Architect",
                post_content="Embedded systems reliability and deterministic CI pipeline design.",
                post_published_at=datetime.utcnow() - timedelta(hours=1),
                post_reaction_count=88,
            )
        ]
    )

    service.scan_candidates(payload)
    comment = service.list_comments()[0]

    updated = service.approve_comment(comment.id, post_now=True)

    assert updated.status == "POSTED"
    assert updated.linkedin_comment_id == "comment-1"
    assert updated.posted_at is not None


def test_scan_candidates_skips_invalid_post_url_or_urn():
    session = create_session()
    service = EngagementService(session, ai_client=FakeAIClient(), linkedin_client=FakeLinkedInClient())

    payload = Payload(
        candidates=[
            Candidate(
                post_url="https://www.linkedin.com/feed/update/not-a-valid-post",
                post_urn=None,
                post_author="Safety Engineer",
                post_content="Functional safety and SDV reliability practices.",
                post_published_at=datetime.utcnow() - timedelta(hours=1),
                post_reaction_count=120,
                post_language="en",
            )
        ],
        style="technical",
        auto_post=False,
    )

    result = service.scan_candidates(payload)

    assert result["searched"] == 1
    assert result["relevant"] == 0
    assert result["queued_for_review"] == 0
    assert result["skipped"] == 1
    comments = service.list_comments()
    assert len(comments) == 1
    assert comments[0].status == "SKIPPED"
    assert comments[0].skip_reason == "Invalid or missing LinkedIn post URL/URN."
