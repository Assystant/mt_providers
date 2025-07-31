# Architectural Decision Records (ADRs)

This document contains the architectural decisions made during the development of the MT Providers framework.

## ADR-001: Plugin Architecture with Entry Points

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

We need a way to allow third-party developers to create translation providers that can be automatically discovered and integrated into the framework without modifying the core code.

### Decision

We will use Python's entry points mechanism for plugin discovery and registration.

### Rationale

- **Automatic Discovery**: Entry points allow automatic discovery of installed providers
- **Loose Coupling**: Core framework doesn't need to know about specific providers
- **Standard Approach**: Entry points are a well-established Python packaging pattern
- **Easy Installation**: Providers can be installed as separate packages via pip

### Implementation

```python
# In provider package's pyproject.toml
[project.entry-points."mt_providers"]
microsoft = "mt_provider_microsoft:MicrosoftTranslator"
```

```python
# In framework registry
def discover_providers():
    entry_points = metadata.entry_points().get("mt_providers", [])
    for entry_point in entry_points:
        provider_class = entry_point.load()
        register_provider(provider_class.name, provider_class)
```

### Consequences

**Positive:**
- Easy to add new providers
- No core code changes needed for new providers
- Standard Python packaging workflow

**Negative:**
- Requires understanding of entry points for provider developers
- Discovery happens at import time

## ADR-002: Standardized Response Format

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

Different translation APIs return results in different formats. We need a consistent interface for consumers of the framework.

### Decision

All translation operations will return a standardized `TranslationResponse` TypedDict.

### Rationale

- **Consistency**: Same interface regardless of underlying provider
- **Type Safety**: TypedDict provides static type checking
- **Extensibility**: Metadata field allows provider-specific information
- **Error Handling**: Standardized error reporting

### Implementation

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

### Consequences

**Positive:**
- Consistent API for all providers
- Easy to switch between providers
- Rich metadata available

**Negative:**
- Some provider-specific features may need to go in metadata
- All providers must conform to this structure

## ADR-003: Async Support with Fallback

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

Some applications need async support for better concurrency, but not all providers may implement async methods. We need to support both sync and async usage patterns.

### Decision

Providers can optionally implement async methods. If not implemented, the framework provides a fallback using `run_in_executor`.

### Rationale

- **Flexibility**: Providers choose whether to implement async
- **Compatibility**: Sync-only providers work in async contexts
- **Performance**: Native async implementations can be more efficient
- **Migration**: Easy to upgrade from sync to async

### Implementation

```python
async def translate_async(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
    if not self.supports_async:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.translate, text, source_lang, target_lang)
    raise NotImplementedError("Async translation not implemented")
```

### Consequences

**Positive:**
- Works for both sync and async applications
- Gradual migration path
- No breaking changes

**Negative:**
- Fallback may not be as efficient as native async
- Additional complexity in base class

## ADR-004: Configuration via Data Classes

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

Providers need various configuration options (API keys, endpoints, timeouts, etc.). We need a type-safe and extensible way to handle configuration.

### Decision

Use a `@dataclass` for configuration with sensible defaults and validation.

### Rationale

- **Type Safety**: Static type checking for configuration
- **Defaults**: Sensible defaults reduce configuration burden
- **Validation**: Can validate configuration in provider constructor
- **Documentation**: Self-documenting through type hints

### Implementation

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

### Consequences

**Positive:**
- Type-safe configuration
- Clear documentation of options
- Easy to extend

**Negative:**
- All providers share same configuration class
- Provider-specific options must fit this structure

## ADR-005: Exception Hierarchy

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

We need a clear way to handle different types of errors that can occur during translation operations.

### Decision

Create a hierarchy of custom exceptions with specific error types.

### Rationale

- **Error Handling**: Applications can catch specific error types
- **Debugging**: Clear error messages and types
- **API Design**: Consistent error reporting
- **Recovery**: Different errors may need different recovery strategies

### Implementation

```python
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
```

### Consequences

**Positive:**
- Clear error handling patterns
- Easy to catch specific error types
- Good debugging experience

**Negative:**
- More exception classes to maintain
- Need to map provider errors to framework errors

## ADR-006: Rate Limiting at Provider Level

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

Different translation APIs have different rate limits. Applications need to respect these limits to avoid being blocked.

### Decision

Implement rate limiting at the provider level using async locks and configurable limits.

### Rationale

- **API Compliance**: Respect provider rate limits
- **Configurability**: Different limits for different use cases
- **Async Safe**: Works correctly in async contexts
- **Provider Specific**: Each provider can have different limits

### Implementation

```python
async def _handle_rate_limit(self) -> None:
    if not self.config.rate_limit:
        return
    
    if self._rate_limit_lock is None:
        self._rate_limit_lock = asyncio.Lock()
    
    async with self._rate_limit_lock:
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            wait_time = (1.0 / self.config.rate_limit) - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        self._last_request_time = time.time()
```

