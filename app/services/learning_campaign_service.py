from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from app.db.models.learning_campaign import LearningCampaign
from app.db.models.learning_campaign_item import LearningCampaignItem
from app.db.models.topic import Topic
from app.logger import logger
from app.models.topic import Category
from app.models.topic import Priority
from app.models.topic import TopicStatus
from app.realtime import publish_event
from app.repositories.learning_campaign_repository import LearningCampaignRepository
from app.repositories.topic_repository import TopicRepository
from app.services.generation_service import GenerationService
from app.services.publish_service import PublishService


class LearningCampaignService:
    REQUIRED_COLUMNS = ["topic"]
    COLUMN_ALIASES = {
        "day": "day",
        "series": "series",
        "phase": "phase",
        "category": "category",
        "topic": "topic",
        "subtopic": "subtopic",
        "primary goal": "primary_goal",
        "primary goal (save / share / comment)": "primary_goal",
        "hook": "hook",
        "story / problem": "story_problem",
        "story/problem": "story_problem",
        "teaching points": "teaching_points",
        "enterprise / fde angle": "enterprise_fde_angle",
        "enterprise/fde angle": "enterprise_fde_angle",
        "suggested visual": "suggested_visual",
        "difficulty": "difficulty",
        "target audience": "target_audience",
        "what to cover": "what_to_cover",
        "key takeaway": "key_takeaway",
        "suggested hook": "suggested_hook",
        "post format": "post_format",
        "suggested diagram/visual": "suggested_visual",
        "code demo": "code_demo",
        "real world example": "real_world_example",
        "real-world example": "real_world_example",
        "opinion": "opinion",
        "call to action": "call_to_action",
        "cta": "call_to_action",
        "hashtags": "hashtags",
        "keywords": "keywords",
        "estimated read time": "estimated_read_time",
        "reference/resource": "reference_resource",
        "ai studio prompt": "ai_studio_prompt",
        "status": "status",
        "priority": "priority",
        "audience": "target_audience",
        "recommended format": "recommended_format",
    }
    VISUAL_STYLES = {
        "auto",
        "flow_diagram",
        "animated_infographic",
        "architecture_diagram",
    }

    def __init__(self, db_session):
        self.db = db_session
        self.repo = LearningCampaignRepository(db_session)
        self.topic_repo = TopicRepository(db_session)
        self.generation_service = GenerationService(self.topic_repo, db_session)
        self.publish_service = PublishService(db_session)

    @staticmethod
    def _parse_publish_time(raw: str) -> time:
        try:
            hour, minute = raw.split(":")
            h = int(hour)
            m = int(minute)
        except Exception as exc:
            raise ValueError("publish_time must be in HH:MM format.") from exc
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError("publish_time must be between 00:00 and 23:59.")
        return time(hour=h, minute=m)

    @staticmethod
    def _parse_start_date(raw: str | None) -> date:
        if not raw:
            return datetime.now().date()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("start_date must be in YYYY-MM-DD format.") from exc

    @staticmethod
    def _to_utc_naive(local_date: date, local_time: time, tz_name: str) -> datetime:
        zone = ZoneInfo(tz_name)
        local_dt = datetime.combine(local_date, local_time).replace(tzinfo=zone)
        return local_dt.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _sanitize_text(value) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def _normalize_column_name(name: str) -> str:
        return " ".join(str(name or "").strip().lower().split())

    def _normalized_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        mapped_columns: dict[str, str] = {}
        for original in dataframe.columns:
            normalized = self._normalize_column_name(original)
            canonical = self.COLUMN_ALIASES.get(normalized, normalized.replace(" ", "_"))
            mapped_columns[original] = canonical
        return dataframe.rename(columns=mapped_columns)

    @staticmethod
    def _extract_config_text(config_dataframe: pd.DataFrame) -> str:
        normalized = config_dataframe.copy()
        normalized.columns = [str(column).strip() for column in normalized.columns]

        if len(normalized.columns) >= 2:
            key_col = normalized.columns[0]
            value_col = normalized.columns[1]
            lines = []
            for _, row in normalized.iterrows():
                key = str(row.get(key_col) or "").strip()
                value = str(row.get(value_col) or "").strip()
                if key and value:
                    lines.append(f"{key}: {value}")
            if lines:
                return "\n".join(lines)

        values = []
        for _, row in normalized.iterrows():
            for value in row.tolist():
                text = str(value).strip()
                if text:
                    values.append(text)
        return "\n".join(values)

    @staticmethod
    def _to_day_number(value, fallback: int) -> int:
        if pd.isna(value):
            return fallback
        raw = str(value).strip().lower()
        if raw.startswith("day "):
            raw = raw[4:]
        try:
            parsed = int(float(raw))
            return parsed if parsed > 0 else fallback
        except Exception:
            return fallback

    @staticmethod
    def _is_active_planned_row(status_raw: str) -> bool:
        status = (status_raw or "").strip().lower()
        if not status:
            return True
        return status in {"planned", "plan", "pending", "todo", "to do", "ready"}

    @staticmethod
    def _resolve_priority(priority_raw: str, difficulty_raw: str) -> Priority:
        priority_text = (priority_raw or "").strip().upper()
        if priority_text:
            try:
                return Priority(priority_text)
            except Exception:
                pass

        difficulty = (difficulty_raw or "").strip().lower()
        if difficulty in {"advanced", "expert", "hard"}:
            return Priority.HIGH
        if difficulty in {"intermediate", "medium"}:
            return Priority.MEDIUM
        return Priority.LOW

    @staticmethod
    def _resolve_category(category_raw: str) -> Category:
        category_text = (category_raw or "").strip().upper()
        if category_text:
            try:
                return Category(category_text)
            except Exception:
                pass

        lowered = (category_raw or "").strip().lower()
        if "ai" in lowered or "ml" in lowered:
            return Category.AI
        if "devops" in lowered:
            return Category.DEVOPS
        if "cloud" in lowered:
            return Category.CLOUD
        if "python" in lowered:
            return Category.PYTHON
        if "data" in lowered:
            return Category.DATA
        if "career" in lowered:
            return Category.CAREER
        if "linkedin" in lowered:
            return Category.LINKEDIN
        if "automation" in lowered:
            return Category.AUTOMATION
        if "productivity" in lowered:
            return Category.PRODUCTIVITY
        return Category.GENERAL

    @staticmethod
    def _compose_topic_title(topic: str, subtopic: str) -> str:
        if topic and subtopic:
            return f"{topic} - {subtopic}"
        return topic or subtopic

    @staticmethod
    def _compose_row_prompt(row: dict, config_text: str | None = None) -> str:
        sections: list[str] = []

        if config_text:
            sections.append("AI Studio Config Guidance:\n" + config_text.strip())

        if row.get("ai_studio_prompt"):
            sections.append("Row Prompt Override:\n" + row["ai_studio_prompt"].strip())

        metadata_lines = [
            f"Day: {row.get('day_number', '')}",
            f"Series: {row.get('series', '')}",
            f"Phase: {row.get('phase', '')}",
            f"Category: {row.get('category_raw', '')}",
            f"Topic: {row.get('topic', '')}",
            f"Primary Goal: {row.get('primary_goal', '')}",
            f"Hook: {row.get('hook', '')}",
            f"Story / Problem: {row.get('story_problem', '')}",
            f"Teaching Points: {row.get('teaching_points', '')}",
            f"Enterprise / FDE Angle: {row.get('enterprise_fde_angle', '')}",
            f"Suggested Visual: {row.get('suggested_visual', '')}",
            f"Code Demo: {row.get('code_demo', '')}",
            f"Real-world Example: {row.get('real_world_example', '')}",
            f"Opinion: {row.get('opinion', '')}",
            f"CTA: {row.get('call_to_action', '')}",
            f"Recommended Format: {row.get('recommended_format', '')}",
            f"Difficulty: {row.get('difficulty_raw', '')}",
            f"Audience: {row.get('target_audience', '')}",
            f"Keywords: {row.get('keywords', '')}",
            f"Hashtags: {row.get('hashtags', '')}",
            f"Estimated Read Time: {row.get('estimated_read_time', '')}",
            f"Reference/Resource: {row.get('reference_resource', '')}",
        ]
        sections.append("Use the following metadata to write the post:\n" + "\n".join(metadata_lines))

        if row.get("what_to_cover"):
            sections.append("What to Cover:\n" + row["what_to_cover"].strip())

        prompt_rules = [
            "Write a strong LinkedIn post optimized for engagement.",
            "Use the hook in the opening lines.",
            "Make it enterprise-first and practical.",
            "Use the teaching points and story/problem to structure the body.",
            "Tie the post to the real-world example and enterprise/FDE angle.",
            "End with the CTA and a discussion question if suitable.",
            "Keep the tone sharp, clear, credible, and specific.",
        ]
        sections.append("Requirements:\n" + "\n".join(f"- {rule}" for rule in prompt_rules))

        return "\n\n".join(part for part in sections if part.strip())

    @staticmethod
    def _compose_visual_hint(row: dict) -> str:
        parts: list[str] = []
        suggested_visual = (row.get("suggested_visual") or "").strip()
        post_format = (row.get("post_format") or "").strip()
        code_demo = (row.get("code_demo") or "").strip()
        real_world_example = (row.get("real_world_example") or "").strip()
        if suggested_visual:
            parts.append(f"Preferred visual: {suggested_visual}")
        if post_format:
            parts.append(f"Post format: {post_format}")
        if code_demo:
            parts.append(f"Code demo focus: {code_demo}")
        if real_world_example:
            parts.append(f"Real-world angle: {real_world_example}")
        return " | ".join(parts)

    @staticmethod
    def _build_image_style_hint(campaign: LearningCampaign, item: LearningCampaignItem) -> str:
        style_map = {
            "flow_diagram": "Use a clean flow-diagram style with steps, arrows, and minimal text.",
            "animated_infographic": "Use an animated-infographic look with icon-led story blocks and movement cues.",
            "architecture_diagram": "Use a modern system architecture diagram style with layered components and connectors.",
            "auto": "Auto-select the best visual style for the topic: flow diagram, architecture, or infographic.",
        }
        style_text = style_map.get((campaign.visual_style or "auto").strip().lower(), style_map["auto"])
        if item.visual_hint:
            return f"{style_text} {item.visual_hint}"
        return style_text

    @staticmethod
    def _ensure_quality(text: str, min_words: int, max_words: int) -> None:
        words = [token for token in (text or "").split() if token.strip()]
        count = len(words)
        if count < min_words:
            raise ValueError(f"Generated content too short ({count} words).")
        if count > max_words:
            raise ValueError(f"Generated content too long ({count} words).")
        if "?" not in text:
            raise ValueError("Generated content must include at least one engagement question.")

    def create_campaign_from_excel(
        self,
        name: str,
        file_path: Path,
        publish_time: str,
        timezone_name: str,
        start_date_raw: str | None,
        description: str | None = None,
        auto_approve: bool = True,
        auto_publish: bool = True,
        auto_generate_images: bool = True,
        image_count: int = 1,
        visual_style: str = "auto",
        max_attempts: int = 3,
        min_words: int = 120,
        max_words: int = 320,
    ) -> LearningCampaign:
        campaign_name = (name or "").strip()
        if not campaign_name:
            raise ValueError("Campaign name is required.")
        if self.repo.get_campaign_by_name(campaign_name):
            raise ValueError("Campaign name already exists.")

        publish_t = self._parse_publish_time(publish_time)
        start_d = self._parse_start_date(start_date_raw)

        try:
            ZoneInfo(timezone_name)
        except Exception as exc:
            raise ValueError("Invalid timezone.") from exc

        sheets = pd.read_excel(file_path, sheet_name=None)
        if not sheets:
            raise ValueError("Excel file is empty.")

        config_text = ""
        dataframes: list[pd.DataFrame] = []
        for sheet_name, sheet_dataframe in sheets.items():
            normalized_sheet = self._normalized_dataframe(sheet_dataframe)
            lowered_sheet_name = str(sheet_name).strip().lower()
            if lowered_sheet_name in {"ai_studio_config", "aistudio_config", "config"}:
                config_text = self._extract_config_text(sheet_dataframe)
                continue
            if "topic" in normalized_sheet.columns:
                dataframes.append(normalized_sheet)

        if not dataframes:
            first_sheet = next(iter(sheets.values()))
            dataframe = self._normalized_dataframe(first_sheet)
        else:
            dataframe = pd.concat(dataframes, ignore_index=True)

        for column in self.REQUIRED_COLUMNS:
            if column not in dataframe.columns:
                raise ValueError(f"Missing required column: {column}")

        campaign = LearningCampaign(
            name=campaign_name,
            description=(description or "").strip() or None,
            status="ACTIVE",
            timezone=timezone_name,
            publish_time=publish_time,
            start_date=start_d.isoformat(),
            auto_approve=bool(auto_approve),
            auto_publish=bool(auto_publish),
            auto_generate_images=bool(auto_generate_images),
            image_count=max(1, min(2, int(image_count))),
            visual_style=(visual_style or "auto").strip().lower(),
            max_attempts=max(1, int(max_attempts)),
            min_words=max(80, int(min_words)),
            max_words=max(160, int(max_words)),
        )
        if campaign.min_words >= campaign.max_words:
            raise ValueError("min_words must be lower than max_words.")
        if campaign.visual_style not in self.VISUAL_STYLES:
            raise ValueError("visual_style must be one of: auto, flow_diagram, animated_infographic, architecture_diagram.")

        campaign = self.repo.create_campaign(campaign)

        rows: list[dict] = []
        fallback_day = 0
        for source_index, row in dataframe.iterrows():
            topic_text = self._sanitize_text(row.get("topic"))
            subtopic_text = self._sanitize_text(row.get("subtopic"))
            combined_topic = self._compose_topic_title(topic_text, subtopic_text)
            if not combined_topic:
                continue

            status_text = self._sanitize_text(row.get("status"))
            if not self._is_active_planned_row(status_text):
                continue

            fallback_day += 1
            day_number = self._to_day_number(row.get("day"), fallback_day)
            rows.append(
                {
                    "source_index": int(source_index),
                    "day_number": day_number,
                    "topic": combined_topic,
                    "series": self._sanitize_text(row.get("series")),
                    "phase": self._sanitize_text(row.get("phase")),
                    "primary_goal": self._sanitize_text(row.get("primary_goal")),
                    "hook": self._sanitize_text(row.get("hook")) or self._sanitize_text(row.get("suggested_hook")),
                    "story_problem": self._sanitize_text(row.get("story_problem")),
                    "teaching_points": self._sanitize_text(row.get("teaching_points")),
                    "enterprise_fde_angle": self._sanitize_text(row.get("enterprise_fde_angle")),
                    "category_raw": self._sanitize_text(row.get("category")),
                    "priority_raw": self._sanitize_text(row.get("priority")),
                    "difficulty_raw": self._sanitize_text(row.get("difficulty")),
                    "suggested_visual": self._sanitize_text(row.get("suggested_visual")),
                    "post_format": self._sanitize_text(row.get("post_format")),
                    "code_demo": self._sanitize_text(row.get("code_demo")),
                    "real_world_example": self._sanitize_text(row.get("real_world_example")),
                    "opinion": self._sanitize_text(row.get("opinion")),
                    "call_to_action": self._sanitize_text(row.get("call_to_action")),
                    "recommended_format": self._sanitize_text(row.get("recommended_format")),
                    "target_audience": self._sanitize_text(row.get("target_audience")),
                    "keywords": self._sanitize_text(row.get("keywords")),
                    "hashtags": self._sanitize_text(row.get("hashtags")),
                    "estimated_read_time": self._sanitize_text(row.get("estimated_read_time")),
                    "reference_resource": self._sanitize_text(row.get("reference_resource")),
                    "ai_studio_prompt": self._sanitize_text(row.get("ai_studio_prompt")),
                }
            )

        rows.sort(key=lambda record: (record["day_number"], record["source_index"]))

        items: list[LearningCampaignItem] = []
        for ordered_index, record in enumerate(rows, start=1):
            topic_text = record["topic"]
            if not topic_text:
                continue
            category = self._resolve_category(record["category_raw"])
            priority = self._resolve_priority(record["priority_raw"], record["difficulty_raw"])

            local_date = start_d + timedelta(days=ordered_index - 1)
            scheduled_for = self._to_utc_naive(local_date, publish_t, timezone_name)

            items.append(
                LearningCampaignItem(
                    campaign_id=campaign.id,
                    day_number=ordered_index,
                    topic=topic_text,
                    prompt_brief=self._compose_row_prompt(record, config_text),
                    visual_hint=self._compose_visual_hint(record),
                    category=category,
                    priority=priority,
                    status="PENDING",
                    scheduled_for=scheduled_for,
                    attempts=0,
                )
            )

        if not items:
            raise ValueError("No valid topic rows found in Excel file.")

        self.repo.create_items(items)
        publish_event("campaign.updated", {"campaign_id": campaign.id, "status": campaign.status})
        return self.repo.get_campaign(campaign.id)

    def list_campaigns(self) -> list[LearningCampaign]:
        return self.repo.list_campaigns()

    def get_campaign(self, campaign_id: int) -> LearningCampaign | None:
        return self.repo.get_campaign(campaign_id)

    def list_campaign_items(self, campaign_id: int) -> list[LearningCampaignItem]:
        return self.repo.list_items_for_campaign(campaign_id)

    def set_campaign_status(self, campaign_id: int, status: str) -> LearningCampaign:
        campaign = self.repo.get_campaign(campaign_id)
        if campaign is None:
            raise ValueError("Campaign not found.")
        campaign.status = status
        campaign.last_error = None if status in {"ACTIVE", "PAUSED"} else campaign.last_error
        updated = self.repo.update_campaign(campaign)
        publish_event("campaign.updated", {"campaign_id": updated.id, "status": updated.status})
        return updated

    def _build_topic_title(self, item: LearningCampaignItem, campaign: LearningCampaign) -> str:
        base = item.topic.strip()
        return f"{base}"

    def _create_or_get_topic(self, item: LearningCampaignItem, campaign: LearningCampaign) -> Topic:
        if item.topic_id:
            existing = self.topic_repo.get_by_id(item.topic_id)
            if existing is not None:
                return existing

        title = self._build_topic_title(item, campaign)
        # Always create a dedicated topic for each campaign item.
        # Reusing by title can cross-link items across campaigns and overwrite statuses.
        topic = self.topic_repo.create(
            topic_text=title,
            category=item.category,
            priority=item.priority,
        )
        self.topic_repo.commit()
        self.topic_repo.refresh(topic)

        item.topic_id = topic.id
        self.repo.update_item(item)
        return topic

    def _process_item(self, item: LearningCampaignItem) -> None:
        campaign = self.repo.get_campaign(item.campaign_id)
        if campaign is None or campaign.status != "ACTIVE":
            return

        if self.repo.has_unpublished_previous(item.campaign_id, item.day_number):
            return

        item.status = "PROCESSING"
        item.last_error = None
        self.repo.update_item(item)

        try:
            topic = self._create_or_get_topic(item, campaign)

            generated = self.generation_service.generate_for_topic(
                topic,
                generate_images=campaign.auto_generate_images,
                image_count=campaign.image_count,
                image_style_hint=self._build_image_style_hint(campaign, item),
                prompt_override=item.prompt_brief,
                min_words=campaign.min_words,
                max_words=campaign.max_words,
            )
            if not generated:
                raise ValueError("Content generation failed for campaign item.")

            topic = self.topic_repo.get_by_id(topic.id)
            if topic is None or not topic.generated_post:
                raise ValueError("Generated topic content is missing.")

            self._ensure_quality(topic.generated_post, campaign.min_words, campaign.max_words)

            if campaign.auto_approve and topic.status != TopicStatus.APPROVED:
                self.topic_repo.approve(topic.id)

            if campaign.auto_publish:
                self.publish_service.publish_topic_now(topic.id)
                item.status = "PUBLISHED"
                item.published_at = datetime.utcnow().replace(microsecond=0)
            else:
                item.status = "GENERATED"

            item.last_error = None
            self.repo.update_item(item)

            publish_event(
                "campaign.item.updated",
                {
                    "campaign_id": campaign.id,
                    "item_id": item.id,
                    "status": item.status,
                    "day_number": item.day_number,
                },
            )
            publish_event("campaign.updated", {"campaign_id": campaign.id, "status": campaign.status})
        except Exception as exc:
            item.attempts += 1
            item.last_error = str(exc)
            if item.attempts >= campaign.max_attempts:
                item.status = "FAILED"
                campaign.status = "PAUSED"
                campaign.last_error = (
                    f"Campaign paused after failure on Day {item.day_number}: {str(exc)}"
                )
                self.repo.update_campaign(campaign)
            else:
                item.status = "RETRY"
                item.scheduled_for = datetime.utcnow() + timedelta(minutes=30)
            self.repo.update_item(item)
            logger.exception("Campaign item failed: campaign=%s day=%s", item.campaign_id, item.day_number)
            publish_event(
                "campaign.item.updated",
                {
                    "campaign_id": item.campaign_id,
                    "item_id": item.id,
                    "status": item.status,
                    "day_number": item.day_number,
                    "error": str(exc),
                },
            )
            publish_event("campaign.updated", {"campaign_id": item.campaign_id, "status": campaign.status})

    def process_due_items(self, limit: int = 5) -> int:
        now = datetime.utcnow()
        due_items = self.repo.get_due_items(now, limit=limit)
        processed = 0
        for item in due_items:
            before = item.status
            self._process_item(item)
            if before != "PUBLISHED" and item.status in {"PUBLISHED", "FAILED", "RETRY", "GENERATED"}:
                processed += 1
        return processed
