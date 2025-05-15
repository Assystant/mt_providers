from concurrent.futures import ThreadPoolExecutor

import pytest

from mt_providers.base import BaseTranslationProvider
from mt_providers.registry import (
    check_provider_health,
    clear_registry,
    list_providers,
    register_provider,
)
from mt_providers.types import TranslationConfig, TranslationResponse


def test_thread_safety():
    """Test thread-safe registration of providers"""
    clear_registry()

    def register_mock(i):
        class MockProvider(BaseTranslationProvider):
            name = f"mock_{i}"

        register_provider(f"mock_{i}", MockProvider)

    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(register_mock, range(100)))

    assert len(list_providers()) == 100


@pytest.mark.asyncio
async def test_provider_health_check():
    """Test health check with retries"""
    clear_registry()

    test_provider_name = "test_health"
    test_api_key = "test_api_key"

    class TestProvider(BaseTranslationProvider):
        name = test_provider_name

        def translate(
            self, text: str, source_lang: str, target_lang: str
        ) -> TranslationResponse:
            return self._create_response(
                translated_text="test",
                source_lang=source_lang,
                target_lang=target_lang,
                char_count=4,
            )

    register_provider(test_provider_name, TestProvider)

    # Verify registration
    assert TestProvider.name in list_providers()

    config = TranslationConfig(api_key=test_api_key)

    is_healthy = await check_provider_health(test_provider_name, config)
    assert is_healthy is True
