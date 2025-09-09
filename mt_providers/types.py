from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class TranslationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return str(self.value)


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
    user_agent_name: Optional[str] = None
    user_agent_version: Optional[str] = None
    
    def __post_init__(self):
        """Validate that both user_agent fields are provided together."""
        if (self.user_agent_name is None) != (self.user_agent_version is None):
            raise ValueError(
                "Both user_agent_name and user_agent_version must be provided together"
            )


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
