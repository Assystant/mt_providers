# MT Providers

[![Tests](https://img.shields.io/badge/tests-27%20passing-brightgreen)](https://github.com/assystant/mt-providers)
[![Coverage](https://img.shields.io/badge/coverage-77%25-brightgreen)](https://github.com/assystant/mt-providers)
[![Version](https://img.shields.io/badge/version-0.1.7-blue)](https://pypi.org/project/mt-providers/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://pypi.org/project/mt-providers/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Extensible Machine Translation Providers Framework

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features) 
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
  - [Async Usage](#async-usage)
- [Available Providers](#available-providers)
- [Provider Management](#provider-management)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Advanced Features](#advanced-features)
- [Documentation](#documentation)
- [Testing](#testing)
- [Performance](#performance)
- [Compatibility](#compatibility)
- [Contributing](#contributing)
- [License](#license)
- [Support & Community](#support--community)
- [Changelog](#changelog)
- [Roadmap](#roadmap)

## Overview

MT Providers is a unified framework for machine translation services that allows easy integration of different translation providers through a consistent interface. Whether you're building a small application or a large-scale translation service, MT Providers provides the flexibility and reliability you need.

## Key Features

- 🔌 **Plugin Architecture**: Easy integration of new translation providers
- 🔄 **Async Support**: Full async/await support with sync fallback
- 📊 **Batch Processing**: Efficient bulk translation capabilities
- 🛡️ **Rate Limiting**: Built-in rate limiting and retry logic
- 🎯 **Type Safety**: Complete type annotations with mypy support
- 🏥 **Health Checks**: Provider health monitoring and status checking
- 📝 **Comprehensive Logging**: Structured logging throughout
- 🧪 **Well Tested**: High test coverage and quality assurance

## Quick Start

### Installation

```bash
# Install the framework
pip install mt-providers

# Install providers (example with Microsoft Translator)
pip install mt-provider-microsoft
```

### Basic Usage

```python
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

# Configure your provider
config = TranslationConfig(
    api_key="your-api-key",
    region="westus2"  # Required for some providers like Microsoft
)

# Get a provider instance
translator = get_provider("microsoft")(config)

# Translate text
result = translator.translate("Hello world", "en", "es")
print(result["translated_text"])  # Output: ¡Hola mundo!

# Batch translation
texts = ["Hello", "World", "How are you?"]
results = translator.bulk_translate(texts, "en", "es")

for result in results:
    print(result["translated_text"])
```

### Async Usage

```python
import asyncio

async def async_translation():
    result = await translator.translate_async("Hello world", "en", "es")
    print(result["translated_text"])

asyncio.run(async_translation())
```

## Available Providers

| Provider | Package | Status | Features |
|----------|---------|---------|----------|
| Microsoft Translator | `mt-provider-microsoft` | ✅ Available | Sync/Async, Batch, Rate Limiting |
| Google Translate | `mt-provider-google` | 🚧 Coming Soon | High-quality neural translations |
| Amazon Translate | `mt-provider-amazon` | 🚧 Coming Soon | AWS ecosystem integration |
| DeepL | `mt-provider-deepl` | 🚧 Coming Soon | Premium translation quality |

## Provider Management

```python
from mt_providers import list_providers, discover_providers

# List all available providers  
providers = list_providers()
print(f"Available providers: {providers}")  # ['microsoft']

# Discover providers from entry points
discovered = discover_providers()
print(f"Discovered providers: {discovered}")

# Check provider health
from mt_providers.registry import check_provider_health
is_healthy = await check_provider_health("microsoft", config)
print(f"Provider healthy: {is_healthy}")
```

## Configuration

### Basic Configuration

```python
from mt_providers.types import TranslationConfig

config = TranslationConfig(
    api_key="your-api-key",
    region="your-region",        # Provider-specific
    timeout=30,                  # Request timeout in seconds
    rate_limit=10,              # Requests per second
    retry_attempts=3,           # Number of retries
    retry_backoff=1.0          # Backoff multiplier
)
```

### Environment-Based Configuration

```python
import os

config = TranslationConfig(
    api_key=os.getenv("TRANSLATION_API_KEY"),
    region=os.getenv("TRANSLATION_REGION", "westus2"),
    rate_limit=int(os.getenv("TRANSLATION_RATE_LIMIT", "10"))
)
```

## Error Handling

```python
from mt_providers.exceptions import (
    ProviderNotFoundError, 
    ConfigurationError,
    TranslationError
)
from mt_providers.types import TranslationStatus

try:
    translator = get_provider("microsoft")(config)
    result = translator.translate("Hello", "en", "es")
    
    if result["status"] == TranslationStatus.SUCCESS:
        print(f"Translation: {result['translated_text']}")
    else:
        print(f"Translation failed: {result['error']}")
        
except ProviderNotFoundError:
    print("Provider not found")
except ConfigurationError:
    print("Configuration error")
except TranslationError:
    print("Translation error")
```

## Advanced Features

### Rate Limiting

```python
# Configure rate limiting
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    rate_limit=100  # 100 requests per second
)

# Rate limiting is automatically applied
results = translator.bulk_translate(large_text_list, "en", "es")
```

### Custom Provider Development

```python
from mt_providers import BaseTranslationProvider
from mt_providers.types import TranslationResponse

class MyProvider(BaseTranslationProvider):
    name = "my_provider"
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResponse:
        # Your implementation here
        return self._create_response(
            translated_text="translated text",
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(text)
        )
```

Register via entry points in `pyproject.toml`:

```toml
[project.entry-points."mt_providers"]
my_provider = "my_package.module:MyProvider"
```

## Documentation

Comprehensive documentation is available to help you get started and master the framework:

- 📚 **[API Reference](docs/api_reference.md)** - Complete API documentation for all classes and methods
- 🔧 **[Provider Integration Guide](docs/provider_integration_guide.md)** - Step-by-step guide for creating custom providers  
- 📖 **[Usage Examples](docs/usage_examples.md)** - Practical examples and tutorials for common use cases
- ⚙️ **[Configuration Guide](docs/configuration_guide.md)** - Detailed configuration options and best practices
- 🏗️ **[Architectural Decisions](docs/architectural_decisions.md)** - Design decisions and framework architecture

### Quick Links
- [Getting Started Tutorial](docs/usage_examples.md#getting-started)
- [Creating Your First Provider](docs/provider_integration_guide.md#quick-start)
- [Configuration Examples](docs/configuration_guide.md#common-configurations)
- [Error Handling Patterns](docs/usage_examples.md#error-handling)
- [Performance Optimization](docs/usage_examples.md#performance-tips)

## Testing

The framework includes comprehensive test coverage ensuring reliability and stability:

```bash
# Run all tests
pytest

# Run with coverage report  
pytest --cov=mt_providers --cov-report=html

# Run specific test categories
pytest tests/test_integration.py  # Integration tests
pytest tests/test_provider.py     # Provider tests  
pytest tests/test_registry.py     # Registry tests

# Type checking
mypy mt_providers

# Code formatting and linting
black mt_providers
isort mt_providers
```

### Test Coverage
- **Total Tests**: 27 tests covering all major functionality
- **Coverage**: 77% code coverage (207 statements, 48 uncovered)
- **Test Categories**: Unit, Integration, Performance, and Regression tests
- **Continuous Integration**: Automated testing on multiple Python versions

## Performance

MT Providers is optimized for high-performance translation workloads with enterprise-grade capabilities:

- **⚡ Fast Provider Discovery**: Sub-millisecond provider lookup and instantiation
- **📦 Efficient Batch Processing**: Automatic request chunking and parallel processing
- **🔗 Connection Pooling**: HTTP connection reuse for reduced latency
- **⚡ Async Support**: Non-blocking operations with asyncio for maximum concurrency
- **🛡️ Smart Rate Limiting**: Configurable rate limiting that respects API quotas
- **📊 Performance Monitoring**: Built-in benchmarking and health check capabilities
- **🚀 Memory Efficient**: Optimized memory usage for large-scale deployments

### Benchmarks
- Provider discovery: ~0.005 seconds for full registry scan
- Provider instantiation: <0.001 seconds average
- Memory footprint: Minimal overhead per provider instance
- Concurrent operations: Scales linearly with available resources

## Compatibility

- **Python**: 3.8+ (3.10+ recommended for optimal performance)
- **Type Checking**: Full mypy support with comprehensive type annotations
- **Async**: Native asyncio compatibility with automatic sync fallback
- **Frameworks**: Seamless integration with Flask, Django, FastAPI, Starlette
- **Platforms**: Cross-platform support (Linux, macOS, Windows)
- **Packaging**: Standard Python packaging with wheel and source distributions

## Contributing

We welcome contributions! The MT Providers framework is designed to be extensible and community-driven.

### How to Contribute
1. **Fork the repository** and create your feature branch
2. **Add comprehensive tests** for new functionality  
3. **Update documentation** for any API changes
4. **Ensure all tests pass** and maintain code coverage
5. **Follow code style guidelines** (black, isort, mypy)
6. **Submit a pull request** with a clear description

### Areas for Contribution
- 🔌 New translation provider implementations
- 📚 Documentation improvements and examples
- 🧪 Additional test coverage and edge cases
- ⚡ Performance optimizations and benchmarks
- 🐛 Bug fixes and issue resolution

### Development Setup

```bash
# Clone the repository
git clone https://github.com/assystant/mt-providers.git
cd mt-providers

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install development dependencies
pip install -e .[test,dev]

# Run tests
pytest

# Run type checking
mypy mt_providers

# Format code
black mt_providers
isort mt_providers
```

### Project Structure
```
mt_providers/
├── mt_providers/          # Core framework code
│   ├── base.py           # Base provider class
│   ├── registry.py       # Provider discovery and registration
│   ├── types.py          # Type definitions
│   ├── exceptions.py     # Custom exceptions
│   └── utils.py          # Utility functions
├── tests/                # Comprehensive test suite
├── docs/                 # Documentation
└── examples/             # Usage examples
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support & Community

- 📧 **Email**: [support@assystant.com](mailto:support@assystant.com)
- 🐛 **Issues**: [GitHub Issues](https://github.com/assystant/mt-providers/issues) - Report bugs and request features
- 💬 **Discussions**: [GitHub Discussions](https://github.com/assystant/mt-providers/discussions) - Ask questions and share ideas
- 📖 **Documentation**: Comprehensive guides available in the [docs/](docs/) directory
- 🎯 **Examples**: Practical examples in [docs/usage_examples.md](docs/usage_examples.md)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed information about changes in each version.

## Roadmap

### Current Status
- ✅ **Core Framework**: Complete with plugin architecture
- ✅ **Microsoft Translator**: Full implementation with async support
- ✅ **Documentation**: Comprehensive guides and API reference
- ✅ **Testing**: 77% coverage with 27 tests
- ✅ **Type Safety**: Full mypy compliance
- ✅ **Performance**: Optimized for production workloads

### Upcoming Features
- 🚧 **Google Translate Provider**: High-quality neural translations
- 🚧 **Amazon Translate Provider**: AWS ecosystem integration  
- 🚧 **DeepL Provider**: Premium translation quality
- 🚧 **Caching Layer**: Redis/Memcached response caching
- 🚧 **Translation Memory**: Integration with TMX files
- 🚧 **Streaming Support**: Real-time translation capabilities
- 🚧 **Metrics & Observability**: Detailed performance monitoring
- 🚧 **CLI Tools**: Command-line interface for batch operations