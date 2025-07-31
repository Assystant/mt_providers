# Configuration Guide

This guide covers all configuration options and best practices for the MT Providers framework.

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [Provider-Specific Settings](#provider-specific-settings)
3. [Performance Tuning](#performance-tuning)
4. [Security Best Practices](#security-best-practices)
5. [Environment Configuration](#environment-configuration)
6. [Advanced Settings](#advanced-settings)

## Basic Configuration

### TranslationConfig Overview

The `TranslationConfig` class is the main configuration object for all providers:

```python
from mt_providers.types import TranslationConfig

config = TranslationConfig(
    api_key="your-api-key",           # Required: API key for the service
    endpoint=None,                    # Optional: Custom API endpoint
    region=None,                      # Optional: Service region (required for some providers)
    timeout=30,                       # Optional: Request timeout in seconds
    rate_limit=None,                  # Optional: Maximum requests per second
    retry_attempts=3,                 # Optional: Number of retry attempts
    retry_backoff=1.0                 # Optional: Backoff multiplier for retries
)
```

### Required vs Optional Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `api_key` | ✅ | - | Authentication key for the translation service |
| `endpoint` | ❌ | `None` | Custom API endpoint URL |
| `region` | ❌* | `None` | Service region (required for Microsoft Translator) |
| `timeout` | ❌ | `30` | Request timeout in seconds |
| `rate_limit` | ❌ | `None` | Maximum requests per second |
| `retry_attempts` | ❌ | `3` | Number of retry attempts on failure |
| `retry_backoff` | ❌ | `1.0` | Backoff multiplier for exponential retry |

*Required for some providers

## Provider-Specific Settings

### Microsoft Translator

Microsoft Translator requires specific configuration:

```python
config = TranslationConfig(
    api_key="your-subscription-key",          # Cognitive Services subscription key
    region="westus2",                         # Required: Azure region
    endpoint="https://api.cognitive.microsofttranslator.com/translate",  # Optional: custom endpoint
    timeout=60,                               # Recommended for batch operations
    rate_limit=100                            # Adjust based on your subscription tier
)
```

#### Microsoft-Specific Requirements

- **Region**: Always required for Microsoft Translator
- **API Key**: Use your Cognitive Services subscription key
- **Rate Limits**: Depend on your subscription tier:
  - Free tier: 2M characters/month
  - Standard: Based on your pricing tier

#### Common Microsoft Regions

```python
# Common Azure regions for Microsoft Translator
REGIONS = {
    "us_east": "eastus",
    "us_west": "westus2", 
    "europe": "westeurope",
    "asia": "eastasia",
    "australia": "australiaeast"
}

config = TranslationConfig(
    api_key="your-key",
    region=REGIONS["us_west"]
)
```

### Google Translate (Future Provider)

When Google Translate provider becomes available:

```python
config = TranslationConfig(
    api_key="your-google-api-key",
    endpoint="https://translation.googleapis.com/language/translate/v2",
    timeout=30,
    rate_limit=1000  # Google typically has higher rate limits
)
```

### Amazon Translate (Future Provider)

When Amazon Translate provider becomes available:

```python
config = TranslationConfig(
    api_key="your-access-key-id",
    region="us-east-1",               # AWS region
    timeout=30
)
```

## Performance Tuning

### Timeout Configuration

Choose timeouts based on your use case:

```python
# For single translations
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    timeout=10  # Short timeout for interactive applications
)

# For batch operations
config = TranslationConfig(
    api_key="your-key", 
    region="westus2",
    timeout=300  # Longer timeout for large batches
)

# For background processing
config = TranslationConfig(
    api_key="your-key",
    region="westus2", 
    timeout=600  # Very long timeout for bulk processing
)
```

### Rate Limiting

Configure rate limits to optimize throughput while respecting API limits:

```python
# Conservative rate limiting (good for shared APIs)
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    rate_limit=10  # 10 requests per second
)

# Aggressive rate limiting (for dedicated/high-tier subscriptions)
config = TranslationConfig(
    api_key="your-key",
    region="westus2", 
    rate_limit=100  # 100 requests per second
)

# No rate limiting (use provider's default limits)
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    rate_limit=None
)
```

### Retry Configuration

Configure retries for reliability:

```python
# Conservative retry settings
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    retry_attempts=3,     # Retry up to 3 times
    retry_backoff=2.0     # Double wait time between retries
)

# Aggressive retry settings (for unreliable networks)
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    retry_attempts=5,     # More retry attempts
    retry_backoff=1.5     # Shorter backoff
)

# No retries (for real-time applications)
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    retry_attempts=0      # No retries
)
```

## Security Best Practices

### API Key Management

Never hardcode API keys in your source code:

```python
# ❌ BAD: Hardcoded API key
config = TranslationConfig(
    api_key="sk-1234567890abcdef",  # Don't do this!
    region="westus2"
)

# ✅ GOOD: Environment variable
import os
config = TranslationConfig(
    api_key=os.getenv("TRANSLATION_API_KEY"),
    region=os.getenv("TRANSLATION_REGION", "westus2")
)

# ✅ GOOD: Configuration file (not in version control)
import json
with open("config.json") as f:
    settings = json.load(f)
    
config = TranslationConfig(
    api_key=settings["api_key"],
    region=settings["region"]
)

# ✅ GOOD: Secret management service
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://vault.vault.azure.net/", credential=credential)

config = TranslationConfig(
    api_key=client.get_secret("translation-api-key").value,
    region="westus2"
)
```

### Network Security

Configure secure endpoints and use HTTPS:

```python
# Always use HTTPS endpoints
config = TranslationConfig(
    api_key=os.getenv("TRANSLATION_API_KEY"),
    region="westus2",
    endpoint="https://api.cognitive.microsofttranslator.com/translate"  # HTTPS
)

# For corporate environments with proxies
import requests
session = requests.Session()
session.proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'https://proxy.company.com:8080'
}
# Note: Session configuration would be provider-specific
```

### Input Validation

Always validate input before translation:

```python
from mt_providers.utils import validate_language_code

def safe_translate(translator, text: str, source_lang: str, target_lang: str):
    """Safely translate with input validation."""
    
    # Validate language codes
    if not validate_language_code(source_lang):
        raise ValueError(f"Invalid source language code: {source_lang}")
    if not validate_language_code(target_lang):
        raise ValueError(f"Invalid target language code: {target_lang}")
    
    # Validate text length
    if len(text) > 10000:  # Adjust based on provider limits
        raise ValueError("Text too long for translation")
    
    # Sanitize text (remove potentially harmful content)
    sanitized_text = text.strip()
    if not sanitized_text:
        return {"translated_text": "", "status": "success"}
    
    return translator.translate(sanitized_text, source_lang, target_lang)
```

## Environment Configuration

### Development Environment

```python
# Development configuration
config = TranslationConfig(
    api_key=os.getenv("DEV_TRANSLATION_API_KEY", "test-key"),
    region=os.getenv("DEV_TRANSLATION_REGION", "westus2"),
    timeout=10,
    rate_limit=5,  # Lower rate limit for development
    retry_attempts=1  # Faster failure for debugging
)
```

### Staging Environment

```python
# Staging configuration
config = TranslationConfig(
    api_key=os.getenv("STAGING_TRANSLATION_API_KEY"),
    region=os.getenv("STAGING_TRANSLATION_REGION", "westus2"),
    timeout=30,
    rate_limit=50,
    retry_attempts=3
)
```

### Production Environment

```python
# Production configuration
config = TranslationConfig(
    api_key=os.getenv("PROD_TRANSLATION_API_KEY"),
    region=os.getenv("PROD_TRANSLATION_REGION"),
    timeout=60,
    rate_limit=100,
    retry_attempts=5,
    retry_backoff=2.0
)

# Validate required environment variables
required_vars = ["PROD_TRANSLATION_API_KEY", "PROD_TRANSLATION_REGION"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}")
```

### Configuration Factory

Create a configuration factory for different environments:

```python
import os
from enum import Enum
from mt_providers.types import TranslationConfig

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class ConfigFactory:
    """Factory for creating environment-specific configurations."""
    
    @staticmethod
    def create_config(env: Environment = None) -> TranslationConfig:
        """Create configuration based on environment."""
        
        # Auto-detect environment if not specified
        if env is None:
            env_name = os.getenv("ENVIRONMENT", "development").lower()
            try:
                env = Environment(env_name)
            except ValueError:
                env = Environment.DEVELOPMENT
        
        base_config = {
            "api_key": os.getenv("TRANSLATION_API_KEY"),
            "region": os.getenv("TRANSLATION_REGION", "westus2")
        }
        
        if env == Environment.DEVELOPMENT:
            return TranslationConfig(
                **base_config,
                timeout=10,
                rate_limit=5,
                retry_attempts=1
            )
        elif env == Environment.STAGING:
            return TranslationConfig(
                **base_config,
                timeout=30,
                rate_limit=50,
                retry_attempts=3
            )
        elif env == Environment.PRODUCTION:
            return TranslationConfig(
                **base_config,
                timeout=60,
                rate_limit=100,
                retry_attempts=5,
                retry_backoff=2.0
            )

# Usage
config = ConfigFactory.create_config(Environment.PRODUCTION)
```

## Advanced Settings

### Custom Endpoints

For enterprise or regional deployments:

```python
# Custom Microsoft Translator endpoint
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    endpoint="https://your-custom-endpoint.cognitive.microsofttranslator.com/translate"
)

# API Gateway endpoint
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    endpoint="https://api.yourcompany.com/translation/v1/translate"
)
```

### Multiple Provider Configuration

```python
from typing import Dict
from mt_providers import get_provider

class MultiProviderConfig:
    """Manage configurations for multiple providers."""
    
    def __init__(self):
        self.configs: Dict[str, TranslationConfig] = {}
    
    def add_provider_config(self, provider_name: str, config: TranslationConfig):
        """Add configuration for a provider."""
        self.configs[provider_name] = config
    
    def get_translator(self, provider_name: str):
        """Get configured translator for provider."""
        if provider_name not in self.configs:
            raise ValueError(f"No configuration for provider: {provider_name}")
        
        provider_class = get_provider(provider_name)
        return provider_class(self.configs[provider_name])

# Usage
multi_config = MultiProviderConfig()

# Add Microsoft configuration
microsoft_config = TranslationConfig(
    api_key=os.getenv("MICROSOFT_API_KEY"),
    region=os.getenv("MICROSOFT_REGION")
)
multi_config.add_provider_config("microsoft", microsoft_config)

# Add other providers as needed
# google_config = TranslationConfig(api_key=os.getenv("GOOGLE_API_KEY"))
# multi_config.add_provider_config("google", google_config)

# Get translator
translator = multi_config.get_translator("microsoft")
```

### Configuration Validation

```python
from mt_providers.exceptions import ConfigurationError

def validate_config(config: TranslationConfig, provider_name: str) -> None:
    """Validate configuration for specific provider."""
    
    if not config.api_key:
        raise ConfigurationError("API key is required")
    
    if provider_name == "microsoft":
        if not config.region:
            raise ConfigurationError("Region is required for Microsoft Translator")
        
        valid_regions = ["eastus", "westus2", "westeurope", "eastasia"]
        if config.region not in valid_regions:
            raise ConfigurationError(f"Invalid region for Microsoft: {config.region}")
    
    if config.timeout and config.timeout < 1:
        raise ConfigurationError("Timeout must be at least 1 second")
    
    if config.rate_limit and config.rate_limit <= 0:
        raise ConfigurationError("Rate limit must be positive")
    
    if config.retry_attempts < 0:
        raise ConfigurationError("Retry attempts cannot be negative")

# Usage
try:
    validate_config(config, "microsoft")
    translator = get_provider("microsoft")(config)
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

### Logging Configuration

```python
import logging
from mt_providers.logging import configure_logging

# Configure framework logging
configure_logging(level=logging.INFO)

# Custom logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log'),
        logging.StreamHandler()
    ]
)

# Provider-specific logging
logger = logging.getLogger("mt_providers")
logger.setLevel(logging.DEBUG)  # Debug level for troubleshooting
```

## Configuration Templates

### Basic Template

```python
# basic_config.py
import os
from mt_providers.types import TranslationConfig

def get_basic_config():
    return TranslationConfig(
        api_key=os.getenv("TRANSLATION_API_KEY"),
        region=os.getenv("TRANSLATION_REGION", "westus2"),
        timeout=30
    )
```

### Production Template

```python
# production_config.py
import os
from mt_providers.types import TranslationConfig
from mt_providers.exceptions import ConfigurationError

def get_production_config():
    # Validate required environment variables
    api_key = os.getenv("TRANSLATION_API_KEY")
    if not api_key:
        raise ConfigurationError("TRANSLATION_API_KEY environment variable is required")
    
    region = os.getenv("TRANSLATION_REGION")
    if not region:
        raise ConfigurationError("TRANSLATION_REGION environment variable is required")
    
    return TranslationConfig(
        api_key=api_key,
        region=region,
        timeout=int(os.getenv("TRANSLATION_TIMEOUT", "60")),
        rate_limit=int(os.getenv("TRANSLATION_RATE_LIMIT", "100")),
        retry_attempts=int(os.getenv("TRANSLATION_RETRY_ATTEMPTS", "5")),
        retry_backoff=float(os.getenv("TRANSLATION_RETRY_BACKOFF", "2.0"))
    )
```

### Docker Template

```yaml
# docker-compose.yml
version: '3.8'
services:
  translator:
    image: your-app:latest
    environment:
      - TRANSLATION_API_KEY=${TRANSLATION_API_KEY}
      - TRANSLATION_REGION=${TRANSLATION_REGION:-westus2}
      - TRANSLATION_TIMEOUT=${TRANSLATION_TIMEOUT:-60}
      - TRANSLATION_RATE_LIMIT=${TRANSLATION_RATE_LIMIT:-100}
    env_file:
      - .env
```

```bash
# .env file
TRANSLATION_API_KEY=your-actual-api-key
TRANSLATION_REGION=westus2
TRANSLATION_TIMEOUT=60
TRANSLATION_RATE_LIMIT=100
```

This configuration guide provides comprehensive coverage of all configuration options and best practices for the MT Providers framework. Use these examples as templates for your specific use case and environment.
