"""
Generation Service

Handles generation, retry, history recording, and review state transitions.
"""

import json
import re
import time
from pathlib import Path
import uuid

from app.ai.client import OpenAIClient
from app.config.settings import settings
from app.models.topic import TopicStatus
from app.repositories.generation_history_repository import GenerationHistoryRepository
from app.repositories.topic_repository import TopicRepository
from app.services.publish_service import PublishService
from app.logger import logger


DEFAULT_TEMPLATES = {
    "story": "story.txt",
    "technical": "technical.txt",
    "leadership": "leadership.txt",
    "career": "career.txt",
    "devops": "devops.txt",
    "ai": "ai.txt",
}


ENGAGEMENT_RULES = {
    "discussion_starter": {
        "hook": "Open with a debatable question and invite viewpoints.",
        "structure": "Use one central opinion, two supporting points, and a discussion CTA.",
        "cta": "Ask readers to agree/disagree with reasons in comments.",
    },
    "how_to_playbook": {
        "hook": "Open with a practical challenge question.",
        "structure": "Provide a clear step-by-step playbook with numbered actions.",
        "cta": "Ask readers which step they will implement first.",
    },
    "trend_radar": {
        "hook": "Open with a what-is-changing-fastest question.",
        "structure": "Summarize 3 trends and why each matters now.",
        "cta": "Ask which trend will have the biggest impact this quarter.",
    },
    "case_study_breakdown": {
        "hook": "Open with a problem-to-outcome curiosity question.",
        "structure": "Use context, action, result, and lesson format.",
        "cta": "Ask readers if they want a deeper teardown in comments.",
    },
    "cta_to_dm": {
        "hook": "Open with a high-value pain-point question.",
        "structure": "Share concise value points and tangible outcomes.",
        "cta": "Ask readers to comment a keyword or DM for the full resource.",
    },
}


