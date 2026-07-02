from __future__ import annotations

from pathlib import Path
import re
import uuid
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from app.ai.client import OpenAIClient
from app.config.settings import settings
from app.logger import logger
from app.models.topic import TopicStatus
from app.repositories.topic_repository import TopicRepository
from app.schemas.ingest import TrendingNewsItem
from app.services.publish_service import PublishService


class TrendingService:
    NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    ENGAGEMENT_RULES = {
        "discussion_starter": {
            "hook": "Open with a debatable question that invites comments.",
            "structure": "One strong viewpoint, two supporting arguments, and invite disagreement.",
            "cta": "Ask readers whether they agree/disagree and why.",
        },
        "how_to_playbook": {
            "hook": "Open with a practical implementation question.",
            "structure": "Use a numbered playbook format with concrete steps.",
            "cta": "Ask readers which step they will apply this week.",
        },
        "trend_radar": {
            "hook": "Open with a what-is-changing-fastest question.",
            "structure": "Summarize 3 trends and implications for teams.",
            "cta": "Ask which trend matters most this quarter.",
        },
        "case_study_breakdown": {
            "hook": "Open with a challenge-to-outcome question.",
            "structure": "Use context, action, result, and lesson sections.",
            "cta": "Ask if readers want a deeper case study breakdown.",
        },
        "cta_to_dm": {
            "hook": "Open with a pain-point question for target readers.",
            "structure": "Provide concise value bullets and practical outcomes.",
            "cta": "Ask readers to comment a keyword or DM for the full framework.",
        },
    }

    def __init__(self, db_session):
        self.db = db_session
        self.topic_repository = TopicRepository(db_session)
        self.ai_client = OpenAIClient()

    @staticmethod
    def _normalize_source(value: str | None) -> str | None:
        if not value:
            return None
        source = value.strip()
        if " - " in source:
            source = source.split(" - ")[-1].strip()
        return source or None

    def fetch_news(self, category: str, keyword: str | None, max_items: int) -> list[TrendingNewsItem]:
        query = category
        if keyword and keyword.strip():
            query = f"{query} {keyword.strip()}"

        url = self.NEWS_RSS_URL.format(query=quote_plus(query))

        with urlopen(url, timeout=20) as response:
            payload = response.read()

        root = ET.fromstring(payload)
        items: list[TrendingNewsItem] = []
        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            source = self._normalize_source(item.findtext("source"))
            published = (item.findtext("pubDate") or "").strip() or None

            if not title or not link:
                continue

            items.append(
                TrendingNewsItem(
                    title=title,
                    link=link,
                    source=source,
                    published=published,
                )
            )
            if len(items) >= max_items:
                break

        return items

    def _build_summary_prompt(
        self,
        category: str,
        items: list[TrendingNewsItem],
        engagement_type: str,
    ) -> str:
        engagement_type = engagement_type if engagement_type in self.ENGAGEMENT_RULES else "trend_radar"
        rules = self.ENGAGEMENT_RULES[engagement_type]
        lines = "\n".join(
            [f"- {item.title} ({item.source or 'Unknown source'}) - {item.link}" for item in items]
        )
        return (
            "Create one high-quality LinkedIn post draft with an executive-style cumulative summary.\n"
            f"Category: {category}\n"
            f"Engagement type: {engagement_type}\n"
            "Requirements:\n"
            "- opening line should be an engagement question\n"
            "- first sentence must be strong and suitable for bold formatting\n"
            "- 140 to 220 words\n"
            "- include 3 key trends and why they matter\n"
            "- include one concise call-to-action\n"
            "- include 4-8 hashtags with important domain keywords\n"
            "- keep a professional, practical tone\n\n"
            f"Hook rule: {rules['hook']}\n"
            f"Structure rule: {rules['structure']}\n"
            f"CTA rule: {rules['cta']}\n\n"
            "News inputs:\n"
            f"{lines}"
        )

    @staticmethod
    def _ensure_engagement_question(text: str, category: str, engagement_type: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return cleaned
        head = cleaned[:220]
        if "?" in head:
            return cleaned

        question_map = {
            "discussion_starter": f"Do you agree that {category} teams are over-optimizing tools and under-optimizing execution?",
            "how_to_playbook": f"How would you implement {category} in one practical sprint without overengineering?",
            "trend_radar": f"What is changing fastest in {category} that your team should act on this quarter?",
            "case_study_breakdown": f"What separates high-performing {category} rollouts from the ones that stall?",
            "cta_to_dm": f"Want a practical {category} framework you can apply this week?",
        }
        question = question_map.get(engagement_type, question_map["trend_radar"])
        return f"{question}\n\n{cleaned}"

    @staticmethod
    def _ensure_bold_first_sentence(text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return cleaned

        end_match = re.search(r"[.!?]", cleaned)
        if end_match:
            end_index = end_match.end()
        else:
            first_newline = cleaned.find("\n")
            end_index = first_newline if first_newline != -1 else min(len(cleaned), 140)

        first_sentence = cleaned[:end_index].strip()
        rest = cleaned[end_index:].lstrip()

        if first_sentence.startswith("**") and first_sentence.endswith("**"):
            return cleaned

        bolded = f"**{first_sentence}**"
        return f"{bolded}\n\n{rest}".strip()

    @staticmethod
    def _derive_keyword_hashtags(text: str, category: str, keyword: str | None) -> list[str]:
        normalized_text = (text or "").lower()

        # Domain keywords we always want to prioritize when present.
        candidates = {
            "ai": "#AI",
            "rag": "#RAG",
            "agent": "#AIAgents",
            "agents": "#AIAgents",
            "healthcare": "#Healthcare",
            "devops": "#DevOps",
            "cloud": "#CloudComputing",
            "enterprise": "#EnterpriseAI",
            "automation": "#Automation",
            "mcp": "#MCP",
        }

        hashtags: list[str] = []
        for token, tag in candidates.items():
            if token in normalized_text and tag not in hashtags:
                hashtags.append(tag)

        if keyword:
            for token in re.findall(r"[A-Za-z0-9]+", keyword):
                if len(token) >= 2:
                    dynamic_tag = f"#{token}"
                    if dynamic_tag not in hashtags:
                        hashtags.append(dynamic_tag)

        category_tag = f"#{category.replace(' ', '')}"
        if category_tag not in hashtags:
            hashtags.insert(0, category_tag)

        # Keep compact and readable.
        return hashtags[:8]

    def _apply_engagement_polish(
        self,
        text: str,
        category: str,
        keyword: str | None,
        engagement_type: str,
    ) -> str:
        polished = self._ensure_engagement_question(text, category, engagement_type)
        polished = self._ensure_bold_first_sentence(polished)

        hashtags = self._derive_keyword_hashtags(polished, category, keyword)
        if hashtags:
            if re.search(r"#[A-Za-z0-9_]+", polished):
                # Replace trailing hashtag line with improved tags.
                lines = polished.splitlines()
                while lines and lines[-1].strip().startswith("#"):
                    lines.pop()
                polished = "\n".join(lines).strip()
            polished = f"{polished}\n\n{' '.join(hashtags)}"

        return polished.strip()

    def _build_image_prompt(self, category: str, generated_post: str, index: int) -> str:
        return (
            f"Create a premium LinkedIn visual for {category} trends, variation {index}. "
            "Art direction: modern B2B editorial, minimal and clean, realistic or high-end vector style, strong composition. "
            "Use visual metaphors for trends and momentum. "
            "If text appears, keep it very short (max 3 words) and clearly legible. "
            "Avoid crowded infographic blocks, avoid cartoonish style, avoid dense typography, avoid logos/brand marks. "
            "Color palette: professional blue/neutral tones with subtle contrast accents. "
            f"Context: {generated_post[:450]}"
        )

    @staticmethod
    def _slugify(text: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
        return slug[:48] or "trend"

    def _save_images(self, topic_id: int, category: str, generated_post: str, image_count: int) -> list[str]:
        generated_dir = Path(__file__).resolve().parent.parent / "static" / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)

        urls: list[str] = []
        for idx in range(1, image_count + 1):
            prompt = self._build_image_prompt(category, generated_post, idx)
            image_bytes = self.ai_client.generate_image(prompt)
            filename = f"trend-{topic_id}-{self._slugify(category)}-{idx}-{uuid.uuid4().hex[:8]}.png"
            image_path = generated_dir / filename
            image_path.write_bytes(image_bytes)
            urls.append(f"http://{settings.host}:{settings.port}/static/generated/{filename}")

        return urls

    def generate_trending_topic(
        self,
        engagement_type: str,
        category,
        priority,
        keyword: str | None,
        max_items: int,
        image_count: int,
    ) -> dict:
        news_items = self.fetch_news(category.value, keyword, max_items)
        if not news_items:
            raise ValueError("No recent news items found for this category.")

        engagement_type = (engagement_type or "trend_radar").strip().lower()
        if engagement_type not in self.ENGAGEMENT_RULES:
            engagement_type = "trend_radar"

        prompt = self._build_summary_prompt(category.value, news_items, engagement_type)
        result = self.ai_client.generate_post(
            prompt,
            "You are a senior LinkedIn strategist focused on concise trend synthesis.",
        )
        generated_post = self._apply_engagement_polish(
            result["content"].strip(),
            category.value,
            keyword,
            engagement_type,
        )
        if not generated_post:
            raise ValueError("AI did not generate summary content.")

        base_topic_text = f"{category.value} viral trends digest"
        if keyword and keyword.strip():
            base_topic_text = f"{base_topic_text} - {keyword.strip()}"

        topic_text = base_topic_text
        attempt = 2
        while self.topic_repository.get_by_topic(topic_text):
            topic_text = f"{base_topic_text} #{attempt}"
            attempt += 1

        topic = self.topic_repository.create(
            topic_text=topic_text,
            category=category,
            priority=priority,
        )
        self.topic_repository.commit()
        self.topic_repository.refresh(topic)

        self.topic_repository.update_generated_post(
            topic.id,
            TopicStatus.READY_FOR_REVIEW,
            generated_post,
        )

        image_urls = self._save_images(topic.id, category.value, generated_post, image_count)

        auto_attached_media = False
        if image_urls:
            publish_service = PublishService(self.db)
            for image_url in image_urls:
                try:
                    publish_service.attach_media_to_topic(topic.id, image_url, mime_type="image/png")
                    auto_attached_media = True
                except Exception:
                    # Keep draft creation successful even if auto-attach cannot run.
                    logger.exception("Unable to auto-attach generated image for topic %s", topic.id)

        return {
            "success": True,
            "message": "Trending topic created with cumulative summary and generated images.",
            "topic_id": topic.id,
            "topic": topic.topic,
            "engagement_type": engagement_type,
            "category": category,
            "priority": priority,
            "generated_post": generated_post,
            "auto_attached_media": auto_attached_media,
            "image_urls": image_urls,
            "news_items": news_items,
        }
