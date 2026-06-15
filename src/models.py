from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Category(str, Enum):
    automation = "автоматизація"
    integration = "інтеграція"
    report = "звіт/аналітика"
    bug = "баг/підтримка"
    question = "питання/консультація"
    out_of_scope = "поза скоупом"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class LLMClassification(BaseModel):
    """Schema that the LLM fills in — no 'id' here, we inject it ourselves."""
    category: Category
    target_department: Optional[str]
    priority: Priority
    short_summary: str
    requested_actions: list[str]
    needs_clarification: bool
    confidence: Confidence  # how sure the model is about its own classification


class ClassifiedRequest(LLMClassification):
    """Full record stored in output.json, includes original metadata."""
    id: str
    channel: str
    timestamp: str