class GenerationService:

    HASHTAG_MAP = {
        "automation": "#automation",
        "automated": "#automated",
        "pipeline": "#pipeline",
        "pipelines": "#pipelines",
        "deployment": "#deployment",
        "deployments": "#deployments",
        "devops": "#devops",
        "cicd": "#cicd",
        "ci/cd": "#cicd",
        "engineering": "#engineering",
        "leadership": "#leadership",
        "product": "#product",
        "productivity": "#productivity",
        "security": "#security",
        "testing": "#testing",
        "cloud": "#cloud",
        "ai": "#ai",
        "data": "#data",
    }

    CATEGORY_DEFAULT_HASHTAGS = {
        "AI": ["#ai", "#artificialintelligence", "#machinelearning", "#innovation"],
        "DEVOPS": ["#devops", "#cicd", "#automation", "#softwareengineering"],
        "CLOUD": ["#cloud", "#cloudcomputing", "#infrastructure", "#scalability"],
        "DATA": ["#data", "#analytics", "#datapipeline", "#businessintelligence"],
        "PYTHON": ["#python", "#programming", "#automation", "#softwareengineering"],
        "CAREER": ["#careergrowth", "#leadership", "#productivity", "#professionaldevelopment"],
        "LINKEDIN": ["#linkedin", "#personalbranding", "#contentstrategy", "#professionalgrowth"],
        "AUTOMATION": ["#automation", "#workflow", "#efficiency", "#operations"],
        "PRODUCTIVITY": ["#productivity", "#focus", "#timemanagement", "#worksmarter"],
        "GENERAL": ["#leadership", "#innovation", "#strategy", "#business"],
    }

    VISUAL_TEMPLATE_HINTS = {
        "auto": "Choose the strongest composition automatically based on topic context.",
        "matrix_2x2": "Design a clean 2x2 decision matrix infographic with clear quadrants and axis labels.",
        "tool_comparison": "Design a horizontal comparison board of tools/options with clear cards and concise labels.",
        "flow_diagram": "Design a step-by-step flow diagram with directional connectors and concise nodes.",
        "architecture_diagram": "Design a modern architecture diagram with layered components and relationship arrows.",
        "timeline": "Design a timeline visual with milestones and short annotations.",
        "checklist": "Design a checklist-style infographic with grouped items and visual hierarchy.",
    }

    def __init__(self, topic_repository: TopicRepository, db_session):
        self.topic_repository = topic_repository
        self.history_repository = GenerationHistoryRepository(db_session)
        self.db = db_session
        self.ai_client = OpenAIClient()

    @staticmethod
    def _slugify(text: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
        return slug[:48] or "topic"

    @staticmethod
    def _word_count(text: str) -> int:
        return len([token for token in (text or "").split() if token.strip()])

    @staticmethod
    def _trim_to_word_limit(text: str, max_words: int) -> str:
        if max_words <= 0:
            return (text or "").strip()
        words = [token for token in (text or "").split() if token.strip()]
        if len(words) <= max_words:
            return (text or "").strip()
        trimmed = " ".join(words[:max_words]).strip()
        if trimmed and trimmed[-1] not in ".!?":
            trimmed = f"{trimmed}."
        return trimmed

    def _rewrite_with_word_limit(
        self,
        topic,
        generated_post: str,
        min_words: int,
        max_words: int,
    ) -> str:
        rewrite_prompt = (
            f"Rewrite the LinkedIn post below to be between {min_words} and {max_words} words. "
            "Keep the core meaning, preserve a clear call to action, and keep the tone professional and concise. "
            "Return only the revised post text.\n\n"
            f"Topic: {topic.topic}\n\n"
            f"Post:\n{generated_post}"
        )
        result = self.ai_client.generate_post(
            rewrite_prompt,
            "You are an experienced LinkedIn content editor who writes concise, high-quality posts.",
        )
        return (result.get("content") or "").strip()

    def _build_image_prompt(
        self,
        topic,
        generated_post: str,
        index: int,
        image_style_hint: str | None = None,
        visual_template: str = "auto",
    ) -> str:
        style_hint = (image_style_hint or "").strip()
        template_hint = self.VISUAL_TEMPLATE_HINTS.get(visual_template, self.VISUAL_TEMPLATE_HINTS["auto"])
        return (
            f"Create a premium LinkedIn visual for {topic.category.value}, variation {index}. "
            "Art direction: modern B2B editorial, minimal and clean, realistic or high-end vector style, strong composition. "
            "Prefer educational visuals such as flow diagrams, architecture diagrams, or animated-style infographics. "
            "Use symbols/metaphors from the topic instead of big headline text. "
            "If text appears, keep it very short (max 3 words) and clearly legible. "
            "Avoid poster-like layouts, avoid cartoonish style, avoid dense typography, avoid logos and brand names. "
            "Color palette: professional blue/neutral tones with subtle contrast accents. "
            "Output should look suitable for executive LinkedIn posts. "
            f"Template direction: {template_hint} "
            f"Topic: {topic.topic}. Context: {generated_post[:450]}. "
            f"Style guidance: {style_hint if style_hint else 'auto-select best educational style for the topic.'}"
        )

    def _save_images(
        self,
        topic,
        generated_post: str,
        image_count: int,
        image_style_hint: str | None = None,
        visual_template: str = "auto",
        image_size: str = "1536x1024",
    ) -> list[str]:
        generated_dir = Path(__file__).resolve().parent.parent / "static" / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)

        urls: list[str] = []
        for idx in range(1, image_count + 1):
            prompt = self._build_image_prompt(
                topic,
                generated_post,
                idx,
                image_style_hint=image_style_hint,
                visual_template=visual_template,
            )
            image_bytes = self.ai_client.generate_image(prompt, size=image_size)
            filename = (
                f"topic-{topic.id}-{self._slugify(topic.category.value)}-"
                f"{self._slugify(topic.topic)}-{idx}-{uuid.uuid4().hex[:8]}.png"
            )
            image_path = generated_dir / filename
            image_path.write_bytes(image_bytes)
            urls.append(f"http://{settings.host}:{settings.port}/static/generated/{filename}")

        return urls

    def _load_prompt_template(self, template_name: str) -> str:
        normalized = template_name.lower()
        filename = DEFAULT_TEMPLATES.get(normalized, "story.txt")
        prompt_path = Path(__file__).resolve().parent.parent / "prompt_templates" / filename

        if not prompt_path.exists():
            raise FileNotFoundError(prompt_path)

        return prompt_path.read_text(encoding="utf-8")

    def _build_prompt(self, topic, template_name: str) -> str:
        template_text = self._load_prompt_template(template_name)
        return template_text.format(topic=topic.topic)

    @staticmethod
    def _extract_existing_hashtags(text: str) -> set[str]:
        return {tag.lower() for tag in re.findall(r"#[A-Za-z0-9_]+", text or "")}

    def _collect_hashtag_candidates(self, topic, text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9/]+", f"{topic.topic} {text}".lower())
        candidates: list[str] = []

        category_tag = f"#{topic.category.value.lower()}"
        candidates.append(category_tag)

        for token in tokens:
            mapped = self.HASHTAG_MAP.get(token)
            if mapped and mapped not in candidates:
                candidates.append(mapped)

        for tag in self.CATEGORY_DEFAULT_HASHTAGS.get(topic.category.value, []):
            if tag not in candidates:
                candidates.append(tag)

        # Keep output compact and deterministic.
        return candidates[:10]

    @staticmethod
    def _append_trailing_hashtags(text: str, hashtags: list[str], min_count: int = 4, max_count: int = 8) -> str:
        body = (text or "").strip()
        if not body:
            return body

        existing = GenerationService._extract_existing_hashtags(body)
        ordered: list[str] = []

        # Preserve existing tags in first-seen order.
        for tag in re.findall(r"#[A-Za-z0-9_]+", body):
            lowered = tag.lower()
            if lowered not in [item.lower() for item in ordered]:
                ordered.append(tag if tag.startswith("#") else f"#{tag}")

        for tag in hashtags:
            lowered = tag.lower()
            if lowered not in existing and lowered not in [item.lower() for item in ordered]:
                ordered.append(tag)

        if len(ordered) < min_count:
            return body

        final_tags = ordered[:max_count]
        lines = [line for line in body.splitlines() if not line.strip().startswith("#")]
        clean_body = "\n".join(lines).strip()
        return f"{clean_body}\n\n{' '.join(final_tags)}"

    @staticmethod
    def _inject_inline_hashtags(text: str, hashtags: list[str], min_count: int = 2, max_count: int = 5) -> str:
        body = (text or "").strip()
        if not body:
            return body

        non_hashtag_lines = [line for line in body.splitlines() if not line.strip().startswith("#")]
        working = "\n".join(non_hashtag_lines)
        inserted = 0

        for tag in hashtags:
            if inserted >= max_count:
                break

            keyword = tag.lstrip("#")
            if not keyword:
                continue

            pattern = re.compile(rf"(?<!#)\b{re.escape(keyword)}\b", re.IGNORECASE)
            if not pattern.search(working):
                continue

            working = pattern.sub(tag, working, count=1)
            inserted += 1

        if inserted < min_count:
            return body

        hashtag_lines = [line for line in body.splitlines() if line.strip().startswith("#")]
        suffix = f"\n{'\n'.join(hashtag_lines)}" if hashtag_lines else ""
        return f"{working.strip()}{suffix}".strip()

    def _enrich_generated_post_with_hashtags(self, topic, generated_post: str) -> str:
        candidates = self._collect_hashtag_candidates(topic, generated_post)
        with_inline = self._inject_inline_hashtags(generated_post, candidates)
        with_trailing = self._append_trailing_hashtags(with_inline, candidates)
        return with_trailing.strip()

    def _record_history(
        self,
        topic_id: int,
        prompt_template: str,
        prompt_version: str,
        model: str,
        temperature: float,
        max_tokens: int,
        status: str,
        generated_post: str | None = None,
        error_message: str | None = None,
        retry_count: int = 0,
        latency_ms: int | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ):
        version = self.history_repository.get_latest_version(topic_id) + 1
        return self.history_repository.create(
            topic_id=topic_id,
            version=version,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            retry_count=retry_count,
            latency_ms=latency_ms,
            generated_post=generated_post,
            error_message=error_message,
            status=status,
        )

    def generate_for_topic(
        self,
        topic,
        template_name: str = "story",
        prompt_version: str = "v1",
        retry_limit: int = 3,
        generate_images: bool = False,
        image_count: int = 1,
        image_style_hint: str | None = None,
        visual_template: str = "auto",
        image_size: str = "1536x1024",
        prompt_override: str | None = None,
        min_words: int | None = None,
        max_words: int | None = None,
    ) -> bool:
        self.topic_repository.update_generated_post(
            topic.id,
            TopicStatus.GENERATING,
        )

        prompt = (prompt_override or "").strip() or self._build_prompt(topic, template_name)
        model = settings.GPT_MODEL
        temperature = settings.GPT_TEMPERATURE
        max_tokens = settings.GPT_MAX_TOKENS

        attempts = 0
        while attempts < retry_limit:
            attempts += 1
            start = time.time()
            try:
                result = self.ai_client.generate_post(
                    prompt,
                    "You are an experienced LinkedIn content creator.",
                )
                latency_ms = int((time.time() - start) * 1000)
                generated_post = result["content"].strip()

                if not generated_post:
                    raise ValueError("AI returned empty generated content.")

                generated_post = self._enrich_generated_post_with_hashtags(topic, generated_post)

                if min_words is not None and max_words is not None:
                    word_count = self._word_count(generated_post)
                    if word_count > max_words or word_count < min_words:
                        generated_post = self._rewrite_with_word_limit(
                            topic,
                            generated_post,
                            min_words,
                            max_words,
                        )
                        generated_post = self._enrich_generated_post_with_hashtags(topic, generated_post)
                        word_count = self._word_count(generated_post)

                        if word_count > max_words:
                            generated_post = self._trim_to_word_limit(generated_post, max_words)
                        if word_count < min_words:
                            raise ValueError(
                                f"Generated content too short ({word_count} words)."
                            )

                self.topic_repository.update_generated_post(
                    topic.id,
                    TopicStatus.READY_FOR_REVIEW,
                    generated_post,
                )

                self._record_history(
                    topic.id,
                    template_name,
                    prompt_version,
                    model,
                    temperature,
                    max_tokens,
                    TopicStatus.READY_FOR_REVIEW,
                    generated_post=generated_post,
                    error_message=None,
                    retry_count=attempts - 1,
                    latency_ms=latency_ms,
                    prompt_tokens=result.get("prompt_tokens"),
                    completion_tokens=result.get("completion_tokens"),
                    total_tokens=result.get("total_tokens"),
                )

                if generate_images:
                    count = max(1, min(2, int(image_count)))
                    try:
                        image_urls = self._save_images(
                            topic,
                            generated_post,
                            count,
                            image_style_hint=image_style_hint,
                            visual_template=visual_template,
                            image_size=image_size,
                        )
                        if image_urls:
                            publish_service = PublishService(self.db)
                            for image_url in image_urls:
                                publish_service.attach_media_to_topic(
                                    topic.id,
                                    image_url,
                                    mime_type="image/png",
                                )
                    except Exception as exc:
                        failed_topic = self.topic_repository.get_by_id(topic.id)
                        if failed_topic is not None:
                            failed_topic.error_message = f"Image generation failed: {str(exc)}"
                            self.topic_repository.update(failed_topic)
                        # Keep draft generation successful even if image steps fail.
                        logger.exception("Image generation/attachment failed for topic %s", topic.id)

                return True

            except Exception as exc:
                latency_ms = int((time.time() - start) * 1000)
                error_message = str(exc)
                logger.exception("Generation attempt failed for topic %s", topic.id)

                self._record_history(
                    topic.id,
                    template_name,
                    prompt_version,
                    model,
                    temperature,
                    max_tokens,
                    TopicStatus.FAILED,
                    generated_post=None,
                    error_message=error_message,
                    retry_count=attempts,
                    latency_ms=latency_ms,
                )

                if attempts >= retry_limit:
                    self.topic_repository.mark_failed(topic.id, error_message)
                    return False

        return False

    def generate_images_for_topic(
        self,
        topic,
        image_count: int = 1,
        image_style_hint: str | None = None,
        visual_template: str = "auto",
        image_size: str = "1536x1024",
    ) -> list[str]:
        context = (topic.generated_post or topic.topic or "").strip()
        if not context:
            raise ValueError("Topic content is empty; cannot generate image.")

        count = max(1, min(2, int(image_count)))
        image_urls = self._save_images(
            topic,
            context,
            count,
            image_style_hint=image_style_hint,
            visual_template=visual_template,
            image_size=image_size,
        )

        if image_urls:
            publish_service = PublishService(self.db)
            for image_url in image_urls:
                publish_service.attach_media_to_topic(
                    topic.id,
                    image_url,
                    mime_type="image/png",
                )

        return image_urls

    @staticmethod
    def _extract_json_payload(raw_text: str) -> dict:
        text = (raw_text or "").strip()
        if not text:
            raise ValueError("Enhancement model returned empty content.")

        # Support plain JSON or markdown-fenced JSON.
        if "```" in text:
            text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Enhancement response was not valid JSON.") from exc

    @staticmethod
    def _enforce_engagement_signature(text: str, engagement_type: str, category: str) -> str:
        optimized = (text or "").strip()
        if not optimized:
            return optimized

        lines = [line.rstrip() for line in optimized.splitlines()]
        first_non_empty = next((line for line in lines if line.strip()), "")

        if engagement_type == "discussion_starter":
            if "?" not in first_non_empty:
                question = f"What is the biggest misconception teams still have about {category} right now?"
                optimized = f"{question}\n\n{optimized}".strip()

        elif engagement_type == "how_to_playbook":
            if not re.search(r"(?m)^\s*1\.\s+", optimized):
                playbook_block = (
                    "1. Diagnose the highest-friction bottleneck.\n"
                    "2. Execute one practical change this week.\n"
                    "3. Measure outcomes and iterate with data."
                )
                optimized = f"{optimized}\n\n{playbook_block}".strip()

        elif engagement_type == "trend_radar":
            if "trend 1:" not in optimized.lower():
                trend_block = (
                    "Trend 1: Market behavior shift\n"
                    "Trend 2: Tooling and workflow shift\n"
                    "Trend 3: Team execution shift"
                )
                optimized = f"{optimized}\n\n{trend_block}".strip()

        elif engagement_type == "case_study_breakdown":
            required_sections = ["Context:", "Action:", "Result:", "Lesson:"]
            missing_sections = [section for section in required_sections if section.lower() not in optimized.lower()]
            if missing_sections:
                section_block = "\n".join(
                    [
                        "Context: Briefly describe the starting challenge.",
                        "Action: Explain the steps taken.",
                        "Result: Share measurable outcome.",
                        "Lesson: State what others can replicate.",
                    ]
                )
                optimized = f"{optimized}\n\n{section_block}".strip()

        elif engagement_type == "cta_to_dm":
            if "dm" not in optimized.lower():
                optimized = f"{optimized}\n\nDM me \"PLAYBOOK\" if you want the full framework.".strip()

        return optimized

    def _build_engagement_fallback(self, topic, engagement_type: str, hashtag_count: int) -> dict:
        rules = ENGAGEMENT_RULES.get(engagement_type, ENGAGEMENT_RULES["discussion_starter"])
        topic_label = topic.topic.strip() if topic.topic else topic.category.value
        hooks = [
            f"{topic_label}: what is your take?",
            f"What is the most practical move for {topic_label} right now?",
            f"Would you implement this approach for {topic_label}? Why or why not?",
        ]

        optimized_post = self._enforce_engagement_signature(
            (topic.generated_post or "").strip(),
            engagement_type,
            topic.category.value,
        )
        optimized_post = self._enrich_generated_post_with_hashtags(topic, optimized_post)

        hashtags = self._collect_hashtag_candidates(topic, optimized_post)
        if len(hashtags) < hashtag_count:
            defaults = self.CATEGORY_DEFAULT_HASHTAGS.get(topic.category.value, [])
            for tag in defaults:
                if tag not in hashtags:
                    hashtags.append(tag)
                if len(hashtags) >= hashtag_count:
                    break

        return {
            "hooks": hooks[:3],
            "hashtags": hashtags[:hashtag_count],
            "optimized_post": optimized_post,
            "rule_summary": rules,
        }

    def enhance_engagement(
        self,
        topic,
        engagement_type: str = "discussion_starter",
        extra_keywords: list[str] | None = None,
        hashtag_count: int = 6,
    ) -> dict:
        if not topic.generated_post or not topic.generated_post.strip():
            raise ValueError("Generate or add draft content before engagement enhancement.")

        extra_keywords = [kw.strip() for kw in (extra_keywords or []) if kw and kw.strip()]
        hashtag_count = max(4, min(10, int(hashtag_count)))

        engagement_type = (engagement_type or "discussion_starter").strip().lower()
        if engagement_type not in ENGAGEMENT_RULES:
            engagement_type = "discussion_starter"
        rules = ENGAGEMENT_RULES[engagement_type]

        prompt = (
            "You will optimize a LinkedIn draft for engagement while preserving factual meaning.\n"
            "Return ONLY valid JSON with this exact shape:\n"
            "{\"hooks\":[\"...\",\"...\",\"...\"],\"hashtags\":[\"#tag\"],\"optimized_post\":\"...\"}\n"
            "Rules:\n"
            "- hooks: exactly 3 options, each under 140 chars\n"
            f"- hashtags: exactly {hashtag_count} tags, mixed broad+niche+trending\n"
            "- optimized_post: 120-260 words, clear paragraphs, one CTA\n"
            "- naturally include provided keywords if relevant\n"
            "- avoid spammy tone and keyword stuffing\n"
            "- do not invent claims\n\n"
            f"Engagement type: {engagement_type}\n"
            f"Hook rule: {rules['hook']}\n"
            f"Structure rule: {rules['structure']}\n"
            f"CTA rule: {rules['cta']}\n\n"
            f"Category: {topic.category.value}\n"
            f"Topic title: {topic.topic}\n"
            f"Extra keywords: {', '.join(extra_keywords) if extra_keywords else 'None'}\n"
            "Draft to optimize:\n"
            f"{topic.generated_post.strip()}"
        )

        payload = None
        last_error = None
        system_prompt = "You are a senior LinkedIn growth editor."

        for attempt in range(1, 4):
            try:
                retry_prompt = prompt
                if attempt > 1:
                    retry_prompt = (
                        f"{prompt}\n\n"
                        "IMPORTANT: Return only valid minified JSON with keys hooks, hashtags, optimized_post. "
                        "No markdown, no prose, no code fences."
                    )

                result = self.ai_client.generate_post(retry_prompt, system_prompt)
                payload = self._extract_json_payload(result.get("content", ""))
                break
            except ValueError as exc:
                last_error = exc
                continue

        if payload is None:
            logger.warning(
                "Engagement enhancement fallback used for topic %s after retries: %s",
                topic.id,
                str(last_error) if last_error else "unknown error",
            )
            fallback = self._build_engagement_fallback(topic, engagement_type, hashtag_count)
            return {
                "success": True,
                "message": "Engagement enhancement fallback applied after model returned an empty or invalid response.",
                "topic_id": topic.id,
                "engagement_type": engagement_type,
                "optimized_post": fallback["optimized_post"],
                "hooks": fallback["hooks"],
                "hashtags": fallback["hashtags"],
            }

        hooks = [str(h).strip() for h in payload.get("hooks", []) if str(h).strip()]
        hashtags = [str(h).strip() for h in payload.get("hashtags", []) if str(h).strip()]
        optimized_post = str(payload.get("optimized_post", "")).strip()

        if not hooks:
            raise ValueError("Enhancement did not return hook options.")
        if not hashtags:
            raise ValueError("Enhancement did not return hashtag suggestions.")
        if not optimized_post:
            raise ValueError("Enhancement did not return optimized draft content.")

        optimized_post = self._enforce_engagement_signature(
            optimized_post,
            engagement_type,
            topic.category.value,
        )

        return {
            "success": True,
            "message": "Engagement enhancement generated successfully.",
            "topic_id": topic.id,
            "engagement_type": engagement_type,
            "optimized_post": optimized_post,
            "hooks": hooks[:3],
            "hashtags": hashtags[:hashtag_count],
        }
