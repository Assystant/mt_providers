"""Integration tests for MT Providers framework."""

import pytest
from mt_providers import get_provider, list_providers, discover_providers
from mt_providers.types import TranslationConfig, TranslationStatus
from mt_providers.exceptions import ProviderNotFoundError, ConfigurationError
from mt_providers.registry import check_provider_health


class TestProviderDiscovery:
    """Test provider discovery and registration."""

    def test_provider_discovery(self):
        """Test that providers are discovered correctly."""
        providers = list_providers()
        assert "microsoft" in providers
        assert len(providers) >= 1

    def test_discover_providers_idempotent(self):
        """Test discovering providers multiple times doesn't cause issues."""
        initial_providers = list_providers()

        # Discover again
        discovered = discover_providers()
        final_providers = list_providers()

        # Should be the same
        assert initial_providers == final_providers
        assert "microsoft" in discovered

    def test_get_provider_success(self):
        """Test getting a registered provider."""
        provider_class = get_provider("microsoft")
        assert provider_class is not None
        assert hasattr(provider_class, "name")
        assert provider_class.name == "microsoft"

    def test_get_provider_not_found(self):
        """Test error when provider not found."""
        with pytest.raises(ProviderNotFoundError):
            get_provider("nonexistent_provider")


class TestProviderInstantiation:
    """Test provider instantiation and configuration."""

    def test_microsoft_provider_instantiation(self):
        """Test Microsoft provider can be instantiated."""
        config = TranslationConfig(api_key="test-key", region="westus2")
        provider_class = get_provider("microsoft")
        provider = provider_class(config)

        assert provider.name == "microsoft"
        assert provider.config.api_key == "test-key"
        assert provider.config.region == "westus2"

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test missing API key
        with pytest.raises(ConfigurationError):
            config = TranslationConfig(api_key="", region="westus2")
            provider_class = get_provider("microsoft")
            provider_class(config)

    def test_provider_attributes(self):
        """Test provider has required attributes."""
        config = TranslationConfig(api_key="test-key", region="westus2")
        provider_class = get_provider("microsoft")
        provider = provider_class(config)

        assert hasattr(provider, "name")
        assert hasattr(provider, "requires_region")
        assert hasattr(provider, "supports_async")
        assert hasattr(provider, "max_chunk_size")
        assert hasattr(provider, "translate")
        assert hasattr(provider, "bulk_translate")


class TestTranslationInterface:
    """Test translation interface without making real API calls."""

    @pytest.fixture
    def mock_provider(self, requests_mock):
        """Create a provider with mocked API responses."""
        requests_mock.post(
            "https://api.cognitive.microsofttranslator.com/translate",
            json=[{
                "translations": [{"text": "¡Hola mundo!"}],
                "detectedLanguage": {"language": "en", "score": 1.0}
            }]
        )

        config = TranslationConfig(api_key="test-key", region="westus2")
        provider_class = get_provider("microsoft")
        return provider_class(config)

    def test_single_translation(self, mock_provider):
        """Test single translation."""
        result = mock_provider.translate("Hello world", "en", "es")

        assert result["status"] == TranslationStatus.SUCCESS
        assert result["translated_text"] == "¡Hola mundo!"
        assert result["provider"] == "microsoft"
        assert result["source_lang"] == "en"
        assert result["target_lang"] == "es"
        assert result["char_count"] == 11
        assert "request_id" in result
        assert "timestamp" in result

    def test_bulk_translation(self, mock_provider, requests_mock):
        """Test bulk translation."""
        # Mock bulk response
        requests_mock.post(
            "https://api.cognitive.microsofttranslator.com/translate",
            json=[
                {"translations": [{"text": "¡Hola!"}]},
                {"translations": [{"text": "¡Mundo!"}]}
            ]
        )

        texts = ["Hello", "World"]
        results = mock_provider.bulk_translate(texts, "en", "es")

        assert len(results) == 2
        assert all(r["status"] == TranslationStatus.SUCCESS for r in results)
        assert results[0]["translated_text"] == "¡Hola!"
        assert results[1]["translated_text"] == "¡Mundo!"

    @pytest.mark.asyncio
    async def test_async_translation(self, mock_provider):
        """Test async translation."""
        result = await mock_provider.translate_async("Hello world", "en", "es")

        assert result["status"] == TranslationStatus.SUCCESS
        assert result["translated_text"] == "¡Hola mundo!"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_api_error_handling(self, requests_mock):
        """Test handling of API errors."""
        requests_mock.post(
            "https://api.cognitive.microsofttranslator.com/translate",
            status_code=500
        )

        config = TranslationConfig(api_key="test-key", region="westus2")
        provider_class = get_provider("microsoft")
        provider = provider_class(config)

        result = provider.translate("Hello world", "en", "es")

        assert result["status"] == TranslationStatus.FAILED
        assert result["error"] is not None
        assert result["translated_text"] == ""

    def test_network_timeout(self, requests_mock):
        """Test network timeout handling."""
        import requests
        requests_mock.post(
            "https://api.cognitive.microsofttranslator.com/translate",
            exc=requests.Timeout("Request timeout")
        )

        config = TranslationConfig(
            api_key="test-key", region="westus2", timeout=1)
        provider_class = get_provider("microsoft")
        provider = provider_class(config)

        result = provider.translate("Hello world", "en", "es")

        assert result["status"] == TranslationStatus.FAILED
        assert "timeout" in result["error"].lower()


