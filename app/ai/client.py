"""
OpenAI Client

Supports:
- GPT-5 family
- GPT-4.1 family
- GPT-4o family

Author: LinkedIn AI Studio
"""

import logging
import base64

from openai import OpenAI

from app.ai.base import AIClient
from app.config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIClient(AIClient):

    MAX_RETRIES = 3

    def __init__(self):

        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=60,
        )

    def generate_post(
        self,
        prompt: str,
        system_prompt: str,
    ) -> dict:

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        request = self._build_request(messages)

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    **request
                )

                usage = response.usage
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
                total_tokens = getattr(usage, "total_tokens", 0)

                logger.info(
                    "Prompt=%s Completion=%s Total=%s",
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                )

                content = response.choices[0].message.content.strip()

                return {
                    "content": content,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "request": request,
                }

            except Exception:
                logger.exception(
                    "OpenAI request failed. Attempt %s/%s",
                    attempt + 1,
                    self.MAX_RETRIES,
                )

                if attempt == self.MAX_RETRIES - 1:
                    raise

    def _build_request(self, messages):

        request = {
            "model": settings.GPT_MODEL,
            "messages": messages,
            "max_completion_tokens": settings.GPT_MAX_TOKENS,
        }

        model = settings.GPT_MODEL.lower()

        if not model.startswith("gpt-5"):
            request["temperature"] = settings.GPT_TEMPERATURE

        return request

    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
    ) -> bytes:

        response = self.client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
        )

        if not response.data:
            raise RuntimeError("Image generation returned no data.")

        b64_image = getattr(response.data[0], "b64_json", None)
        if not b64_image:
            raise RuntimeError("Image generation did not include base64 image data.")

        return base64.b64decode(b64_image)