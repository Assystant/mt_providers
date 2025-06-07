import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from .exceptions import ConfigurationError
from .types import TranslationConfig, TranslationResponse, TranslationStatus

logger = logging.getLogger(__name__)


class BaseTranslationProvider(ABC):
    """Base class for translation providers."""

    name: str
    requires_region: bool = False
    supports_async: bool = False
    max_chunk_size: int = 5000
    min_supported_version: str = "0.1.0"  # Add minimum supported version

    def __init__(self, config: TranslationConfig):
        from . import __version__

        if not self.name:
            raise ConfigurationError("Provider name must be set")

        # Version compatibility check
        from packaging import version

        # min_ver = self.min_supported_version
        # if version.parse(__version__) < version.parse(min_ver):
        #     raise ConfigurationError(
        #         f"Provider {self.name} requires mt_providers>={min_ver}"
        #     )

        self.config = config
        self.validate_config()
        self._last_request_time: Optional[float] = None
        self._rate_limit_lock = None

    def validate_config(self) -> None:
        """Validate provider configuration."""
        if not self.config.api_key:
            raise ConfigurationError("API key is required")
        if self.requires_region and not self.config.region:
            raise ConfigurationError("Region is required for this provider")

    @abstractmethod
    def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResponse:
        """Translate single text."""
        pass

    async def translate_async(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResponse:
        """Async translation implementation."""
        if not self.supports_async:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.translate, text, source_lang, target_lang
            )
        raise NotImplementedError("Async translation not implemented")

    def bulk_translate(
        self, texts: List[str], source_lang: str, target_lang: str
    ) -> List[TranslationResponse]:
        """Translate multiple texts."""
        return [self.translate(text, source_lang, target_lang) for text in texts]

    def _create_response(
        self,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        char_count: int,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranslationResponse:
        """Helper to create standardized response"""
        return {
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "provider": self.name,
            "char_count": char_count,
            "status": TranslationStatus.FAILED if error else TranslationStatus.SUCCESS,
            "error": error,
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {},
        }

    async def _handle_rate_limit(self) -> None:
        """Enforce rate limiting if configured."""
        if not self.config.rate_limit:
            return

        async with self._rate_limit_lock:
            if self._last_request_time:
                elapsed = time.time() - self._last_request_time
                wait_time = (1.0 / self.config.rate_limit) - elapsed
                if wait_time > 0:
                    logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            self._last_request_time = time.time()