class TestHealthChecking:
    """Test provider health checking."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, requests_mock):
        """Test successful health check."""
        requests_mock.post(
            "https://api.cognitive.microsofttranslator.com/translate",
            json=[{
                "translations": [{"text": "test"}],
                "detectedLanguage": {"language": "en", "score": 1.0}
            }]
        )

        config = TranslationConfig(api_key="test-key", region="westus2")
        is_healthy = await check_provider_health("microsoft", config)

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, requests_mock):
        """Test failed health check."""
        requests_mock.post(
            "https://api.cognitive.microsofttranslator.com/translate",
            status_code=401
        )

        config = TranslationConfig(api_key="invalid-key", region="westus2")

        # Health check should return False on failure
        is_healthy = await check_provider_health("microsoft", config)
        assert is_healthy is False


class TestConfigurationOptions:
    """Test various configuration options."""

    def test_rate_limiting_config(self):
        """Test rate limiting configuration."""
        config = TranslationConfig(
            api_key="test-key",
            region="westus2",
            rate_limit=10
        )

        provider_class = get_provider("microsoft")
        provider = provider_class(config)

        assert provider.config.rate_limit == 10

    def test_timeout_config(self):
        """Test timeout configuration."""
        config = TranslationConfig(
            api_key="test-key",
            region="westus2",
            timeout=60
        )

        provider_class = get_provider("microsoft")
        provider = provider_class(config)

        assert provider.config.timeout == 60

    def test_retry_config(self):
        """Test retry configuration."""
        config = TranslationConfig(
            api_key="test-key",
            region="westus2",
            retry_attempts=5,
            retry_backoff=2.0
        )

        provider_class = get_provider("microsoft")
        provider = provider_class(config)

        assert provider.config.retry_attempts == 5
        assert provider.config.retry_backoff == 2.0


class TestFrameworkIntegration:
    """Test framework integration scenarios."""

    def test_multiple_provider_instances(self):
        """Test creating multiple provider instances."""
        config1 = TranslationConfig(api_key="key1", region="westus2")
        config2 = TranslationConfig(api_key="key2", region="eastus")

        provider_class = get_provider("microsoft")
        provider1 = provider_class(config1)
        provider2 = provider_class(config2)

        assert provider1.config.api_key == "key1"
        assert provider2.config.api_key == "key2"
        assert provider1.config.region == "westus2"
        assert provider2.config.region == "eastus"

    def test_provider_metadata(self):
        """Test provider metadata and attributes."""
        provider_class = get_provider("microsoft")

        assert provider_class.name == "microsoft"
        assert provider_class.requires_region is True
        assert hasattr(provider_class, "supports_async")
        assert hasattr(provider_class, "max_chunk_size")


class TestPerformance:
    """Basic performance tests."""

    def test_provider_discovery_performance(self):
        """Test that provider discovery is reasonably fast."""
        import time

        start_time = time.time()
        providers = list_providers()
        discovery_time = time.time() - start_time

        assert len(providers) >= 1
        assert discovery_time < 1.0  # Should be very fast

    def test_provider_instantiation_performance(self):
        """Test that provider instantiation is fast."""
        import time

        config = TranslationConfig(api_key="test-key", region="westus2")
        provider_class = get_provider("microsoft")

        start_time = time.time()
        provider = provider_class(config)
        instantiation_time = time.time() - start_time

        assert provider is not None
        assert instantiation_time < 0.1  # Should be very fast


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running integration smoke tests...")

    # Test provider discovery
    providers = list_providers()
    print(f"✓ Found providers: {providers}")

    # Test provider instantiation
    config = TranslationConfig(api_key="test-key", region="westus2")
    provider_class = get_provider("microsoft")
    provider = provider_class(config)
    print(f"✓ Instantiated provider: {provider.name}")

    print("✓ All smoke tests passed!")
