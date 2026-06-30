"""
Validation Service

Handles validation logic for topics.

Author: LinkedIn AI Studio
"""

from app.models.topic import Topic


class ValidationService:
    """
    Service responsible for validating topics.
    """

    @staticmethod
    def validate_topic(topic: Topic) -> None:
        if not topic.topic:
            raise ValueError("Topic cannot be empty.")
        if not topic.category:
            raise ValueError("Category cannot be empty.")