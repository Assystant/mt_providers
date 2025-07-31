# Usage Examples and Tutorials

This document provides comprehensive examples and tutorials for using the MT Providers framework.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Translation](#basic-translation)
3. [Batch Translation](#batch-translation)
4. [Async Translation](#async-translation)
5. [Error Handling](#error-handling)
6. [Advanced Configuration](#advanced-configuration)
7. [Real-World Examples](#real-world-examples)

## Quick Start

### Installation

```bash
# Install the framework
pip install mt-providers

# Install specific providers
pip install mt-provider-microsoft
```

### Basic Setup

```python
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

# Configure your provider
config = TranslationConfig(
    api_key="your-api-key",
    region="your-region"  # Required for some providers like Microsoft
)

# Get a provider instance
translator = get_provider("microsoft")(config)

# Translate text
result = translator.translate("Hello world", "en", "es")
print(result["translated_text"])  # Output: ¡Hola mundo!
```

## Basic Translation

### Single Text Translation

```python
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

# Setup
config = TranslationConfig(api_key="your-key", region="westus2")
translator = get_provider("microsoft")(config)

# Simple translation
result = translator.translate(
    text="Hello, how are you?",
    source_lang="en",
    target_lang="es"
)

print(f"Original: {result['translated_text']}")
print(f"Status: {result['status']}")
print(f"Characters: {result['char_count']}")
print(f"Provider: {result['provider']}")
```

### Working with Different Languages

```python
# English to Spanish
en_to_es = translator.translate("Good morning", "en", "es")
print(en_to_es["translated_text"])  # Buenos días

# French to English
fr_to_en = translator.translate("Bonjour le monde", "fr", "en")
print(fr_to_en["translated_text"])  # Hello world

# Chinese to English
zh_to_en = translator.translate("你好世界", "zh", "en")
print(zh_to_en["translated_text"])  # Hello world

# Auto-detect source language (if supported)
auto_to_en = translator.translate("Hola mundo", "auto", "en")
print(auto_to_en["translated_text"])  # Hello world
```

## Batch Translation

### Translating Multiple Texts

```python
# List of texts to translate
texts = [
    "Hello world",
    "How are you?", 
    "Good morning",
    "Thank you very much"
]

# Batch translate
results = translator.bulk_translate(texts, "en", "es")

# Process results
for i, result in enumerate(results):
    if result["status"] == "success":
        print(f"'{texts[i]}' -> '{result['translated_text']}'")
    else:
        print(f"Error translating '{texts[i]}': {result['error']}")
```

### Processing Large Datasets

```python
import csv
from typing import List, Dict

def translate_csv_file(input_file: str, output_file: str, 
                      source_col: str, target_col: str,
                      source_lang: str, target_lang: str):
    """Translate a CSV file with batch processing."""
    
    # Read input file
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Extract texts to translate
    texts = [row[source_col] for row in rows]
    
    # Batch translate (processes in chunks automatically)
    translations = translator.bulk_translate(texts, source_lang, target_lang)
    
    # Add translations to rows
    for i, translation in enumerate(translations):
        if translation["status"] == "success":
            rows[i][target_col] = translation["translated_text"]
        else:
            rows[i][target_col] = f"ERROR: {translation['error']}"
            rows[i][f"{target_col}_error"] = translation["error"]
    
    # Write output file
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

# Example usage
translate_csv_file(
    input_file="products.csv",
    output_file="products_translated.csv",
    source_col="description",
    target_col="description_es",
    source_lang="en",
    target_lang="es"
)
```

## Async Translation

### Basic Async Usage

```python
import asyncio
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

async def async_translation_example():
    config = TranslationConfig(api_key="your-key", region="westus2")
    translator = get_provider("microsoft")(config)
    
    # Single async translation
    result = await translator.translate_async("Hello world", "en", "es")
    print(result["translated_text"])

# Run the async function
asyncio.run(async_translation_example())
```

### Concurrent Translations

```python
import asyncio
from typing import List

async def translate_concurrent(translator, texts: List[str], 
                             source_lang: str, target_lang: str):
    """Translate multiple texts concurrently."""
    
    # Create tasks for concurrent execution
    tasks = [
        translator.translate_async(text, source_lang, target_lang)
        for text in texts
    ]
    
    # Wait for all translations to complete
    results = await asyncio.gather(*tasks)
    
    return results

async def concurrent_example():
    config = TranslationConfig(api_key="your-key", region="westus2")
    translator = get_provider("microsoft")(config)
    
    texts = [
        "Hello world",
        "How are you?",
        "Good morning",
        "Thank you"
    ]
    
    # Translate concurrently
    results = await translate_concurrent(translator, texts, "en", "es")
    
    for text, result in zip(texts, results):
        print(f"'{text}' -> '{result['translated_text']}'")

asyncio.run(concurrent_example())
```

### Rate-Limited Async Processing

```python
import asyncio
from asyncio import Semaphore

async def rate_limited_translation(translator, texts: List[str],
                                 source_lang: str, target_lang: str,
                                 max_concurrent: int = 5):
    """Translate with rate limiting."""
    
    semaphore = Semaphore(max_concurrent)
    
    async def translate_one(text: str):
        async with semaphore:
            return await translator.translate_async(text, source_lang, target_lang)
    
    tasks = [translate_one(text) for text in texts]
    return await asyncio.gather(*tasks)

# Usage
async def rate_limited_example():
    config = TranslationConfig(
        api_key="your-key", 
        region="westus2",
        rate_limit=10  # 10 requests per second
    )
    translator = get_provider("microsoft")(config)
    
    large_text_list = ["Text " + str(i) for i in range(100)]
    
    results = await rate_limited_translation(
        translator, large_text_list, "en", "es", max_concurrent=5
    )
    
    print(f"Translated {len(results)} texts")

asyncio.run(rate_limited_example())
```

## Error Handling

### Basic Error Handling

```python
from mt_providers.exceptions import ProviderNotFoundError, ConfigurationError
from mt_providers.types import TranslationStatus

# Handle provider not found
try:
    translator = get_provider("nonexistent_provider")
except ProviderNotFoundError as e:
    print(f"Provider not found: {e}")
    available = mt_providers.list_providers()
    print(f"Available providers: {available}")

# Handle configuration errors
try:
    config = TranslationConfig(api_key="")  # Invalid config
    translator = get_provider("microsoft")(config)
    result = translator.translate("test", "en", "es")
except ConfigurationError as e:
    print(f"Configuration error: {e}")

# Handle translation errors
config = TranslationConfig(api_key="invalid-key", region="westus2")
translator = get_provider("microsoft")(config)

result = translator.translate("Hello world", "en", "es")
if result["status"] == TranslationStatus.FAILED:
    print(f"Translation failed: {result['error']}")
else:
    print(f"Translation successful: {result['translated_text']}")
```

### Robust Batch Processing with Error Handling

```python
from mt_providers.types import TranslationStatus
import logging

def robust_batch_translate(translator, texts: List[str], 
                          source_lang: str, target_lang: str,
                          max_retries: int = 3):
    """Batch translate with retry logic for failed translations."""
    
    results = []
    failed_indices = []
    
    # First attempt
    batch_results = translator.bulk_translate(texts, source_lang, target_lang)
    
    for i, result in enumerate(batch_results):
        if result["status"] == TranslationStatus.SUCCESS:
            results.append(result)
        else:
            results.append(None)
            failed_indices.append(i)
            logging.warning(f"Failed to translate text {i}: {result['error']}")
    
    # Retry failed translations individually
    for retry in range(max_retries):
        if not failed_indices:
            break
            
        retry_indices = []
        for i in failed_indices:
            result = translator.translate(texts[i], source_lang, target_lang)
            if result["status"] == TranslationStatus.SUCCESS:
                results[i] = result
                logging.info(f"Successfully retried text {i} on attempt {retry + 1}")
            else:
                retry_indices.append(i)
                logging.warning(f"Retry {retry + 1} failed for text {i}: {result['error']}")
        
        failed_indices = retry_indices
    
    # Fill remaining failures with error responses
    for i in failed_indices:
        results[i] = {
            "translated_text": "",
            "status": TranslationStatus.FAILED,
            "error": "Maximum retries exceeded",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "char_count": len(texts[i])
        }
    
    return results

# Usage
texts = ["Hello", "World", "How are you?"]
results = robust_batch_translate(translator, texts, "en", "es")

for i, result in enumerate(results):
    if result["status"] == TranslationStatus.SUCCESS:
        print(f"✓ '{texts[i]}' -> '{result['translated_text']}'")
    else:
        print(f"✗ '{texts[i]}' failed: {result['error']}")
```

## Advanced Configuration

### Provider-Specific Settings

```python
# Microsoft Translator with all options
config = TranslationConfig(
    api_key="your-subscription-key",
    region="westus2",              # Required for Microsoft
    endpoint="https://api.cognitive.microsofttranslator.com/translate",
    timeout=60,                    # Request timeout in seconds
    rate_limit=100,                # Requests per second
    retry_attempts=3,              # Number of retries
    retry_backoff=1.0             # Backoff multiplier
)

translator = get_provider("microsoft")(config)
```

### Environment-Based Configuration

```python
import os
from mt_providers.types import TranslationConfig

def get_config_from_env():
    """Load configuration from environment variables."""
    return TranslationConfig(
        api_key=os.getenv("TRANSLATION_API_KEY"),
        region=os.getenv("TRANSLATION_REGION", "westus2"),
        endpoint=os.getenv("TRANSLATION_ENDPOINT"),
        timeout=int(os.getenv("TRANSLATION_TIMEOUT", "30")),
        rate_limit=int(os.getenv("TRANSLATION_RATE_LIMIT", "10")) if os.getenv("TRANSLATION_RATE_LIMIT") else None
    )

# Usage
config = get_config_from_env()
translator = get_provider("microsoft")(config)
```

### Multiple Provider Setup

```python
from typing import Dict

class MultiProviderTranslator:
    """Manage multiple translation providers."""
    
    def __init__(self):
        self.providers: Dict[str, BaseTranslationProvider] = {}
    
    def add_provider(self, name: str, provider_name: str, config: TranslationConfig):
        """Add a provider instance."""
        provider_class = get_provider(provider_name)
        self.providers[name] = provider_class(config)
    
    def translate(self, text: str, source_lang: str, target_lang: str, 
                 provider: str = None):
        """Translate using specified or first available provider."""
        if provider and provider in self.providers:
            return self.providers[provider].translate(text, source_lang, target_lang)
        elif self.providers:
            return next(iter(self.providers.values())).translate(text, source_lang, target_lang)
        else:
            raise ValueError("No providers configured")

# Setup multiple providers
multi_translator = MultiProviderTranslator()

# Add Microsoft provider
microsoft_config = TranslationConfig(api_key="ms-key", region="westus2")
multi_translator.add_provider("microsoft", "microsoft", microsoft_config)

# Add other providers as they become available
# google_config = TranslationConfig(api_key="google-key")
# multi_translator.add_provider("google", "google", google_config)

# Use specific provider
result = multi_translator.translate("Hello", "en", "es", provider="microsoft")
```

## Real-World Examples

### 1. Website Content Translation

```python
import requests
from bs4 import BeautifulSoup
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

def translate_webpage_content(url: str, target_lang: str):
    """Translate content of a webpage."""
    
    # Setup translator
    config = TranslationConfig(api_key="your-key", region="westus2")
    translator = get_provider("microsoft")(config)
    
    # Fetch webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract text content
    text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    texts = [elem.get_text().strip() for elem in text_elements if elem.get_text().strip()]
    
    # Translate in batches
    translations = translator.bulk_translate(texts, "auto", target_lang)
    
    # Replace content
    for i, (elem, translation) in enumerate(zip(text_elements, translations)):
        if translation["status"] == "success":
            elem.string = translation["translated_text"]
    
    return str(soup)

# Usage
translated_html = translate_webpage_content("https://example.com", "es")
with open("translated_page.html", "w", encoding="utf-8") as f:
    f.write(translated_html)
```

### 2. Chat Application Translation

```python
import asyncio
from datetime import datetime
from typing import List, Dict

class TranslatingChatBot:
    """Chat bot that translates messages in real-time."""
    
    def __init__(self, config: TranslationConfig):
        self.translator = get_provider("microsoft")(config)
        self.user_languages: Dict[str, str] = {}
    
    def set_user_language(self, user_id: str, language: str):
        """Set preferred language for a user."""
        self.user_languages[user_id] = language
    
    async def translate_message(self, message: str, from_user: str, to_user: str):
        """Translate message between users."""
        from_lang = self.user_languages.get(from_user, "en")
        to_lang = self.user_languages.get(to_user, "en")
        
        if from_lang == to_lang:
            return message  # No translation needed
        
        result = await self.translator.translate_async(message, from_lang, to_lang)
        
        if result["status"] == "success":
            return result["translated_text"]
        else:
            return f"[Translation failed: {result['error']}] {message}"
    
    async def broadcast_message(self, message: str, from_user: str, all_users: List[str]):
        """Broadcast message to all users in their preferred languages."""
        tasks = []
        for user in all_users:
            if user != from_user:
                task = self.translate_message(message, from_user, user)
                tasks.append((user, task))
        
        results = await asyncio.gather(*[task for _, task in tasks])
        
        translated_messages = {}
        for (user, _), translated in zip(tasks, results):
            translated_messages[user] = translated
        
        return translated_messages

# Usage
async def chat_example():
    config = TranslationConfig(api_key="your-key", region="westus2")
    chat_bot = TranslatingChatBot(config)
    
    # Setup users with different languages
    chat_bot.set_user_language("alice", "en")
    chat_bot.set_user_language("bob", "es")
    chat_bot.set_user_language("charlie", "fr")
    
    # Simulate message broadcast
    message = "Hello everyone, how are you doing?"
    translations = await chat_bot.broadcast_message(
        message, "alice", ["alice", "bob", "charlie"]
    )
    
    print(f"Original (Alice): {message}")
    for user, translated in translations.items():
        print(f"To {user}: {translated}")

asyncio.run(chat_example())
```

### 3. Document Translation Service

```python
import json
from pathlib import Path
from typing import Union

class DocumentTranslator:
    """Service for translating various document types."""
    
    def __init__(self, config: TranslationConfig):
        self.translator = get_provider("microsoft")(config)
    
    def translate_json(self, input_file: Path, output_file: Path, 
                      target_lang: str, fields_to_translate: List[str]):
        """Translate specific fields in a JSON file."""
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def translate_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if key in fields_to_translate or current_path in fields_to_translate:
                        if isinstance(value, str) and value.strip():
                            result = self.translator.translate(value, "auto", target_lang)
                            if result["status"] == "success":
                                obj[key] = result["translated_text"]
                    else:
                        translate_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    translate_recursive(item, f"{path}[{i}]")
        
        translate_recursive(data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def translate_text_file(self, input_file: Path, output_file: Path, 
                           source_lang: str, target_lang: str):
        """Translate a plain text file."""
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into paragraphs for better translation
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Translate paragraphs
        results = self.translator.bulk_translate(paragraphs, source_lang, target_lang)
        
        # Reconstruct content
        translated_paragraphs = []
        for result in results:
            if result["status"] == "success":
                translated_paragraphs.append(result["translated_text"])
            else:
                translated_paragraphs.append(f"[TRANSLATION ERROR: {result['error']}]")
        
        translated_content = '\n\n'.join(translated_paragraphs)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_content)

# Usage
config = TranslationConfig(api_key="your-key", region="westus2")
doc_translator = DocumentTranslator(config)

# Translate JSON configuration file
doc_translator.translate_json(
    input_file=Path("config.json"),
    output_file=Path("config_es.json"),
    target_lang="es",
    fields_to_translate=["title", "description", "message"]
)

# Translate text file
doc_translator.translate_text_file(
    input_file=Path("readme.txt"),
    output_file=Path("readme_es.txt"),
    source_lang="en",
    target_lang="es"
)
```

### 4. E-commerce Product Catalog Translation

```python
import pandas as pd
from mt_providers import get_provider
from mt_providers.types import TranslationConfig, TranslationStatus

class ProductCatalogTranslator:
    """Translate e-commerce product catalogs."""
    
    def __init__(self, config: TranslationConfig):
        self.translator = get_provider("microsoft")(config)
    
    def translate_catalog(self, input_csv: str, output_csv: str, 
                         target_lang: str, text_columns: List[str]):
        """Translate product catalog CSV file."""
        
        # Load data
        df = pd.read_csv(input_csv)
        
        # Collect all texts to translate
        all_texts = []
        text_mappings = []  # Track which text belongs to which row/column
        
        for col in text_columns:
            if col in df.columns:
                for idx, text in enumerate(df[col].fillna('')):
                    if text.strip():
                        all_texts.append(text)
                        text_mappings.append((idx, col))
        
        print(f"Translating {len(all_texts)} text segments...")
        
        # Batch translate
        results = self.translator.bulk_translate(all_texts, "auto", target_lang)
        
        # Apply translations back to dataframe
        for i, (row_idx, col_name) in enumerate(text_mappings):
            result = results[i]
            if result["status"] == TranslationStatus.SUCCESS:
                # Create new column for translation
                translated_col = f"{col_name}_{target_lang}"
                if translated_col not in df.columns:
                    df[translated_col] = ""
                df.at[row_idx, translated_col] = result["translated_text"]
            else:
                print(f"Failed to translate row {row_idx}, column {col_name}: {result['error']}")
        
        # Save translated catalog
        df.to_csv(output_csv, index=False)
        
        # Generate translation report
        successful = sum(1 for r in results if r["status"] == TranslationStatus.SUCCESS)
        total_chars = sum(r["char_count"] for r in results)
        
        print(f"Translation complete:")
        print(f"  Success rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
        print(f"  Total characters: {total_chars}")
        print(f"  Output saved to: {output_csv}")

# Usage
config = TranslationConfig(api_key="your-key", region="westus2")
catalog_translator = ProductCatalogTranslator(config)

catalog_translator.translate_catalog(
    input_csv="products.csv",
    output_csv="products_multilingual.csv",
    target_lang="es",
    text_columns=["name", "description", "category", "brand"]
)
```

## Performance Tips

### 1. Optimize Batch Sizes

```python
# Find optimal batch size for your use case
def benchmark_batch_sizes(translator, texts: List[str], 
                         source_lang: str, target_lang: str):
    """Benchmark different batch sizes."""
    import time
    
    batch_sizes = [1, 10, 50, 100, 200]
    
    for batch_size in batch_sizes:
        start_time = time.time()
        
        # Process in batches
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = translator.bulk_translate(batch, source_lang, target_lang)
            results.extend(batch_results)
        
        duration = time.time() - start_time
        chars_per_second = sum(len(text) for text in texts) / duration
        
        print(f"Batch size {batch_size}: {duration:.2f}s, {chars_per_second:.0f} chars/sec")
```

### 2. Connection Reuse

```python
# For high-volume applications, consider implementing connection pooling
# This is typically handled by the requests library automatically
config = TranslationConfig(
    api_key="your-key",
    region="westus2",
    timeout=60  # Longer timeout for batch operations
)
```

### 3. Caching

```python
from functools import lru_cache
import hashlib

class CachedTranslator:
    """Translator with built-in caching."""
    
    def __init__(self, config: TranslationConfig):
        self.translator = get_provider("microsoft")(config)
        self._cache = {}
    
    def _cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation."""
        content = f"{text}|{source_lang}|{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def translate(self, text: str, source_lang: str, target_lang: str):
        """Translate with caching."""
        cache_key = self._cache_key(text, source_lang, target_lang)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = self.translator.translate(text, source_lang, target_lang)
        
        # Only cache successful translations
        if result["status"] == TranslationStatus.SUCCESS:
            self._cache[cache_key] = result
        
        return result

# Usage
cached_translator = CachedTranslator(config)
```

These examples demonstrate the versatility and power of the MT Providers framework. Start with the basic examples and gradually incorporate more advanced features as your needs grow.
