import pytest

from mt_providers.base import BaseTranslationProvider
from mt_providers.exceptions import ConfigurationError
from mt_providers.types import TranslationConfig, TranslationStatus
from mt_providers.utils import validate_language_code


def test_language_code_validation():
    assert validate_language_code("en-US")
    assert validate_language_code("fr")
    assert validate_language_code("zh-Hans")
    assert not validate_language_code("invalid")


@pytest.mark.asyncio
async def test_async_translation():
    """Test async translation fallback."""

    class TestProvider(BaseTranslationProvider):
        name = "test"

        def translate(self, text, source_lang, target_lang):
            return self._create_response("test", source_lang, target_lang, 4)

    provider = TestProvider(TranslationConfig(api_key="test"))
    result = await provider.translate_async("test", "en", "fr")
    assert result["status"] == TranslationStatus.SUCCESS
