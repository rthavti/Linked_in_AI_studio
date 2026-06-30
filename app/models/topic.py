"""
Domain models and enums for Topic.
"""

from enum import Enum


class TopicStatus(str, Enum):
    NEW = "NEW"
    GENERATING = "GENERATING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Category(str, Enum):
    AI = "AI"
    DEVOPS = "DEVOPS"
    CLOUD = "CLOUD"
    PYTHON = "PYTHON"
    DATA = "DATA"
    CAREER = "CAREER"
    LINKEDIN = "LINKEDIN"
    AUTOMATION = "AUTOMATION"
    PRODUCTIVITY = "PRODUCTIVITY"
    GENERAL = "GENERAL"