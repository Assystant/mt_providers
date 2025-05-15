# MT Providers

Extensible Machine Translation Providers Framework

## Installation

```bash
pip install mt-providers
```

## Usage

```python
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

# Configure provider
config = TranslationConfig(
    api_key="your-key",
    region="your-region"
)

# Get provider instance
translator = get_provider("microsoft")(config)

# Translate text
result = translator.translate(
    text="Hello world",
    source_lang="en-GB",
    target_lang="fr-FR"
)
print(result["translated_text"])
```

## Creating Custom Providers

1. Create your provider class:

```python
from mt_providers import BaseTranslationProvider

class MyProvider(BaseTranslationProvider):
    name = "my_provider"
    
    def translate(self, text, source_lang, target_lang):
        # Implementation
        pass
```

2. Register via entry points in your package's pyproject.toml:

```toml
[project.entry-points."mt_providers"]
my_provider = "my_package.module:MyProvider"
```