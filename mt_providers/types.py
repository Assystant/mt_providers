from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, TypedDict


class TranslationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"TranslationStatus.{self.name}"


class TranslationProvider(Protocol):
    def translate(self, text: str, source: str, target: str) -> str:
        ...

    def bulk_translate(self, texts: List[str], source: str, target: str) -> List[str]:
        ...  # Changed from list[str]


@dataclass
class TranslationConfig:
    """Base configuration for translation providers."""

    api_key: str
    endpoint: Optional[str] = None
    region: Optional[str] = None
    timeout: int = 30
    rate_limit: Optional[int] = None
    retry_attempts: int = 3
    retry_backoff: float = 1.0


class TranslationResponse(TypedDict):
    """Standardized translation response."""

    translated_text: str
    source_lang: str
    target_lang: str
    provider: str
    char_count: int
    status: TranslationStatus
    error: Optional[str]
    request_id: str
    timestamp: datetime
    metadata: Dict[str, Any]  # More specific typing for metadata
