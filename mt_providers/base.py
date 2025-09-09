import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
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
    min_supported_version: str = "0.1.8"  # Add minimum supported version

    def __init__(self, config: TranslationConfig):
        from . import __version__

        if not self.name:
            raise ConfigurationError("Provider name must be set")

        # Version compatibility check
        if hasattr(self, 'min_supported_version') and self.min_supported_version:
            from packaging import version
            
            min_ver = self.min_supported_version
            if version.parse(__version__) < version.parse(min_ver):
                raise ConfigurationError(
                    f"Provider {self.name} requires mt_providers>={min_ver}, "
                    f"but {__version__} is installed"
                )

        self.config = config
        self.validate_config()
        self._last_request_time: Optional[float] = None
        self._rate_limit_lock: Optional[asyncio.Lock] = None

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
            "timestamp": datetime.now(timezone.utc),
            "metadata": metadata or {},
        }

    def get_user_agent(self) -> str:
        """
        Get User-Agent string for this provider.
        
        Returns:
            Formatted User-Agent string (name/version)
        """
        # If user provides custom UA name/version, use that
        if self.config.user_agent_name and self.config.user_agent_version:
            return f"{self.config.user_agent_name}/{self.config.user_agent_version}"
        
        # Otherwise, detect from package metadata
        provider_name = self.name  # Fallback to class name attribute
        provider_version = "unknown"
        
        try:
            import importlib.metadata as metadata
            
            # Get the module where this provider class is defined
            module_name = self.__class__.__module__
            
            # Extract package name from module
            package_name = module_name.split('.')[0] if '.' in module_name else module_name
            
            # Try to get metadata for this package
            try:
                dist = metadata.distribution(package_name)
                provider_version = dist.version
                
                # Extract provider name from package name
                # e.g., 'mt_provider_deepl' -> 'deepl'
                if package_name.startswith('mt_provider_'):
                    provider_name = package_name.replace('mt_provider_', '')
                elif package_name.startswith('mt_providers_'):
                    provider_name = package_name.replace('mt_providers_', '')
            except metadata.PackageNotFoundError:
                pass
                
        except Exception:
            pass
        
        return f"{provider_name}/{provider_version}"
    

    async def _handle_rate_limit(self) -> None:
        """Enforce rate limiting if configured."""
        if not self.config.rate_limit:
            return

        if self._rate_limit_lock is None:
            self._rate_limit_lock = asyncio.Lock()

        async with self._rate_limit_lock:
            if self._last_request_time:
                elapsed = time.time() - self._last_request_time
                wait_time = (1.0 / self.config.rate_limit) - elapsed
                if wait_time > 0:
                    logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            self._last_request_time = time.time()
