from __future__ import annotations

import json
import re
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from app.ai.client import OpenAIClient
from app.ai.linkedin_client import LinkedInClient
from app.db.models.engagement_comment_history import EngagementCommentHistory
from app.db.models.engagement_setting import EngagementSetting
from app.logger import logger
from app.repositories.engagement_repository import EngagementRepository
from app.repositories.linkedin_account_repository import LinkedInAccountRepository
from app.services.token_service import TokenService


STYLE_PROMPTS = {
    "professional": "Write in a professional senior-engineer tone.",
    "thought_leadership": "Write in a thought-leadership tone with a strategic edge.",
    "technical": "Write in a highly technical and implementation-oriented tone.",
    "question": "Write as a technical question-first response that invites dialogue.",
}


DEFAULT_TOPICS = [
    "functional safety",
    "fde",
    "autosar",
    "sdv",
    "ci/cd",
    "devops",
    "ai",
    "automotive",
    "embedded systems",
]


DEFAULT_BLOCKED_KEYWORDS = [
    "hiring",
    "job opening",
    "apply now",
    "politics",
    "political",
    "election",
    "religion",
    "religious",
    "sponsored",
    "promoted",
]


DEFAULT_TOPIC_CONFIG = {
    "style": "professional",
    "min_reactions": 50,
    "posts_to_search": 10,
    "comments_per_run": 2,
    "auto_post_enabled": False,
    "require_review": True,
}


