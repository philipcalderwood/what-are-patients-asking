#!/usr/bin/env python3
"""
Database Performance Benchmark for MRPC - Test Module

This module provides comprehensive benchmarking of database operations
to measure the impact of initialization optimizations while maintaining
the per-request pattern.

Usage:
    # Run as pytest
    pytest tests/benchmarking/test_database_performance.py -v

    # Run standalone
    python tests/benchmarking/test_database_performance.py
"""

import time
import statistics
import sys
import pytest
from pathlib import Path
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utilities.mrpc_database import MRPCDatabase


class DatabaseBenchmark:
    """Benchmark database operations with statistical analysis"""

    def __init__(self, iterations=100):
        self.iterations = iterations
        self.results = {}

    @contextmanager
    def timer(self, operation_name):
        """Context manager to time operations"""
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            duration = (end - start) * 1000  # Convert to milliseconds

            if operation_name not in self.results:
                self.results[operation_name] = []
            self.results[operation_name].append(duration)

    def benchmark_database_creation(self):
        """Benchmark MRPCDatabase instantiation (current pattern)"""
        print(f"🔄 Benchmarking database creation ({self.iterations} iterations)...")

        for i in range(self.iterations):
            with self.timer("database_creation"):
                db = MRPCDatabase()
                # Simulate typical usage - accessing a property
                _ = db.db_path

    def benchmark_auth_flow(self):
        """Benchmark authentication flow (database + user lookup)"""
        print(f"🔐 Benchmarking authentication flow ({self.iterations} iterations)...")

        for i in range(self.iterations):
            with self.timer("auth_flow"):
                db = MRPCDatabase()
                # Simulate auth lookup (even if user doesn't exist)
                users = db.get_all_users()
                # Simulate typical auth check
                _ = len(users) > 0

    def benchmark_multiple_operations(self):
        """Benchmark multiple database operations (realistic usage)"""
        print(f"Benchmarking multiple operations ({self.iterations} iterations)...")

        for i in range(self.iterations):
            with self.timer("multiple_operations"):
                # Create database instance
                db = MRPCDatabase()

                # Simulate typical dashboard operations
                summary = db.get_posts_summary()
                users = db.get_all_users()

                # Simulate basic data access
                if summary and summary.get("total_posts", 0) > 0:
                    # Get available tags (lightweight operation)
                    tags = db.get_available_tags()

    def calculate_statistics(self, operation_name):
        """Calculate comprehensive statistics for an operation"""
        if operation_name not in self.results:
            return None

        data = self.results[operation_name]
        return {
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "min": min(data),
            "max": max(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "count": len(data),
        }

    def get_performance_status(self, mean_ms):
        """Determine performance status based on mean timing"""
        if mean_ms < 1.0:
            return " Excellent"
        elif mean_ms < 5.0:
            return "🟡 Good"
        elif mean_ms < 10.0:
            return "🟠 Acceptable"
        else:
            return "🔴 Needs Optimization"

    def print_results(self):
        """Print comprehensive benchmark results"""
        print("\n📈 PERFORMANCE RESULTS")
        print("=" * 60)

        for operation in ["database_creation", "auth_flow", "multiple_operations"]:
            stats = self.calculate_statistics(operation)
            if stats:
                status = self.get_performance_status(stats["mean"])

                print(f"\n🔸 {operation.replace('_', ' ').title()}:")
                print(f"   Mean:   {stats['mean']:.3f}ms")
                print(f"   Median: {stats['median']:.3f}ms")
                print(f"   Min:    {stats['min']:.3f}ms")
                print(f"   Max:    {stats['max']:.3f}ms")
                print(f"   StdDev: {stats['stdev']:.3f}ms")
                print(f"   Status: {status}")

    def save_results(self, filepath=None):
        """Save results to file for historical comparison"""
        if filepath is None:
            filepath = project_root / "benchmark_results.txt"

        with open(filepath, "w") as f:
            f.write("Database Performance Benchmark Results\n")
            f.write("=" * 50 + "\n\n")

            for operation in ["database_creation", "auth_flow", "multiple_operations"]:
                stats = self.calculate_statistics(operation)
                if stats:
                    f.write(f"{operation.replace('_', ' ').title()}:\n")
                    f.write(f"  Mean: {stats['mean']:.3f}ms\n")
                    f.write(f"  Median: {stats['median']:.3f}ms\n")
                    f.write(f"  Min: {stats['min']:.3f}ms\n")
                    f.write(f"  Max: {stats['max']:.3f}ms\n")
                    f.write(f"  StdDev: {stats['stdev']:.3f}ms\n\n")

        print(f"\n💾 Results saved to {filepath}")

    def run_full_benchmark(self):
        """Run all benchmarks and display results"""
        print("🚀 Starting Database Performance Benchmark")
        print("=" * 60)

        # Run all benchmarks
        self.benchmark_database_creation()
        self.benchmark_auth_flow()
        self.benchmark_multiple_operations()

        print("\n Benchmark complete!")

        # Display results
        self.print_results()

        # Save to file
        self.save_results()

        # Analysis and recommendations
        self._print_analysis()

        return self.results

    def _print_analysis(self):
        """Print analysis and recommendations"""
        print("\n🎯 ANALYSIS:")
        print("This benchmark measures the current database instantiation pattern.")
        print(
            "Look for operations taking >5ms - these indicate optimization opportunities."
        )
        print("\nNext steps:")
        print("1. Note the baseline performance")
        print("2. Implement optimizations")
        print("3. Re-run benchmark to measure improvements")


# Pytest test functions
class TestDatabasePerformance:
    """Pytest test class for database performance benchmarking"""

    def test_database_performance_quick(self):
        """Quick performance test with fewer iterations for CI"""
        benchmark = DatabaseBenchmark(iterations=10)
        results = benchmark.run_full_benchmark()

        # Assert that basic operations complete in reasonable time
        db_stats = benchmark.calculate_statistics("database_creation")
        auth_stats = benchmark.calculate_statistics("auth_flow")
        multi_stats = benchmark.calculate_statistics("multiple_operations")

        # Performance thresholds (adjusted for optimized version)
        assert db_stats["mean"] < 2.0, (
            f"Database creation too slow: {db_stats['mean']:.3f}ms"
        )
        assert auth_stats["mean"] < 2.0, (
            f"Auth flow too slow: {auth_stats['mean']:.3f}ms"
        )
        assert multi_stats["mean"] < 15.0, (
            f"Multiple operations too slow: {multi_stats['mean']:.3f}ms"
        )

    def test_database_performance_comprehensive(self):
        """Comprehensive performance test with full iterations"""
        benchmark = DatabaseBenchmark(iterations=50)
        results = benchmark.run_full_benchmark()

        # Verify all benchmarks completed
        assert "database_creation" in results
        assert "auth_flow" in results
        assert "multiple_operations" in results

        # Verify we got expected number of measurements
        assert len(results["database_creation"]) == 50
        assert len(results["auth_flow"]) == 50
        assert len(results["multiple_operations"]) == 50


def main():
    """Main function for standalone execution"""
    print("🎯 Database Performance Benchmark Tool")
    print("=====================================\n")

    # Run comprehensive benchmark
    benchmark = DatabaseBenchmark(iterations=100)
    benchmark.run_full_benchmark()


if __name__ == "__main__":
    main()
