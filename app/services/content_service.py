"""
Content Generation Service
"""

import logging

from app.models.topic import TopicStatus
from app.repositories.topic_repository import TopicRepository
from app.ai.client import OpenAIClient

logger = logging.getLogger(__name__)


class ContentService:

    def __init__(
        self,
        repository: TopicRepository,
        ai_client: OpenAIClient,
    ):
        self.repository = repository
        self.ai_client = ai_client

    def generate_next(self) -> bool:

        topic = self.repository.get_next_pending()

        if topic is None:

            logger.info("No pending topics found.")

            return False

        self.repository.update_generated_post(
            topic.id,
            TopicStatus.PROCESSING,
        )

        prompt = self.build_prompt(topic)

        try:

            result = self.ai_client.generate_post(
                prompt,
                "You are an experienced LinkedIn content creator.",
            )
            generated_post = result["content"]

            self.repository.update_generated_post(
                topic.id,
                TopicStatus.READY,
                generated_post,
            )

            logger.info(
                "Generated LinkedIn post for topic %s",
                topic.id,
            )

            return True

        except Exception as ex:

            self.repository.mark_failed(
                topic.id,
                str(ex),
            )

            logger.exception(
                "Generation failed for topic %s",
                topic.id,
            )

            return False

    def build_prompt(self, topic) -> str:

        return f"""
You are an experienced LinkedIn content creator.

Write a professional LinkedIn post tailored for a LinkedIn audience.

Topic:
{topic.topic}

Category:
{topic.category}

Priority:
{topic.priority}

Requirements:
- Start with a compelling hook
- Use storytelling with practical insights
- Offer actionable advice for professionals
- Include a strong call to action
- Close with a question
- Add five relevant hashtags

Length:
200-300 words

Tone:
Professional, confident, and helpful
"""