import pytest

from mt_providers.exceptions import ValidationError
from mt_providers.utils import normalize_language_code, validate_language_code


def test_language_code_validation():
    """Test language code validation"""
    assert validate_language_code("en-US")
    assert validate_language_code("fr")
    assert validate_language_code("zh-Hans")
    assert not validate_language_code("invalid")


def test_language_code_normalization():
    """Test language code normalization"""
    assert normalize_language_code("en-US") == "en-us"
    with pytest.raises(ValidationError):
        normalize_language_code("invalid")
