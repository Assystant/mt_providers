# MT Providers API Reference

## Overview

The MT Providers framework provides a unified interface for machine translation services. This document contains the complete API reference for developers.

## Core Components

### BaseTranslationProvider

Abstract base class that all translation providers must inherit from.

```python
from mt_providers import BaseTranslationProvider
from mt_providers.types import TranslationConfig, TranslationResponse

class MyProvider(BaseTranslationProvider):
    name = "my_provider"
    requires_region = False
    supports_async = True
    max_chunk_size = 5000
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
        # Implementation here
        pass
```

#### Required Attributes

- `name` (str): Unique identifier for the provider
- `requires_region` (bool): Whether provider requires a region parameter
- `supports_async` (bool): Whether provider supports async operations
- `max_chunk_size` (int): Maximum characters per translation request

#### Required Methods

- `translate(text, source_lang, target_lang)`: Translate a single text
- `bulk_translate(texts, source_lang, target_lang)`: Translate multiple texts
- `translate_async(text, source_lang, target_lang)`: Async translation (optional)

### Registry Functions

#### register_provider(name, provider_class)

Register a translation provider with the framework.

**Parameters:**
- `name` (str): Unique identifier for the provider
- `provider_class` (Type[BaseTranslationProvider]): Provider class

**Raises:**
- `ProviderError`: If provider name is already registered or class is invalid

#### get_provider(name)

Get a registered provider by name.

**Parameters:**
- `name` (str): Name of the provider to retrieve

**Returns:**
- `Type[BaseTranslationProvider]`: The provider class

**Raises:**
- `ProviderNotFoundError`: If provider is not found

#### discover_providers(entry_point_group="mt_providers")

Discover and register providers from entry points.

**Parameters:**
- `entry_point_group` (str): Entry point group name
- `raise_errors` (bool): Whether to raise exceptions on errors

**Returns:**
- `List[str]`: List of successfully registered provider names

#### list_providers()

List all registered provider names.

**Returns:**
- `List[str]`: Sorted list of provider names

### Type Definitions

#### TranslationConfig

Configuration object for translation providers.

```python
@dataclass
class TranslationConfig:
    api_key: str
    endpoint: Optional[str] = None
    region: Optional[str] = None
    timeout: int = 30
    rate_limit: Optional[int] = None
    retry_attempts: int = 3
    retry_backoff: float = 1.0
```

#### TranslationResponse

Standardized response from translation operations.

```python
class TranslationResponse(TypedDict):
    translated_text: str
    source_lang: str
    target_lang: str
    provider: str
    char_count: int
    status: TranslationStatus
    error: Optional[str]
    request_id: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

#### TranslationStatus

Enumeration of translation statuses.

```python
class TranslationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
```

### Exception Hierarchy

```
TranslationError (base)
├── ProviderError
│   ├── ProviderNotFoundError
│   └── ConfigurationError
└── ValidationError
```

#### TranslationError

Base exception class for all translation-related errors.

#### ProviderError

Base exception for provider-related errors.

#### ProviderNotFoundError

Raised when a requested provider is not found in the registry.

#### ConfigurationError

Raised when there is an error in provider configuration.

#### ValidationError

Raised when validation fails for inputs like language codes.

## Usage Examples

### Basic Usage

```python
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

# Configure provider
config = TranslationConfig(
    api_key="your-api-key",
    region="your-region"
)

# Get provider instance
translator = get_provider("microsoft")(config)

# Translate text
result = translator.translate("Hello world", "en", "es")
print(result["translated_text"])  # "¡Hola mundo!"
```

### Batch Translation

```python
texts = ["Hello", "World", "How are you?"]
results = translator.bulk_translate(texts, "en", "es")

for result in results:
    print(f"{result['translated_text']} (status: {result['status']})")
```

### Async Translation

```python
import asyncio

async def translate_async():
    result = await translator.translate_async("Hello world", "en", "es")
    print(result["translated_text"])

asyncio.run(translate_async())
```

### Error Handling

```python
from mt_providers.exceptions import ProviderNotFoundError, ConfigurationError

try:
    translator = get_provider("nonexistent")
except ProviderNotFoundError as e:
    print(f"Provider not found: {e}")

try:
    config = TranslationConfig(api_key="")  # Invalid config
    translator = get_provider("microsoft")(config)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Utility Functions

### Language Code Validation

```python
from mt_providers.utils import validate_language_code, normalize_language_code

# Validate language codes
assert validate_language_code("en-US") == True
assert validate_language_code("invalid") == False

# Normalize language codes
normalized = normalize_language_code("en-US")  # Returns "en-us"
```

## Provider Health Checking

```python
from mt_providers.registry import check_provider_health
from mt_providers.types import TranslationConfig

config = TranslationConfig(api_key="test-key")
is_healthy = await check_provider_health("microsoft", config)
```

## Performance Considerations

- Use `bulk_translate()` for multiple texts to reduce API calls
- Configure appropriate `rate_limit` to avoid hitting API limits
- Set reasonable `timeout` values for network requests
- Use async methods when available for better concurrency
