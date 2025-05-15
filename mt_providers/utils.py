import re
from typing import Optional

from .exceptions import ValidationError


def validate_language_code(code: str) -> bool:
    """Validate language code format."""
    pattern = r"^[a-z]{2,3}(-[A-Z][a-z]{3})?(-[A-Z]{2})?$"
    return bool(re.match(pattern, code))


def normalize_language_code(code: str) -> str:
    """Normalize language code to standard format."""
    if not validate_language_code(code):
        raise ValidationError(f"Invalid language code: {code}")
    return code.lower()
