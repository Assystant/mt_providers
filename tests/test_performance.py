"""Performance benchmarks for MT Providers framework."""

import time
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from mt_providers import get_provider, list_providers, discover_providers
from mt_providers.types import TranslationConfig
from mt_providers.base import BaseTranslationProvider


class BenchmarkResults:
    """Container for benchmark results."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.times: List[float] = []
        self.operations = 0
        self.errors = 0
    
    def add_time(self, duration: float):
        """Add a timing measurement."""
        self.times.append(duration)
        self.operations += 1
    
    def add_error(self):
        """Record an error."""
        self.errors += 1
    
    @property
    def avg_time(self) -> float:
        """Average time per operation."""
        return sum(self.times) / len(self.times) if self.times else 0
    
    @property
    def min_time(self) -> float:
        """Minimum time."""
        return min(self.times) if self.times else 0
    
    @property
    def max_time(self) -> float:
        """Maximum time."""
        return max(self.times) if self.times else 0
    
    @property
    def operations_per_second(self) -> float:
        """Operations per second."""
        return 1.0 / self.avg_time if self.avg_time > 0 else 0
    
    def __str__(self) -> str:
        return (
            f"{self.test_name}:\n"
            f"  Operations: {self.operations}\n"
            f"  Errors: {self.errors}\n"
            f"  Avg time: {self.avg_time:.4f}s\n"
            f"  Min time: {self.min_time:.4f}s\n"
            f"  Max time: {self.max_time:.4f}s\n"
            f"  Ops/sec: {self.operations_per_second:.2f}\n"
        )


class MockProvider(BaseTranslationProvider):
    """Mock provider for performance testing."""
    
    name = "mock"
    supports_async = True
    
    def __init__(self, config: TranslationConfig):
        super().__init__(config)
        self.call_count = 0
        self.delay = 0.001  # 1ms simulated processing time
    
    def translate(self, text: str, source_lang: str, target_lang: str):
        """Mock translation with simulated delay."""
        time.sleep(self.delay)
        self.call_count += 1
        
        return self._create_response(
            translated_text=f"mock_translation_{self.call_count}",
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(text)
        )
    
    async def translate_async(self, text: str, source_lang: str, target_lang: str):
        """Mock async translation."""
        await asyncio.sleep(self.delay)
        self.call_count += 1
        
        return self._create_response(
            translated_text=f"mock_async_translation_{self.call_count}",
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(text)
        )


class PerformanceBenchmarks:
    """Performance benchmark suite."""
    
    def __init__(self):
        self.results: List[BenchmarkResults] = []
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        print("Running MT Providers Performance Benchmarks")
        print("=" * 50)
        
        # Registry benchmarks
        self.benchmark_provider_discovery()
        self.benchmark_provider_lookup()
        self.benchmark_provider_instantiation()
        
        # Translation benchmarks
        self.benchmark_single_translations()
        self.benchmark_bulk_translations()
        self.benchmark_async_translations()
        self.benchmark_concurrent_translations()
        
        # Memory and resource benchmarks
        self.benchmark_memory_usage()
        
        # Print results
        self.print_results()
    
    def benchmark_provider_discovery(self):
        """Benchmark provider discovery performance."""
        results = BenchmarkResults("Provider Discovery")
        
        for _ in range(100):
            start_time = time.time()
            discover_providers()
            duration = time.time() - start_time
            results.add_time(duration)
        
        self.results.append(results)
    
    def benchmark_provider_lookup(self):
        """Benchmark provider lookup performance."""
        results = BenchmarkResults("Provider Lookup")
        
        for _ in range(1000):
            start_time = time.time()
            try:
                get_provider("microsoft")
                duration = time.time() - start_time
                results.add_time(duration)
            except Exception:
                results.add_error()
        
        self.results.append(results)
    
    def benchmark_provider_instantiation(self):
        """Benchmark provider instantiation performance."""
        results = BenchmarkResults("Provider Instantiation")
        config = TranslationConfig(api_key="test-key", region="westus2")
        provider_class = get_provider("microsoft")
        
        for _ in range(100):
            start_time = time.time()
            try:
                provider = provider_class(config)
                duration = time.time() - start_time
                results.add_time(duration)
            except Exception:
                results.add_error()
        
        self.results.append(results)
    
    def benchmark_single_translations(self):
        """Benchmark single translation performance."""
        from mt_providers.registry import register_provider
        
        # Register mock provider for testing
        register_provider("mock", MockProvider)
        
        results = BenchmarkResults("Single Translations")
        config = TranslationConfig(api_key="test-key")
        provider = MockProvider(config)
        
        test_texts = [
            "Hello world",
            "This is a test",
            "Short",
            "This is a much longer text that should take about the same time to process",
        ]
        
        for i in range(100):
            text = test_texts[i % len(test_texts)]
            start_time = time.time()
            try:
                result = provider.translate(text, "en", "es")
                duration = time.time() - start_time
                results.add_time(duration)
            except Exception:
                results.add_error()
        
        self.results.append(results)
    
    def benchmark_bulk_translations(self):
        """Benchmark bulk translation performance."""
        results = BenchmarkResults("Bulk Translations")
        config = TranslationConfig(api_key="test-key")
        provider = MockProvider(config)
        
        # Test different batch sizes
        batch_sizes = [1, 10, 50, 100]
        texts = [f"Test text {i}" for i in range(100)]
        
        for batch_size in batch_sizes:
            batch_texts = texts[:batch_size]
            start_time = time.time()
            try:
                results_batch = provider.bulk_translate(batch_texts, "en", "es")
                duration = time.time() - start_time
                results.add_time(duration)
                
                # Verify all translations succeeded
                if len(results_batch) != batch_size:
                    results.add_error()
            except Exception:
                results.add_error()
        
        self.results.append(results)
    
    def benchmark_async_translations(self):
        """Benchmark async translation performance."""
        async def run_async_benchmark():
            results = BenchmarkResults("Async Translations")
            config = TranslationConfig(api_key="test-key")
            provider = MockProvider(config)
            
            for i in range(100):
                start_time = time.time()
                try:
                    result = await provider.translate_async(f"Test {i}", "en", "es")
                    duration = time.time() - start_time
                    results.add_time(duration)
                except Exception:
                    results.add_error()
            
            return results
        
        results = asyncio.run(run_async_benchmark())
        self.results.append(results)
    
    def benchmark_concurrent_translations(self):
        """Benchmark concurrent translation performance."""
        async def run_concurrent_benchmark():
            results = BenchmarkResults("Concurrent Translations")
            config = TranslationConfig(api_key="test-key")
            provider = MockProvider(config)
            
            # Test different concurrency levels
            concurrency_levels = [1, 5, 10, 20]
            
            for concurrency in concurrency_levels:
                tasks = []
                start_time = time.time()

                for i in range(concurrency):
                    task = provider.translate_async(f"Concurrent test {i}", "en", "es")
                    tasks.append(task)

                try:
                    await asyncio.gather(*tasks)
                    duration = time.time() - start_time
                    results.add_time(duration)
                except Exception:
                    results.add_error()

            return results

        results = asyncio.run(run_concurrent_benchmark())
        self.results.append(results)

    def benchmark_memory_usage(self):
        """Benchmark memory usage patterns."""
        import gc

        results = BenchmarkResults("Memory Usage")
        config = TranslationConfig(api_key="test-key")

        # Test creating many provider instances
        providers = []
        start_time = time.time()

        try:
            for i in range(100):
                provider = MockProvider(config)
                providers.append(provider)

            # Force garbage collection
            gc.collect()

            duration = time.time() - start_time
            results.add_time(duration)

            # Clean up
            del providers
            gc.collect()

        except Exception:
            results.add_error()

        self.results.append(results)

    def print_results(self):
        """Print benchmark results."""
        print("\nBenchmark Results")
        print("=" * 50)

        for result in self.results:
            print(result)

        # Summary
        total_operations = sum(r.operations for r in self.results)
        total_errors = sum(r.errors for r in self.results)

        print(f"Summary:")
        print(f"  Total operations: {total_operations}")
        print(f"  Total errors: {total_errors}")
        print(f"  Success rate: {(total_operations - total_errors) / total_operations * 100:.1f}%")


def benchmark_real_provider():
    """Benchmark real provider performance (without making API calls)."""
    print("\nReal Provider Benchmark (No API Calls)")
    print("=" * 40)

    # Test provider lookup speed
    start_time = time.time()
    for _ in range(1000):
        provider_class = get_provider("microsoft")
    lookup_time = time.time() - start_time
    print(f"Provider lookup (1000x): {lookup_time:.4f}s ({1000/lookup_time:.0f} ops/sec)")

    # Test provider instantiation speed
    config = TranslationConfig(api_key="test-key", region="westus2")
    start_time = time.time()
    for _ in range(100):
        provider = provider_class(config)
    instantiation_time = time.time() - start_time
    print(f"Provider instantiation (100x): {instantiation_time:.4f}s ({100/instantiation_time:.0f} ops/sec)")

    # Test framework overhead
    provider = provider_class(config)

    # Test response creation (framework overhead)
    start_time = time.time()
    for i in range(1000):
        response = provider._create_response(
            translated_text=f"test_{i}",
            source_lang="en",
            target_lang="es",
            char_count=10
        )
    response_creation_time = time.time() - start_time
    print(f"Response creation (1000x): {response_creation_time:.4f}s ({1000/response_creation_time:.0f} ops/sec)")


if __name__ == "__main__":
    # Run benchmarks
    benchmark_suite = PerformanceBenchmarks()
    benchmark_suite.run_all_benchmarks()
    # Run real provider benchmarks
    benchmark_real_provider()
    print("\nBenchmarks completed!")
