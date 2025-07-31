# mt_providers/__init__.py
from .base import BaseTranslationProvider
from .registry import (
    discover_providers,
    get_provider,
    list_providers,
    register_provider,
)
from .version import __version__

# Auto-discover external providers at import time
discover_providers()

__all__ = [
    "register_provider",
    "get_provider",
    "list_providers",
    "discover_providers",
    "BaseTranslationProvider",
    "__version__",
]
