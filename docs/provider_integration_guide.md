# Provider Integration Guide

This guide walks you through creating a new translation provider for the MT Providers framework.

## Quick Start

### 1. Create Your Provider Class

```python
from mt_providers import BaseTranslationProvider
from mt_providers.types import TranslationConfig, TranslationResponse
import requests

class MyTranslationProvider(BaseTranslationProvider):
    name = "my_provider"
    requires_region = False  # Set to True if your API requires a region
    supports_async = False   # Set to True if you implement async methods
    max_chunk_size = 5000   # Maximum characters per request
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
        """Implement single text translation."""
        try:
            # Your API call here
            response = requests.post(
                "https://api.example.com/translate",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={
                    "text": text,
                    "source": source_lang,
                    "target": target_lang
                },
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            return self._create_response(
                translated_text=result["translated_text"],
                source_lang=source_lang,
                target_lang=target_lang,
                char_count=len(text),
                metadata={"confidence": result.get("confidence")}
            )
            
        except Exception as e:
            return self._create_response(
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                char_count=len(text),
                error=str(e)
            )
```

### 2. Package Structure

Create a new package with this structure:

```
my_translation_provider/
├── pyproject.toml
├── README.md
├── LICENSE
├── my_translation_provider/
│   ├── __init__.py
│   └── provider.py
└── tests/
    └── test_provider.py
```

### 3. Configure Entry Points

In your `pyproject.toml`:

```toml
[project.entry-points."mt_providers"]
my_provider = "my_translation_provider:MyTranslationProvider"
```

## Detailed Implementation

### Provider Configuration

#### Required Attributes

```python
class MyProvider(BaseTranslationProvider):
    name = "my_provider"              # Unique identifier
    requires_region = False           # Does API need region?
    supports_async = True             # Do you support async?
    max_chunk_size = 5000            # Max chars per request
    min_supported_version = "0.1.0"   # Min framework version
```

#### Configuration Validation

Override `validate_config()` for custom validation:

```python
def validate_config(self) -> None:
    """Validate provider-specific configuration."""
    super().validate_config()  # Validates api_key
    
    if not self.config.endpoint:
        raise ConfigurationError("Endpoint URL is required")
    
    if self.requires_region and not self.config.region:
        raise ConfigurationError("Region is required for this provider")
```

### Translation Methods

#### Single Translation (Required)

```python
def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
    """Translate a single text."""
    # Implementation here
    pass
```

#### Bulk Translation (Optional)

```python
def bulk_translate(self, texts: List[str], source_lang: str, target_lang: str) -> List[TranslationResponse]:
    """Translate multiple texts efficiently."""
    # Default implementation calls translate() for each text
    # Override for better performance
    
    # Example batch API call:
    batch_data = {
        "texts": texts,
        "source": source_lang,
        "target": target_lang
    }
    
    response = requests.post(
        f"{self.config.endpoint}/batch",
        headers=self._get_headers(),
        json=batch_data,
        timeout=self.config.timeout
    )
    
    results = response.json()
    return [
        self._create_response(
            translated_text=result["text"],
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(texts[i])
        )
        for i, result in enumerate(results["translations"])
    ]
```

#### Async Translation (Optional)

```python
async def translate_async(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
    """Async translation implementation."""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{self.config.endpoint}/translate",
            headers=self._get_headers(),
            json={
                "text": text,
                "source": source_lang,
                "target": target_lang
            },
            timeout=self.config.timeout
        ) as response:
            result = await response.json()
            
            return self._create_response(
                translated_text=result["translated_text"],
                source_lang=source_lang,
                target_lang=target_lang,
                char_count=len(text)
            )
```

### Helper Methods

#### Creating Responses

Use `_create_response()` for consistent response format:

```python
# Success response
return self._create_response(
    translated_text="Translated text",
    source_lang=source_lang,
    target_lang=target_lang,
    char_count=len(text),
    metadata={"confidence": 0.95, "model": "v2"}
)

# Error response
return self._create_response(
    translated_text="",
    source_lang=source_lang,
    target_lang=target_lang,
    char_count=len(text),
    error="API error: Rate limit exceeded"
)
```

#### Rate Limiting

Use the built-in rate limiting:

```python
async def translate_async(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
    await self._handle_rate_limit()  # Enforces rate limiting
    
    # Your translation logic here
    pass
```

### Error Handling

#### Common Error Patterns

