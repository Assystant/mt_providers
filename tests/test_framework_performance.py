"""Framework-only performance benchmarks for MT Providers core."""

import asyncio
import time
from typing import Dict, Any, List

from mt_providers import register_provider, get_provider, list_providers
from mt_providers.base import BaseTranslationProvider
from mt_providers.types import TranslationConfig, TranslationStatus


class MockProvider(BaseTranslationProvider):
    """Mock provider for performance testing."""

    name = "mock_provider"
    supports_async = True
    supported_languages = {"en", "fr", "es", "de"}

    def __init__(self, config: TranslationConfig):
        super().__init__(config)

    def translate(
        self, text: str, source_lang: str, target_lang: str, **kwargs
    ) -> Dict[str, Any]:
        """Mock synchronous translation."""
        return {
            "text": f"Translated: {text}",
            "source_language": source_lang,
            "target_language": target_lang,
            "status": TranslationStatus.SUCCESS,
            "provider": self.name,
            "timestamp": time.time(),
        }

    async def translate_async(
        self, text: str, source_lang: str, target_lang: str, **kwargs
    ) -> Dict[str, Any]:
        """Mock asynchronous translation."""
        await asyncio.sleep(0.001)  # Simulate small processing delay
        return self.translate(text, source_lang, target_lang, **kwargs)

    def translate_bulk(
        self, texts: List[str], source_lang: str, target_lang: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """Mock bulk translation."""
        return [
            self.translate(text, source_lang, target_lang, **kwargs) for text in texts
        ]

    async def translate_bulk_async(
        self, texts: List[str], source_lang: str, target_lang: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """Mock async bulk translation."""
        return [
            await self.translate_async(text, source_lang, target_lang, **kwargs)
            for text in texts
        ]


class FrameworkPerformanceBenchmark:
    """Performance benchmark suite focused on framework operations."""

    def __init__(self):
        self.results = {}
        self.setup_test_provider()

    def setup_test_provider(self):
        """Register mock provider for testing."""
        register_provider("mock_provider", MockProvider)

    def time_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Time an operation and store results."""
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()

        duration = end_time - start_time
        self.results[operation_name] = {
            "duration": duration,
            "duration_ms": duration * 1000,
            "result": result,
        }
        print(f"{operation_name}: {duration:.4f}s ({duration * 1000:.2f}ms)")
        return result

    async def time_async_operation(
        self, operation_name: str, operation_func, *args, **kwargs
    ):
        """Time an async operation and store results."""
        start_time = time.time()
        result = await operation_func(*args, **kwargs)
        end_time = time.time()

        duration = end_time - start_time
        self.results[operation_name] = {
            "duration": duration,
            "duration_ms": duration * 1000,
            "result": result,
        }
        print(f"{operation_name}: {duration:.4f}s ({duration * 1000:.2f}ms)")
        return result

    def benchmark_registry_operations(self):
        """Benchmark provider registry operations."""
        print("\n=== Registry Operations Benchmark ===")

        # Test provider listing
        self.time_operation("list_providers", list_providers)

        # Test provider retrieval
        self.time_operation("get_provider", get_provider, "mock_provider")

        # Test multiple provider retrievals (caching effect)
        def get_multiple_providers():
            results = []
            for _ in range(100):
                results.append(get_provider("mock_provider"))
            return results

        self.time_operation("get_provider_100x", get_multiple_providers)

        # Test cache performance
        def test_cache_performance():
            # Clear cache
            get_provider.cache_clear()
            # Time first access (cache miss)
            start = time.time()
            get_provider("mock_provider")
            first_access = time.time() - start

            # Time second access (cache hit)
            start = time.time()
            get_provider("mock_provider")
            second_access = time.time() - start

            return {
                "cache_miss_time": first_access,
                "cache_hit_time": second_access,
                "speedup_factor": first_access / second_access
                if second_access > 0
                else 0,
            }

        self.time_operation("cache_performance", test_cache_performance)

    def benchmark_provider_instantiation(self):
        """Benchmark provider instantiation performance."""
        print("\n=== Provider Instantiation Benchmark ===")

        config = TranslationConfig(api_key="test-key", region="test")
        provider_class = get_provider("mock_provider")

        # Single instantiation
        def single_instantiation():
            return provider_class(config)

        self.time_operation("single_instantiation", single_instantiation)

        # Multiple instantiations
        def multiple_instantiations():
            instances = []
            for _ in range(50):
                instances.append(provider_class(config))
            return instances

        self.time_operation("multiple_instantiations_50x", multiple_instantiations)

    def benchmark_translation_operations(self):
        """Benchmark translation operations."""
        print("\n=== Translation Operations Benchmark ===")

        config = TranslationConfig(api_key="test-key", region="test")
        provider = get_provider("mock_provider")(config)

        # Single translation
        def single_translation():
            return provider.translate("Hello world", "en", "fr")

        self.time_operation("single_translation", single_translation)

        # Multiple translations
        def multiple_translations():
            results = []
            for i in range(20):
                results.append(provider.translate(f"Test message {i}", "en", "fr"))
            return results

        self.time_operation("multiple_translations_20x", multiple_translations)

        # Bulk translation
        texts = [f"Test message {i}" for i in range(20)]

        def bulk_translation():
            return provider.translate_bulk(texts, "en", "fr")

        self.time_operation("bulk_translation_20_texts", bulk_translation)

    async def benchmark_async_operations(self):
        """Benchmark async translation operations."""
        print("\n=== Async Translation Operations Benchmark ===")

        config = TranslationConfig(api_key="test-key", region="test")
        provider = get_provider("mock_provider")(config)

        # Single async translation
        async def single_async_translation():
            return await provider.translate_async("Hello world", "en", "fr")

        await self.time_async_operation(
            "single_async_translation", single_async_translation
        )

        # Multiple concurrent translations
        async def concurrent_translations():
            tasks = []
            for i in range(10):
                task = provider.translate_async(f"Test message {i}", "en", "fr")
                tasks.append(task)
            return await asyncio.gather(*tasks)

        await self.time_async_operation(
            "concurrent_translations_10x", concurrent_translations
        )

        # Async bulk translation
        texts = [f"Test message {i}" for i in range(10)]

        async def async_bulk_translation():
            return await provider.translate_bulk_async(texts, "en", "fr")

        await self.time_async_operation(
            "async_bulk_translation_10_texts", async_bulk_translation
        )

    def benchmark_error_handling_performance(self):
        """Benchmark error handling performance."""
        print("\n=== Error Handling Benchmark ===")

        # Test exception creation and handling
        def test_provider_errors():
            errors_caught = 0
            for i in range(100):
                try:
                    get_provider("nonexistent_provider")
                except Exception:
                    errors_caught += 1
            return errors_caught

        self.time_operation("error_handling_100x", test_provider_errors)

    def generate_performance_report(self):
        """Generate a comprehensive performance report."""
        print("\n" + "=" * 60)
        print("FRAMEWORK PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)

        # Registry operations
        print("\nRegistry Operations:")
        print(
            f"  - List providers: {self.results.get('list_providers', {}).get('duration_ms', 0):.2f}ms"
        )
        print(
            f"  - Get provider: {self.results.get('get_provider', {}).get('duration_ms', 0):.2f}ms"
        )
        print(
            f"  - Get provider 100x: {self.results.get('get_provider_100x', {}).get('duration_ms', 0):.2f}ms"
        )

        # Cache performance
        cache_result = self.results.get("cache_performance", {}).get("result", {})
        if cache_result:
            print(
                f"  - Cache miss: {cache_result.get('cache_miss_time', 0) * 1000:.2f}ms"
            )
            print(
                f"  - Cache hit: {cache_result.get('cache_hit_time', 0) * 1000:.2f}ms"
            )
            print(f"  - Cache speedup: {cache_result.get('speedup_factor', 0):.1f}x")

        # Instantiation
        print("\nProvider Instantiation:")
        print(
            f"  - Single instantiation: {self.results.get('single_instantiation', {}).get('duration_ms', 0):.2f}ms"
        )
        print(
            f"  - Multiple instantiations (50x): {self.results.get('multiple_instantiations_50x', {}).get('duration_ms', 0):.2f}ms"
        )

        # Translations
        print("\nTranslation Operations:")
        print(
            f"  - Single translation: {self.results.get('single_translation', {}).get('duration_ms', 0):.2f}ms"
        )
        print(
            f"  - Multiple translations (20x): {self.results.get('multiple_translations_20x', {}).get('duration_ms', 0):.2f}ms"
        )
        print(
            f"  - Bulk translation (20 texts): {self.results.get('bulk_translation_20_texts', {}).get('duration_ms', 0):.2f}ms"
        )

        # Async operations
        print("\nAsync Operations:")
        print(
            f"  - Single async translation: {self.results.get('single_async_translation', {}).get('duration_ms', 0):.2f}ms"
        )
        print(
            f"  - Concurrent translations (10x): {self.results.get('concurrent_translations_10x', {}).get('duration_ms', 0):.2f}ms"
        )
        print(
            f"  - Async bulk translation (10 texts): {self.results.get('async_bulk_translation_10_texts', {}).get('duration_ms', 0):.2f}ms"
        )

        # Error handling
        print("\nError Handling:")
        print(
            f"  - Error handling (100x): {self.results.get('error_handling_100x', {}).get('duration_ms', 0):.2f}ms"
        )

        print("\n" + "=" * 60)

        # Performance analysis
        self.analyze_performance()

    def analyze_performance(self):
        """Analyze performance results and provide recommendations."""
        print("PERFORMANCE ANALYSIS & RECOMMENDATIONS")
        print("=" * 60)

        # Performance guidelines for the framework
        issues = []
        recommendations = []

        # Check registry performance
        get_provider_time = self.results.get("get_provider", {}).get("duration_ms", 0)
        if get_provider_time > 5:
            issues.append(f"Provider retrieval is slow ({get_provider_time:.2f}ms)")
            recommendations.append("Consider optimizing provider registry lookup")

        # Check cache effectiveness
        cache_result = self.results.get("cache_performance", {}).get("result", {})
        if cache_result:
            speedup = cache_result.get("speedup_factor", 0)
            if speedup < 5:
                issues.append(f"Cache speedup is low ({speedup:.1f}x)")
                recommendations.append("Review caching implementation")

        # Check instantiation performance
        instantiation_time = self.results.get("single_instantiation", {}).get(
            "duration_ms", 0
        )
        if instantiation_time > 10:
            issues.append(
                f"Provider instantiation is slow ({instantiation_time:.2f}ms)"
            )
            recommendations.append("Consider lazy initialization patterns")

        # Check async overhead
        async_time = self.results.get("single_async_translation", {}).get(
            "duration_ms", 0
        )
        sync_time = self.results.get("single_translation", {}).get("duration_ms", 0)
        if async_time > 0 and sync_time > 0:
            overhead = async_time - sync_time
            if overhead > 5:  # 5ms overhead threshold
                issues.append(f"High async overhead ({overhead:.2f}ms)")
                recommendations.append("Optimize async implementation")

        if not issues:
            print("✅ All framework performance metrics are within acceptable ranges")
            print("\n📊 Key Performance Indicators:")
            print(f"  - Provider lookup: {get_provider_time:.2f}ms")
            print(f"  - Cache speedup: {cache_result.get('speedup_factor', 0):.1f}x")
            print(f"  - Instantiation: {instantiation_time:.2f}ms")
            print(f"  - Translation: {sync_time:.2f}ms")
        else:
            print("⚠️  Performance Issues Detected:")
            for issue in issues:
                print(f"  - {issue}")

            print("\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  - {rec}")

    async def run_all_benchmarks(self):
        """Run the complete framework benchmark suite."""
        print("Starting MT Providers Framework Performance Benchmark")
        print("=" * 60)

        # Core benchmarks
        self.benchmark_registry_operations()
        self.benchmark_provider_instantiation()
        self.benchmark_translation_operations()

        # Async benchmarks
        await self.benchmark_async_operations()

        # Error handling
        self.benchmark_error_handling_performance()

        # Generate final report
        self.generate_performance_report()


async def main():
    """Run the framework performance benchmark suite."""
    benchmark_suite = FrameworkPerformanceBenchmark()
    await benchmark_suite.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())