### Consequences

**Positive:**
- Automatic rate limiting
- Prevents API blocks
- Configurable per provider

**Negative:**
- Adds complexity to providers
- May slow down operations

## ADR-007: Bulk Translation Support

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

Translating many texts individually is inefficient. Most APIs support batch operations that are more efficient.

### Decision

All providers must implement `bulk_translate` method. Default implementation calls `translate` for each text, but providers can optimize.

### Rationale

- **Performance**: Batch operations are more efficient
- **Consistency**: Same interface for single and batch operations
- **Flexibility**: Providers can optimize or use default
- **API Efficiency**: Reduces number of API calls

### Implementation

```python
def bulk_translate(self, texts: List[str], source_lang: str, target_lang: str) -> List[TranslationResponse]:
    """Default implementation - override for better performance."""
    return [self.translate(text, source_lang, target_lang) for text in texts]
```

### Consequences

**Positive:**
- Better performance for bulk operations
- Consistent API for all providers
- Easy to optimize per provider

**Negative:**
- All providers must implement this method
- Default implementation may not be optimal

## ADR-008: Thread-Safe Registry

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

The provider registry may be accessed from multiple threads. We need to ensure thread safety for registration and access operations.

### Decision

Use threading locks for registry modifications and LRU cache for provider lookups.

### Rationale

- **Thread Safety**: Multiple threads can safely register/access providers
- **Performance**: LRU cache speeds up repeated lookups
- **Concurrency**: Applications can use providers from multiple threads
- **Safety**: Prevents race conditions during registration

### Implementation

```python
import threading
from functools import lru_cache

_registry_lock = threading.Lock()
PROVIDER_REGISTRY: Dict[str, Type[BaseTranslationProvider]] = {}

def register_provider(name: str, cls: Type[BaseTranslationProvider]) -> None:
    with _registry_lock:
        PROVIDER_REGISTRY[name] = cls

@lru_cache(maxsize=None)
def get_provider(name: str) -> Type[BaseTranslationProvider]:
    return PROVIDER_REGISTRY[name]
```

### Consequences

**Positive:**
- Thread-safe operations
- Fast provider lookups
- Supports concurrent applications

**Negative:**
- Slight overhead from locking
- Cache needs to be cleared on registry changes

## ADR-009: Language Code Validation

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

Different providers support different language code formats. We need to validate input while allowing provider-specific mappings.

### Decision

Implement basic language code validation with utility functions for normalization and validation.

### Rationale

- **Input Validation**: Catch invalid language codes early
- **Standardization**: Consistent language code format
- **Provider Flexibility**: Providers can map to their specific codes
- **Error Prevention**: Reduce API errors from invalid codes

### Implementation

```python
def validate_language_code(code: str) -> bool:
    """Validate language code format."""
    pattern = r"^[a-z]{2,3}(-[A-Z][a-z]{3})?(-[A-Z]{2})?$"
    return bool(re.match(pattern, code))

def normalize_language_code(code: str) -> str:
    """Normalize language code to standard format."""
    if not validate_language_code(code):
        raise ValidationError(f"Invalid language code: {code}")
    return code.lower()
```

### Consequences

**Positive:**
- Early error detection
- Consistent language code handling
- Provider flexibility

**Negative:**
- May reject some valid provider-specific codes
- Additional validation overhead

## ADR-010: Provider Health Checking

**Status:** Accepted  
**Date:** 2024-05-15  
**Deciders:** Development Team  

### Context

Applications may want to check if a provider is operational before using it, especially in production environments.

### Decision

Implement a health check function that attempts a simple translation to verify provider status.

### Rationale

- **Monitoring**: Applications can monitor provider health
- **Failover**: Can switch providers if one is down
- **Debugging**: Easy to test provider configuration
- **Production Ready**: Essential for production deployments

### Implementation

```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def check_provider_health(name: str, config: TranslationConfig, test_text: str = "test") -> bool:
    try:
        provider = get_provider(name)(config)
        if provider.supports_async:
            result = await provider.translate_async(test_text, "en", "fr")
        else:
            result = provider.translate(test_text, "en", "fr")
        return result.get("status") == TranslationStatus.SUCCESS
    except Exception:
        return False
```

### Consequences

**Positive:**
- Easy health monitoring
- Production readiness
- Supports debugging

**Negative:**
- Consumes API quota for health checks
- May be slower than desired for frequent checks

## Future ADRs

The following decisions may need to be made in future versions:

- **ADR-011**: Caching Strategy for Translations
- **ADR-012**: Metrics and Observability
- **ADR-013**: Provider Priority and Fallback
- **ADR-014**: Streaming Translation Support
- **ADR-015**: Translation Memory Integration