```python
def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
    try:
        # API call
        response = self._make_api_call(text, source_lang, target_lang)
        
        return self._create_response(
            translated_text=response["text"],
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(text)
        )
        
    except requests.exceptions.Timeout:
        return self._create_response(
            translated_text="",
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(text),
            error="Request timeout"
        )
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            error_msg = "Rate limit exceeded"
        elif e.response.status_code == 401:
            error_msg = "Authentication failed"
        else:
            error_msg = f"HTTP error: {e.response.status_code}"
            
        return self._create_response(
            translated_text="",
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(text),
            error=error_msg
        )
        
    except Exception as e:
        return self._create_response(
            translated_text="",
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(text),
            error=f"Unexpected error: {str(e)}"
        )
```

### Testing Your Provider

#### Basic Test Structure

```python
import pytest
from mt_providers.types import TranslationConfig, TranslationStatus
from my_translation_provider import MyTranslationProvider

@pytest.fixture
def provider():
    config = TranslationConfig(api_key="test-key")
    return MyTranslationProvider(config)

def test_translate_success(provider, requests_mock):
    # Mock API response
    requests_mock.post(
        "https://api.example.com/translate",
        json={"translated_text": "Hola mundo"}
    )
    
    result = provider.translate("Hello world", "en", "es")
    
    assert result["translated_text"] == "Hola mundo"
    assert result["status"] == TranslationStatus.SUCCESS
    assert result["provider"] == "my_provider"

def test_translate_error(provider, requests_mock):
    # Mock API error
    requests_mock.post(
        "https://api.example.com/translate",
        status_code=500
    )
    
    result = provider.translate("Hello world", "en", "es")
    
    assert result["status"] == TranslationStatus.FAILED
    assert result["error"] is not None

@pytest.mark.asyncio
async def test_translate_async(provider):
    if provider.supports_async:
        result = await provider.translate_async("Hello world", "en", "es")
        assert result["status"] == TranslationStatus.SUCCESS
```

### Package Configuration

#### pyproject.toml Example

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my_translation_provider"
version = "0.1.0"
description = "My Translation Provider for MT Providers Framework"
dependencies = [
    "mt_providers>=0.1.0,<0.2.0",
    "requests>=2.25.0",
    "aiohttp>=3.8.0",  # If supporting async
]

[project.optional-dependencies]
test = [
    "pytest>=6.0.0",
    "pytest-asyncio>=0.18.0",
    "requests-mock>=1.9.0",
]

[project.entry-points."mt_providers"]
my_provider = "my_translation_provider:MyTranslationProvider"

[tool.hatch.build.targets.wheel]
packages = ["my_translation_provider"]
```

### Advanced Features

#### Custom Language Code Mapping

```python
def _map_language_code(self, lang_code: str) -> str:
    """Map standard language codes to provider-specific codes."""
    mapping = {
        "zh-CN": "zh-hans",
        "zh-TW": "zh-hant",
        "pt-BR": "pt-br"
    }
    return mapping.get(lang_code, lang_code)

def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
    # Map language codes
    api_source = self._map_language_code(source_lang)
    api_target = self._map_language_code(target_lang)
    
    # Rest of implementation...
```

#### Request Chunking

```python
def bulk_translate(self, texts: List[str], source_lang: str, target_lang: str) -> List[TranslationResponse]:
    """Handle large batches by chunking."""
    results = []
    chunk_size = 100  # API limit
    
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i + chunk_size]
        chunk_results = self._translate_chunk(chunk, source_lang, target_lang)
        results.extend(chunk_results)
    
    return results
```

## Best Practices

### 1. Configuration

- Always validate configuration in `validate_config()`
- Use environment variables for API keys in tests
- Provide clear error messages for configuration issues

### 2. Error Handling

- Return appropriate error responses instead of raising exceptions
- Log errors for debugging but don't expose sensitive information
- Handle rate limiting gracefully

### 3. Performance

- Implement bulk translation when the API supports it
- Use connection pooling for multiple requests
- Respect API rate limits

### 4. Testing

- Mock all external API calls
- Test both success and error scenarios
- Include async tests if supporting async operations
- Test configuration validation

### 5. Documentation

- Document all configuration options
- Provide usage examples
- Specify API limits and requirements
- Include troubleshooting guide

## Publishing Your Provider

### 1. Package Testing

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Test discovery
python -c "from mt_providers import list_providers; print(list_providers())"
```

### 2. Build and Publish

```bash
# Build package
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

### 3. Documentation

Include in your README:

- Installation instructions
- Configuration options
- Usage examples
- API limits and requirements
- Support contact information

## Example: Complete Provider

See the `mt_provider_microsoft` package for a complete real-world example of a provider implementation with all features including:

- Sync and async support
- Bulk translation
- Rate limiting
- Comprehensive error handling
- Full test coverage
- Proper packaging and documentation
