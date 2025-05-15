import pytest

from mt_providers.types import TranslationConfig


@pytest.fixture
def mock_config():
    return TranslationConfig(api_key="test-key", region="test-region", timeout=30)


@pytest.fixture
def sample_texts():
    return {
        "short": "Hello world",
        "long": "This is a longer text that needs translation",
        "special": "Text with special chars: @#$%",
    }
