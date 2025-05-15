import importlib.metadata as metadata
import logging
from functools import lru_cache
from threading import Lock
from typing import Dict, List, Type

from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseTranslationProvider
from .exceptions import ProviderError, ProviderNotFoundError
from .types import TranslationConfig, TranslationStatus  # Add this import

__all__ = ["register_provider", "get_provider", "list_providers", "discover_providers"]

# Add version info
try:
    __version__ = metadata.version("mt_providers")
except Exception:
    __version__ = "unknown"

logger = logging.getLogger(__name__)

PROVIDER_REGISTRY: Dict[str, Type[BaseTranslationProvider]] = {}
_registry_lock = Lock()


def register_provider(name: str, cls: Type[BaseTranslationProvider]) -> None:
    """
    Register a translation provider.

    Args:
        name: Unique identifier for the provider
        cls: Provider class that inherits from BaseTranslationProvider

    Raises:
        ProviderError: If provider class doesn't inherit from
                      BaseTranslationProvider or if provider name is
                      already registered
    """
    if not name or not isinstance(name, str):
        raise ProviderError("Provider name must be a non-empty string")

    if name in PROVIDER_REGISTRY:
        raise ProviderError(f"Provider '{name}' is already registered")

    if not isinstance(cls, type) or not issubclass(cls, BaseTranslationProvider):
        raise ProviderError(
            f"Provider {name} must inherit from BaseTranslationProvider"
        )

    if hasattr(cls, "min_supported_version"):
        from packaging import version

        min_ver = cls.min_supported_version
        if version.parse(__version__) < version.parse(min_ver):
            raise ProviderError(f"Provider {name} requires mt_providers>={min_ver}")

    with _registry_lock:
        PROVIDER_REGISTRY[name] = cls
        logger.info(f"Registered translation provider: {name}")


@lru_cache(maxsize=None)
def get_provider(name: str) -> Type[BaseTranslationProvider]:
    """
    Get a registered provider by name.

    Args:
        name: Name of the provider to retrieve

    Returns:
        The provider class

    Raises:
        ProviderNotFoundError: If provider is not found in registry
    """
    try:
        return PROVIDER_REGISTRY[name]
    except KeyError:
        available = list_providers()
        msg = f"Provider '{name}' not found. Available providers: {available}"
        logger.error(msg)
        raise ProviderNotFoundError(msg)


def list_providers() -> List[str]:
    """List all registered provider names."""
    return sorted(PROVIDER_REGISTRY.keys())


def discover_providers(
    entry_point_group: str = "mt_providers", raise_errors: bool = False
) -> List[str]:
    """
    Discover and register translation providers from entry points.

    Args:
        entry_point_group: Entry point group name for providers
        raise_errors: If True, raises exceptions instead of logging them

    Returns:
        List of successfully registered provider names
    """
    registered: List[str] = []
    try:
        entry_points = metadata.entry_points().get(entry_point_group, [])
    except Exception as e:
        logger.error(f"Failed to get entry points: {e}")
        if raise_errors:
            raise
        return registered

    for entry_point in entry_points:
        try:
            provider_class = entry_point.load()
            if not hasattr(provider_class, "name"):
                raise ProviderError(
                    f"Provider {entry_point.name} missing 'name' attribute"
                )

            register_provider(provider_class.name, provider_class)
            registered.append(provider_class.name)
        except Exception as e:
            logger.error(
                f"Failed to load provider {entry_point.name}: {str(e)}", exc_info=True
            )
            if raise_errors:
                raise

    return registered


def clear_registry() -> None:
    """Clear the provider registry (mainly for testing)."""
    PROVIDER_REGISTRY.clear()
    # Clear the LRU cache
    get_provider.cache_clear()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def check_provider_health(
    name: str, config: TranslationConfig, test_text: str = "test"
) -> bool:
    """
    Check if a provider is operational.

        Args:
            name: Name of the provider to check
            config: Provider configuration
            test_text: Text to use for health check (default: "test")

        Returns:
            bool: True if provider is operational, False otherwise"""
    print("ATTEMPTING HEALTH CHECK")
    try:
        provider = get_provider(name)(config)
        if provider.supports_async:
            result = await provider.translate_async(test_text, "en", "fr")
        else:
            result = provider.translate(test_text, "en", "fr")
        # Explicitly check the status is SUCCESS
        return result.get("status") == TranslationStatus.SUCCESS
    except Exception as e:
        logger.error(f"Health check failed for provider {name}: {str(e)}")
        raise