class EngagementService:
    def __init__(self, db_session, ai_client: OpenAIClient | None = None, linkedin_client: LinkedInClient | None = None):
        self.db = db_session
        self.repo = EngagementRepository(db_session)
        self.account_repo = LinkedInAccountRepository(db_session)
        self.ai_client = ai_client
        self.linkedin_client = linkedin_client or LinkedInClient()

    def _get_ai_client(self) -> OpenAIClient:
        if self.ai_client is None:
            self.ai_client = OpenAIClient()
        return self.ai_client

    @staticmethod
    def _csv_to_list(value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _list_to_csv(values: list[str] | None) -> str:
        if not values:
            return ""
        unique = []
        seen = set()
        for value in values:
            normalized = str(value).strip()
            lowered = normalized.lower()
            if normalized and lowered not in seen:
                unique.append(normalized)
                seen.add(lowered)
        return ", ".join(unique)

    @staticmethod
    def _normalize_style(style: str | None) -> str:
        style_key = (style or "professional").strip().lower()
        if style_key not in STYLE_PROMPTS:
            return "professional"
        return style_key

    def _normalize_topic_config(self, raw: dict) -> dict:
        topic = str((raw or {}).get("topic") or "").strip()
        if not topic:
            raise ValueError("Topic config requires a non-empty topic.")

        style = self._normalize_style((raw or {}).get("style") or DEFAULT_TOPIC_CONFIG["style"])

        min_reactions = (raw or {}).get("min_reactions")
        if min_reactions is None:
            min_reactions = DEFAULT_TOPIC_CONFIG["min_reactions"]

        posts_to_search = int((raw or {}).get("posts_to_search") or DEFAULT_TOPIC_CONFIG["posts_to_search"])
        comments_per_run = int((raw or {}).get("comments_per_run") or DEFAULT_TOPIC_CONFIG["comments_per_run"])

        return {
            "topic": topic,
            "style": style,
            "min_reactions": max(0, int(min_reactions)),
            "posts_to_search": min(50, max(1, posts_to_search)),
            "comments_per_run": min(20, max(1, comments_per_run)),
            "auto_post_enabled": bool((raw or {}).get("auto_post_enabled", DEFAULT_TOPIC_CONFIG["auto_post_enabled"])),
            "require_review": bool((raw or {}).get("require_review", DEFAULT_TOPIC_CONFIG["require_review"])),
        }

    def _topic_configs_from_json(self, value: str | None) -> list[dict]:
        if not value:
            return []
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []

        configs: list[dict] = []
        seen: set[str] = set()
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                config = self._normalize_topic_config(row)
            except ValueError:
                continue
            lowered = config["topic"].lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            configs.append(config)
        return configs

    def _topic_configs_to_json(self, configs: list[dict] | None) -> str:
        normalized = [self._normalize_topic_config(item) for item in (configs or [])]
        return json.dumps(normalized, separators=(",", ":"))

    @staticmethod
    def _word_count(text: str) -> int:
        return len([token for token in (text or "").split() if token.strip()])

    @staticmethod
    def _contains_emoji(text: str) -> bool:
        if not text:
            return False
        return bool(re.search(r"[\U0001F300-\U0001FAFF]", text))

    @staticmethod
    def _parse_run_time(value: str | None) -> str:
        raw = (value or "09:30").strip()
        parts = raw.split(":")
        if len(parts) != 2:
            raise ValueError("run_time must be in HH:MM format.")
        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError as exc:
            raise ValueError("run_time must be in HH:MM format.") from exc
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("run_time must be between 00:00 and 23:59.")
        return f"{hour:02d}:{minute:02d}"

    def get_or_create_settings(self) -> EngagementSetting:
        settings = self.repo.get_settings()
        if settings is not None:
            return settings

        settings = EngagementSetting(
            enabled=False,
            require_review=True,
            auto_post_enabled=False,
            posts_to_search_per_day=30,
            comments_per_day=5,
            min_reactions=50,
            author_cooldown_hours=72,
            style="professional",
            topics=self._list_to_csv(DEFAULT_TOPICS),
            topic_configs_json=self._topic_configs_to_json([{"topic": topic} for topic in DEFAULT_TOPICS]),
            blocked_keywords=self._list_to_csv(DEFAULT_BLOCKED_KEYWORDS),
            own_author_identifiers="",
            run_time="09:30",
        )
        return self.repo.create_settings(settings)

    def update_settings(self, payload) -> EngagementSetting:
        settings = self.get_or_create_settings()

        if payload.enabled is not None:
            settings.enabled = bool(payload.enabled)
        if payload.require_review is not None:
            settings.require_review = bool(payload.require_review)
        if payload.auto_post_enabled is not None:
            settings.auto_post_enabled = bool(payload.auto_post_enabled)

        if payload.posts_to_search_per_day is not None:
            settings.posts_to_search_per_day = int(payload.posts_to_search_per_day)
        if payload.comments_per_day is not None:
            settings.comments_per_day = int(payload.comments_per_day)
        if payload.min_reactions is not None:
            settings.min_reactions = int(payload.min_reactions)
        if payload.author_cooldown_hours is not None:
            settings.author_cooldown_hours = int(payload.author_cooldown_hours)

        if payload.style is not None:
            settings.style = self._normalize_style(payload.style)
        if payload.topics is not None:
            settings.topics = self._list_to_csv(payload.topics)
        if getattr(payload, "topic_configs", None) is not None:
            raw = [item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in payload.topic_configs]
            settings.topic_configs_json = self._topic_configs_to_json(raw)
            settings.topics = self._list_to_csv([item["topic"] for item in self._topic_configs_from_json(settings.topic_configs_json)])
        if payload.blocked_keywords is not None:
            settings.blocked_keywords = self._list_to_csv(payload.blocked_keywords)
        if payload.own_author_identifiers is not None:
            settings.own_author_identifiers = self._list_to_csv(payload.own_author_identifiers)
        if payload.run_time is not None:
            settings.run_time = self._parse_run_time(payload.run_time)

        return self.repo.update_settings(settings)

    def to_settings_read(self, settings: EngagementSetting) -> dict:
        topic_configs = self._topic_configs_from_json(getattr(settings, "topic_configs_json", ""))
        topics = self._csv_to_list(settings.topics)
        if not topic_configs and topics:
            topic_configs = [self._normalize_topic_config({"topic": topic, "style": settings.style, "min_reactions": settings.min_reactions}) for topic in topics]
        data = {
            "id": settings.id,
            "enabled": settings.enabled,
            "require_review": settings.require_review,
            "auto_post_enabled": settings.auto_post_enabled,
            "posts_to_search_per_day": settings.posts_to_search_per_day,
            "comments_per_day": settings.comments_per_day,
            "min_reactions": settings.min_reactions,
            "author_cooldown_hours": settings.author_cooldown_hours,
            "style": settings.style,
            "topics": topics,
            "topic_configs": topic_configs,
            "blocked_keywords": self._csv_to_list(settings.blocked_keywords),
            "own_author_identifiers": self._csv_to_list(settings.own_author_identifiers),
            "run_time": settings.run_time,
            "created_at": settings.created_at,
            "updated_at": settings.updated_at,
        }
        return data

    @staticmethod
    def _is_english(language: str | None) -> bool:
        if not language:
            return True
        return language.lower().startswith("en")

    @staticmethod
    def _is_recent(published_at: datetime | None) -> bool:
        if published_at is None:
            return True
        if published_at.tzinfo is not None:
            published_at = published_at.astimezone(tz=None).replace(tzinfo=None)
        return published_at >= datetime.utcnow() - timedelta(hours=24)

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        lowered = (text or "").lower()
        return any(keyword.lower() in lowered for keyword in keywords)

    def _select_topic(self, content: str, topics: list[str]) -> str | None:
        lowered = (content or "").lower()
        scored: list[tuple[int, str]] = []
        for topic in topics:
            terms = [t for t in re.split(r"[/\s]+", topic.lower()) if t]
            score = sum(1 for term in terms if term in lowered)
            if score > 0:
                scored.append((score, topic))
        if not scored:
            return None
        scored.sort(reverse=True)
        return scored[0][1]

    def _render_comment_prompt(self, post_content: str, style: str) -> tuple[str, str]:
        style_key = self._normalize_style(style)
        style_prompt = STYLE_PROMPTS[style_key]

        user_prompt = (
            "Read the LinkedIn post below and write one comment.\n"
            "Rules:\n"
            "- Maximum 70 words\n"
            "- No emojis\n"
            "- No generic praise\n"
            "- Add concrete technical value\n"
            "- Do not repeat the post verbatim\n"
            "- End with a thoughtful question when appropriate\n\n"
            f"Post:\n{post_content}"
        )
        system_prompt = (
            "You are a senior engineering leader writing authentic LinkedIn comments. "
            f"{style_prompt}"
        )
        return user_prompt, system_prompt

    def _generate_comment(self, post_content: str, style: str) -> str:
        prompt, system_prompt = self._render_comment_prompt(post_content, style)
        result = self._get_ai_client().generate_post(prompt, system_prompt)
        comment = (result.get("content") or "").strip()

        if not comment:
            raise ValueError("AI generated an empty comment.")
        if self._word_count(comment) > 70:
            words = [token for token in comment.split() if token.strip()]
            comment = " ".join(words[:70]).strip()
            if comment and comment[-1] not in ".!?":
                comment = f"{comment}."
        if self._contains_emoji(comment):
            raise ValueError("Generated comment contains emoji; regenerate required.")

        return comment

    @staticmethod
    def _extract_linkedin_comment_id(response: dict) -> str | None:
        if not isinstance(response, dict):
            return None
        value = response.get("id") or response.get("comment")
        return str(value) if value else None

    def _get_valid_access_token(self, account):
        if account is None:
            return None

        access_token = TokenService.decrypt(account.access_token)
        expires_at = account.expires_at
        if expires_at is not None and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)

        if expires_at is not None and expires_at <= datetime.utcnow():
            refresh_token = TokenService.decrypt(account.refresh_token)
            if not refresh_token:
                raise ValueError("LinkedIn access token expired and no refresh token is available.")
            refresh_resp = self.linkedin_client.refresh_access_token(refresh_token)
            new_access_token = refresh_resp.get("access_token")
            if not new_access_token:
                raise ValueError("LinkedIn token refresh did not return access token.")
            new_refresh_token = refresh_resp.get("refresh_token") or refresh_token
            expires_in = int(refresh_resp.get("expires_in") or 3600)
            account.access_token = TokenService.encrypt(new_access_token)
            account.refresh_token = TokenService.encrypt(new_refresh_token)
            account.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            self.db.commit()
            access_token = new_access_token

        return access_token

    def _get_latest_linkedin_account(self):
        account = self.account_repo.get_latest()
        if account is None:
            raise ValueError("No LinkedIn account configured.")
        return account

    def _get_optional_access_token(self) -> str | None:
        account = self.account_repo.get_latest()
        if account is None:
            return None
        try:
            return self._get_valid_access_token(account)
        except Exception:
            return None

    @staticmethod
    def _post_urn_from_url(url: str) -> str | None:
        if not url:
            return None
        match = re.search(r"urn:li:(share|ugcPost):[0-9]+", url)
        if match:
            return match.group(0)
        trailing = re.search(r"([0-9]{10,})/?$", url)
        if trailing:
            return f"urn:li:share:{trailing.group(1)}"
        return None

    def _validate_post_target(
        self,
        post_url: str,
        post_urn: str | None,
        access_token: str | None,
    ) -> tuple[bool, str, str | None]:
        resolved_urn = (post_urn or self._post_urn_from_url(post_url) or "").strip() or None
        if not resolved_urn:
            return False, "Invalid or missing LinkedIn post URL/URN.", None

        if access_token:
            try:
                if not self.linkedin_client.is_post_accessible(access_token, resolved_urn):
                    return False, "Invalid or inaccessible post URL/URN.", resolved_urn
            except Exception as exc:
                return False, f"Unable to validate post accessibility: {exc}", resolved_urn

        return True, "", resolved_urn

    def post_comment(self, history: EngagementCommentHistory, comment_text: str) -> EngagementCommentHistory:
        account = self._get_latest_linkedin_account()
        access_token = self._get_valid_access_token(account)
        if not access_token:
            raise ValueError("No LinkedIn access token is available.")

        post_urn = history.post_urn or self._post_urn_from_url(history.post_url)
        if not post_urn:
            raise ValueError("Cannot post comment: missing LinkedIn post URN.")

        author_urn = f"urn:li:person:{account.provider_user_id}"
        response = self.linkedin_client.comment_on_post(
            access_token=access_token,
            post_urn=post_urn,
            author_urn=author_urn,
            comment_text=comment_text,
        )

        history.post_urn = post_urn
        history.posted_comment = comment_text
        history.linkedin_comment_id = self._extract_linkedin_comment_id(response)
        history.posted_at = datetime.utcnow().replace(microsecond=0)
        history.status = "POSTED" if history.status == "APPROVED" else "AUTO_POSTED"
        history.skip_reason = None
        return self.repo.update_history(history)

    def _should_skip(
        self,
        candidate,
        settings: EngagementSetting,
        topics: list[str],
        blocked_keywords: list[str],
        own_ids: list[str],
        min_reactions_override: int | None = None,
        forced_topics: list[str] | None = None,
    ) -> tuple[bool, str, str | None, int]:
        content = (candidate.post_content or "").strip()
        if not content:
            return True, "Empty post content.", None, 0

        if candidate.is_company_page:
            return True, "Company page post.", None, 0
        if candidate.is_sponsored:
            return True, "Sponsored post.", None, 0
        if candidate.is_recruiter:
            return True, "Recruiter post.", None, 0
        if candidate.is_repost:
            return True, "Repost skipped by guardrail.", None, 0

        if not self._is_recent(candidate.post_published_at):
            return True, "Post is older than 24 hours.", None, 0
        min_reactions = int(settings.min_reactions) if min_reactions_override is None else int(min_reactions_override)
        if int(candidate.post_reaction_count or 0) < min_reactions:
            return True, "Reactions below threshold.", None, 0
        if not self._is_english(candidate.post_language):
            return True, "Non-English post.", None, 0

        if self.repo.exists_for_post(candidate.post_url):
            return True, "Already commented or queued for this post.", None, 0

        author = (candidate.post_author or "").strip()
        if author and any(identity.lower() in author.lower() for identity in own_ids):
            return True, "Own post skipped.", None, 0

        if self.repo.author_commented_recently(author, int(settings.author_cooldown_hours)):
            return True, "Author cooldown active.", None, 0

        lowered = content.lower()
        if any(keyword.lower() in lowered for keyword in blocked_keywords):
            return True, "Blocked by smart rule keyword.", None, 0

        selected_topic = self._select_topic(content, forced_topics or topics)
        if not selected_topic:
            return True, "No relevant tracked topic.", None, 0

        relevance = sum(1 for term in re.split(r"[/\s]+", selected_topic.lower()) if term and term in lowered)
        return False, "", selected_topic, relevance

    def scan_candidates(self, payload) -> dict:
        settings = self.get_or_create_settings()
        style = self._normalize_style(payload.style or settings.style)
        topics = self._csv_to_list(settings.topics) or DEFAULT_TOPICS
        blocked_keywords = self._csv_to_list(settings.blocked_keywords) or DEFAULT_BLOCKED_KEYWORDS
        own_ids = self._csv_to_list(settings.own_author_identifiers)
        access_token = self._get_optional_access_token()

        searched = 0
        relevant = 0
        queued_for_review = 0
        posted = 0
        skipped = 0

        posted_today = self.repo.count_posted_today()
        comment_budget = max(0, int(settings.comments_per_day) - int(posted_today))

        limit = min(int(settings.posts_to_search_per_day), len(payload.candidates))
        for candidate in payload.candidates[:limit]:
            searched += 1

            target_ok, target_reason, resolved_urn = self._validate_post_target(
                candidate.post_url,
                candidate.post_urn,
                access_token,
            )

            if not target_ok:
                history = EngagementCommentHistory(
                    post_url=candidate.post_url,
                    post_urn=resolved_urn,
                    post_author=(candidate.post_author or "").strip() or None,
                    post_language=candidate.post_language,
                    post_content=candidate.post_content,
                    post_published_at=candidate.post_published_at,
                    post_reaction_count=int(candidate.post_reaction_count or 0),
                    topic="unmatched",
                    style=style,
                    relevance_score=0,
                    status="SKIPPED",
                    skip_reason=target_reason,
                    is_company_page=bool(candidate.is_company_page),
                    is_sponsored=bool(candidate.is_sponsored),
                    is_recruiter=bool(candidate.is_recruiter),
                    is_repost=bool(candidate.is_repost),
                )
                self.repo.create_history(history)
                skipped += 1
                continue

            candidate.post_urn = resolved_urn

            should_skip, reason, topic, relevance = self._should_skip(
                candidate,
                settings,
                topics,
                blocked_keywords,
                own_ids,
            )

            history = EngagementCommentHistory(
                post_url=candidate.post_url,
                post_urn=candidate.post_urn,
                post_author=(candidate.post_author or "").strip() or None,
                post_language=candidate.post_language,
                post_content=candidate.post_content,
                post_published_at=candidate.post_published_at,
                post_reaction_count=int(candidate.post_reaction_count or 0),
                topic=topic or "unmatched",
                style=style,
                relevance_score=int(relevance or 0),
                status="SKIPPED" if should_skip else "REVIEW_PENDING",
                skip_reason=reason or None,
                is_company_page=bool(candidate.is_company_page),
                is_sponsored=bool(candidate.is_sponsored),
                is_recruiter=bool(candidate.is_recruiter),
                is_repost=bool(candidate.is_repost),
            )

            if should_skip:
                self.repo.create_history(history)
                skipped += 1
                continue

            relevant += 1
            if comment_budget <= 0:
                history.status = "SKIPPED"
                history.skip_reason = "Daily comment limit reached."
                self.repo.create_history(history)
                skipped += 1
                continue

            try:
                generated = self._generate_comment(candidate.post_content, style)
                history.generated_comment = generated
                history.posted_comment = generated

                if payload.auto_post and settings.auto_post_enabled and not settings.require_review:
                    created = self.repo.create_history(history)
                    self.post_comment(created, generated)
                    posted += 1
                else:
                    created = self.repo.create_history(history)
                    created.status = "REVIEW_PENDING"
                    self.repo.update_history(created)
                    queued_for_review += 1
            except Exception as exc:
                logger.exception("Engagement comment generation failed for post: %s", candidate.post_url)
                history.status = "FAILED"
                history.skip_reason = str(exc)
                self.repo.create_history(history)
                skipped += 1
                continue

            comment_budget -= 1

        return {
            "searched": searched,
            "relevant": relevant,
            "queued_for_review": queued_for_review,
            "posted": posted,
            "skipped": skipped,
        }

    def scan_direct_from_linkedin(self, topic_configs: list | None = None) -> dict:
        settings = self.get_or_create_settings()
        account = self._get_latest_linkedin_account()
        access_token = self._get_valid_access_token(account)
        if not access_token:
            raise ValueError("No LinkedIn access token is available.")

        stored_topic_configs = self._topic_configs_from_json(getattr(settings, "topic_configs_json", ""))
        raw_topic_configs = topic_configs if topic_configs is not None else stored_topic_configs
        if not raw_topic_configs:
            raw_topic_configs = [{"topic": topic} for topic in (self._csv_to_list(settings.topics) or DEFAULT_TOPICS)]

        normalized_configs = [
            self._normalize_topic_config(item.model_dump() if hasattr(item, "model_dump") else dict(item))
            for item in raw_topic_configs
        ]

        blocked_keywords = self._csv_to_list(settings.blocked_keywords) or DEFAULT_BLOCKED_KEYWORDS
        own_ids = self._csv_to_list(settings.own_author_identifiers)

        searched = 0
        relevant = 0
        queued_for_review = 0
        posted = 0
        skipped = 0
        searched_by_topic: dict[str, int] = {}

        posted_today = self.repo.count_posted_today()
        daily_budget = max(0, int(settings.comments_per_day) - int(posted_today))

        for config in normalized_configs:
            if daily_budget <= 0:
                break

            topic = config["topic"]
            search_limit = min(int(config["posts_to_search"]), int(settings.posts_to_search_per_day))
            rows = self.linkedin_client.search_posts_by_topic(access_token, topic, search_limit)
            searched_by_topic[topic] = len(rows)

            topic_budget = min(int(config["comments_per_run"]), daily_budget)
            for row in rows:
                if topic_budget <= 0 or daily_budget <= 0:
                    break

                candidate = type("Candidate", (), {
                    "post_url": row.get("post_url", ""),
                    "post_content": row.get("post_content", ""),
                    "post_author": row.get("post_author", ""),
                    "post_urn": row.get("post_urn"),
                    "post_language": row.get("post_language", "en"),
                    "post_published_at": None,
                    "post_reaction_count": int(row.get("post_reaction_count", 0) or 0),
                    "is_company_page": bool(row.get("is_company_page", False)),
                    "is_sponsored": bool(row.get("is_sponsored", False)),
                    "is_recruiter": bool(row.get("is_recruiter", False)),
                    "is_repost": bool(row.get("is_repost", False)),
                })

                searched += 1

                target_ok, target_reason, resolved_urn = self._validate_post_target(
                    candidate.post_url,
                    candidate.post_urn,
                    access_token,
                )

                if not target_ok:
                    history = EngagementCommentHistory(
                        post_url=candidate.post_url,
                        post_urn=resolved_urn,
                        post_author=(candidate.post_author or "").strip() or None,
                        post_language=candidate.post_language,
                        post_content=candidate.post_content,
                        post_published_at=candidate.post_published_at,
                        post_reaction_count=int(candidate.post_reaction_count or 0),
                        topic=topic,
                        style=config["style"],
                        relevance_score=0,
                        status="SKIPPED",
                        skip_reason=target_reason,
                        is_company_page=bool(candidate.is_company_page),
                        is_sponsored=bool(candidate.is_sponsored),
                        is_recruiter=bool(candidate.is_recruiter),
                        is_repost=bool(candidate.is_repost),
                    )
                    self.repo.create_history(history)
                    skipped += 1
                    continue

                candidate.post_urn = resolved_urn

                should_skip, reason, selected_topic, relevance_score = self._should_skip(
                    candidate,
                    settings,
                    [topic],
                    blocked_keywords,
                    own_ids,
                    min_reactions_override=int(config["min_reactions"]),
                    forced_topics=[topic],
                )

                history = EngagementCommentHistory(
                    post_url=candidate.post_url,
                    post_urn=candidate.post_urn,
                    post_author=(candidate.post_author or "").strip() or None,
                    post_language=candidate.post_language,
                    post_content=candidate.post_content,
                    post_published_at=candidate.post_published_at,
                    post_reaction_count=int(candidate.post_reaction_count or 0),
                    topic=selected_topic or topic,
                    style=config["style"],
                    relevance_score=int(relevance_score or 0),
                    status="SKIPPED" if should_skip else "REVIEW_PENDING",
                    skip_reason=reason or None,
                    is_company_page=bool(candidate.is_company_page),
                    is_sponsored=bool(candidate.is_sponsored),
                    is_recruiter=bool(candidate.is_recruiter),
                    is_repost=bool(candidate.is_repost),
                )

                if should_skip:
                    self.repo.create_history(history)
                    skipped += 1
                    continue

                relevant += 1
                try:
                    generated = self._generate_comment(candidate.post_content, config["style"])
                    history.generated_comment = generated
                    history.posted_comment = generated

                    post_now = bool(config["auto_post_enabled"]) and not bool(config["require_review"]) and settings.auto_post_enabled
                    if post_now:
                        created = self.repo.create_history(history)
                        self.post_comment(created, generated)
                        posted += 1
                    else:
                        created = self.repo.create_history(history)
                        created.status = "REVIEW_PENDING"
                        self.repo.update_history(created)
                        queued_for_review += 1
                except Exception as exc:
                    logger.exception("Direct engagement generation failed for topic=%s post=%s", topic, candidate.post_url)
                    history.status = "FAILED"
                    history.skip_reason = str(exc)
                    self.repo.create_history(history)
                    skipped += 1
                    continue

                topic_budget -= 1
                daily_budget -= 1

        return {
            "searched": searched,
            "relevant": relevant,
            "queued_for_review": queued_for_review,
            "posted": posted,
            "skipped": skipped,
            "searched_by_topic": searched_by_topic,
        }

    def list_comments(self, status: str | None = None, limit: int = 100) -> list[EngagementCommentHistory]:
        return self.repo.list_history(status=status, limit=limit)

    def approve_comment(self, history_id: int, edited_comment: str | None = None, post_now: bool = True) -> EngagementCommentHistory:
        history = self.repo.get_history_by_id(history_id)
        if history is None:
            raise ValueError("Engagement comment not found.")

        if history.status not in {"REVIEW_PENDING", "FAILED", "APPROVED"}:
            raise ValueError("Only review-pending comments can be approved.")

        final_comment = (edited_comment or history.generated_comment or "").strip()
        if not final_comment:
            raise ValueError("Final comment text is empty.")

        history.status = "APPROVED"
        history.posted_comment = final_comment
        history.skip_reason = None
        history = self.repo.update_history(history)

        if post_now:
            try:
                history = self.post_comment(history, final_comment)
            except Exception as exc:
                history.status = "APPROVED"
                history.skip_reason = f"Post failed: {exc}"
                history = self.repo.update_history(history)

        return history

    def skip_comment(self, history_id: int, reason: str | None = None) -> EngagementCommentHistory:
        history = self.repo.get_history_by_id(history_id)
        if history is None:
            raise ValueError("Engagement comment not found.")

        history.status = "SKIPPED"
        history.skip_reason = (reason or "Skipped by reviewer.").strip()
        return self.repo.update_history(history)

    def analytics(self, days: int = 1) -> dict:
        return self.repo.analytics_summary(days=days)

    @staticmethod
    def _candidate_obj_from_dict(data: dict):
        class Obj:
            def __init__(self, row):
                self.post_url = row.get("post_url", "")
                self.post_content = row.get("post_content", "")
                self.post_author = row.get("post_author", "")
                self.post_urn = row.get("post_urn")
                self.post_language = row.get("post_language", "en")
                value = row.get("post_published_at")
                self.post_published_at = datetime.fromisoformat(value) if value else None
                self.post_reaction_count = int(row.get("post_reaction_count", 0) or 0)
                self.is_company_page = bool(row.get("is_company_page", False))
                self.is_sponsored = bool(row.get("is_sponsored", False))
                self.is_recruiter = bool(row.get("is_recruiter", False))
                self.is_repost = bool(row.get("is_repost", False))

        return Obj(data)

    @staticmethod
    def _load_candidate_rows(path: Path) -> list[dict]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else raw.get("candidates", [])
        return [row for row in rows if isinstance(row, dict)]

    @staticmethod
    def _topic_names_from_configs(topic_configs: list | None) -> list[str]:
        if not topic_configs:
            return []
        topics: list[str] = []
        for item in topic_configs:
            value = item.model_dump() if hasattr(item, "model_dump") else dict(item)
            topic = str(value.get("topic") or "").strip()
            if topic:
                topics.append(topic)
        return topics

    @staticmethod
    def _filter_candidate_rows_by_topics(rows: list[dict], topics: list[str]) -> list[dict]:
        normalized = [topic.lower().strip() for topic in topics if str(topic).strip()]
        if not normalized:
            return rows

        filtered: list[dict] = []
        for row in rows:
            text = f"{row.get('post_content', '')} {row.get('post_author', '')}".lower()
            if any(topic in text for topic in normalized):
                filtered.append(row)
        return filtered

    def scan_from_collector(self, topic_configs: list | None = None) -> dict:
        settings = self.get_or_create_settings()
        topic_names = self._topic_names_from_configs(topic_configs)

        candidate_paths = [
            Path(__file__).resolve().parents[2] / "data" / "engagement_candidates.json",
            Path(__file__).resolve().parents[2] / "data" / "collector" / "engagement_candidates.json",
        ]

        selected_rows: list[dict] = []
        for path in candidate_paths:
            if not path.exists():
                continue
            try:
                rows = self._load_candidate_rows(path)
            except Exception:
                logger.exception("Failed reading collector candidates from %s", path)
                continue
            if rows:
                selected_rows = rows
                break

        if not selected_rows:
            return {
                "searched": 0,
                "relevant": 0,
                "queued_for_review": 0,
                "posted": 0,
                "skipped": 0,
            }

        filtered_rows = self._filter_candidate_rows_by_topics(selected_rows, topic_names)
        payload = type("Payload", (), {
            "candidates": [self._candidate_obj_from_dict(item) for item in filtered_rows],
            "style": settings.style,
            "auto_post": settings.auto_post_enabled and not settings.require_review,
        })
        return self.scan_candidates(payload)

    def run_daily_scan(self) -> dict:
        settings = self.get_or_create_settings()
        if not settings.enabled:
            return {
                "searched": 0,
                "relevant": 0,
                "queued_for_review": 0,
                "posted": 0,
                "skipped": 0,
            }

        candidates_path = Path(__file__).resolve().parents[2] / "data" / "engagement_candidates.json"
        if not candidates_path.exists():
            logger.info("Daily engagement scan skipped: %s not found.", candidates_path)
            return {
                "searched": 0,
                "relevant": 0,
                "queued_for_review": 0,
                "posted": 0,
                "skipped": 0,
            }

        candidates = self._load_candidate_rows(candidates_path)

        payload = type("Payload", (), {
            "candidates": [self._candidate_obj_from_dict(item) for item in candidates],
            "style": settings.style,
            "auto_post": settings.auto_post_enabled and not settings.require_review,
        })
        return self.scan_candidates(payload)
