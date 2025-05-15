class TranslationError(Exception):
    """Base exception class for translation errors."""

    pass


class ProviderError(TranslationError):
    """Base exception for provider-related errors."""

    pass


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not found in the registry."""

    pass


class ConfigurationError(ProviderError):
    """Raised when there is an error in provider configuration."""

    pass


class ValidationError(TranslationError):
    """Raised when validation fails for inputs like language codes."""

    pass
