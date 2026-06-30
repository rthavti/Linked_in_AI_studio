"""
Generation Service

Handles generation, retry, history recording, and review state transitions.
"""

import time
from pathlib import Path

from app.ai.client import OpenAIClient
from app.config.settings import settings
from app.models.topic import TopicStatus
from app.repositories.generation_history_repository import GenerationHistoryRepository
from app.repositories.topic_repository import TopicRepository
from app.logger import logger


DEFAULT_TEMPLATES = {
    "story": "story.txt",
    "technical": "technical.txt",
    "leadership": "leadership.txt",
    "career": "career.txt",
    "devops": "devops.txt",
    "ai": "ai.txt",
}


class GenerationService:

    def __init__(self, topic_repository: TopicRepository, db_session):
        self.topic_repository = topic_repository
        self.history_repository = GenerationHistoryRepository(db_session)
        self.ai_client = OpenAIClient()

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
    ) -> bool:
        self.topic_repository.update_generated_post(
            topic.id,
            TopicStatus.GENERATING,
        )

        prompt = self._build_prompt(topic, template_name)
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
