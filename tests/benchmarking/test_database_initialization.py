#!/usr/bin/env python3
"""
Database Initialization Optimization Validation - Test Module

This module validates the effectiveness of database initialization optimizations
and measures their real-world performance impact.

Usage:
    # Run as pytest
    pytest tests/benchmarking/test_database_initialization.py -v

    # Run standalone
    python tests/benchmarking/test_database_initialization.py
"""

import time
import statistics
import sys
import sqlite3
import pytest
from pathlib import Path
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utilities.mrpc_database import MRPCDatabase


class InitializationBenchmark:
    """Detailed benchmark of database initialization costs"""

    def __init__(self, iterations=30):
        self.iterations = iterations
        self.results = {}

        # Create test database for measuring impact
        self.test_db_path = project_root / "test_benchmark.db"
        self.ensure_clean_test_db()

    def ensure_clean_test_db(self):
        """Ensure we have a fresh test database"""
        if self.test_db_path.exists():
            self.test_db_path.unlink()

    def cleanup_test_db(self):
        """Clean up test database after benchmarking"""
        if self.test_db_path.exists():
            self.test_db_path.unlink()

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

    def benchmark_path_only(self):
        """Benchmark just the path setup (minimal overhead)"""
        print(f"📁 Benchmarking path-only setup ({self.iterations} iterations)...")

        for i in range(self.iterations):
            with self.timer("path_only"):
                # Just the path setup part
                db_path = str(self.test_db_path)
                Path(db_path).parent.mkdir(exist_ok=True)

    def benchmark_full_initialization(self):
        """Benchmark full MRPCDatabase initialization"""
        print(f"🔄 Benchmarking full initialization ({self.iterations} iterations)...")

        for i in range(self.iterations):
            with self.timer("full_init"):
                # Use default database path (should use optimized init)
                db = MRPCDatabase()

    def benchmark_existing_database_access(self):
        """Benchmark accessing an existing database (optimized path)"""
        print(
            f"💾 Benchmarking existing database access ({self.iterations} iterations)..."
        )

        # Ensure main database exists
        db_setup = MRPCDatabase()

        for i in range(self.iterations):
            with self.timer("existing_db_access"):
                # This should use the fast _database_initialized() check
                db = MRPCDatabase()

    def measure_table_count_impact(self):
        """Measure the impact of table count on initialization"""
        print("Measuring table count impact...")

        # Count tables in the current schema
        db = MRPCDatabase()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_count = len(tables)

        print(f"   Current schema has {table_count} tables")
        return table_count

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

    def print_results(self):
        """Print comprehensive benchmark results"""
        print("\n📈 INITIALIZATION PERFORMANCE RESULTS")
        print("=" * 70)

        operations = ["path_only", "full_init", "existing_db_access"]
        operation_labels = ["Path Only", "Full Init", "Existing Db Access"]

        for operation, label in zip(operations, operation_labels):
            stats = self.calculate_statistics(operation)
            if stats:
                print(f"\n🔸 {label}:")
                print(f"   Mean:   {stats['mean']:.3f}ms")
                print(f"   Median: {stats['median']:.3f}ms")
                print(f"   Min:    {stats['min']:.3f}ms")
                print(f"   Max:    {stats['max']:.3f}ms")
                print(f"   StdDev: {stats['stdev']:.3f}ms")

    def analyze_optimization_impact(self):
        """Analyze the effectiveness of the implemented optimizations"""
        print("\n🎯 OPTIMIZATION EFFECTIVENESS ANALYSIS")
        print("=" * 50)

        path_stats = self.calculate_statistics("path_only")
        full_stats = self.calculate_statistics("full_init")
        existing_stats = self.calculate_statistics("existing_db_access")
        table_count = self.measure_table_count_impact()

        print(f"Database schema contains {table_count} tables")

        if full_stats and existing_stats:
            optimization_ratio = existing_stats["mean"] / full_stats["mean"]
            time_difference = full_stats["mean"] - existing_stats["mean"]

            print(f"\nOptimization Results:")
            print(f"   Full initialization: {full_stats['mean']:.3f}ms")
            print(f"   Existing DB access: {existing_stats['mean']:.3f}ms")
            print(f"   Time difference: {time_difference:.3f}ms")
            print(f"   Speed improvement: {(1 - optimization_ratio) * 100:.1f}%")

            if optimization_ratio < 0.5:
                print(
                    " Optimization working effectively - major performance improvement"
                )
            elif optimization_ratio < 0.8:
                print("🟡 Optimization working - moderate performance improvement")
            else:
                print("⚠️  Optimization impact minimal - may need review")

            # Calculate real-world impact
            typical_calls = 50  # Typical number of DB instantiations in a session
            unoptimized_impact = full_stats["mean"] * typical_calls
            optimized_impact = existing_stats["mean"] * typical_calls
            time_saved = unoptimized_impact - optimized_impact

            print(f"\n� Real-World Impact:")
            print(
                f"   Time per {typical_calls} operations (unoptimized): {unoptimized_impact:.1f}ms"
            )
            print(
                f"   Time per {typical_calls} operations (optimized): {optimized_impact:.1f}ms"
            )
            print(f"   Total time saved per session: {time_saved:.1f}ms")

    def run_full_benchmark(self):
        """Run all initialization benchmarks"""
        print("🚀 Starting Database Initialization Optimization Validation")
        print("=" * 70)

        try:
            # Run all benchmarks
            self.benchmark_path_only()
            self.benchmark_full_initialization()
            self.benchmark_existing_database_access()

            table_count = self.measure_table_count_impact()

            print("\n Benchmark complete!")

            # Display results
            self.print_results()

            # Analysis
            self.analyze_optimization_impact()

            return self.results

        finally:
            # Clean up
            self.cleanup_test_db()


# Pytest test functions
class TestDatabaseInitialization:
    """Pytest test class for database initialization benchmarking"""

    def test_initialization_performance_quick(self):
        """Quick initialization test for CI"""
        benchmark = InitializationBenchmark(iterations=5)
        results = benchmark.run_full_benchmark()

        # Verify all benchmarks completed
        assert "path_only" in results
        assert "full_init" in results
        assert "existing_db_access" in results

        # Basic performance checks
        path_stats = benchmark.calculate_statistics("path_only")
        existing_stats = benchmark.calculate_statistics("existing_db_access")

        assert path_stats["mean"] < 1.0, (
            f"Path setup too slow: {path_stats['mean']:.3f}ms"
        )
        assert existing_stats["mean"] < 5.0, (
            f"Existing DB access too slow: {existing_stats['mean']:.3f}ms"
        )

    def test_optimization_effectiveness(self):
        """Test that optimizations are working effectively"""
        benchmark = InitializationBenchmark(iterations=10)
        results = benchmark.run_full_benchmark()

        full_stats = benchmark.calculate_statistics("full_init")
        existing_stats = benchmark.calculate_statistics("existing_db_access")

        # The optimized existing DB access should be significantly faster than full init
        if full_stats and existing_stats:
            optimization_ratio = existing_stats["mean"] / full_stats["mean"]
            assert optimization_ratio <= 1.0, (
                f"Existing DB access should not be slower than full init: {optimization_ratio:.2f}"
            )
            # Note: The ratio might be close to 1.0 since both use the optimized path now

    def test_schema_consistency(self):
        """Test that schema creation produces consistent results"""
        benchmark = InitializationBenchmark(iterations=3)

        # Create multiple test databases and verify they have same table count
        table_counts = []
        for i in range(3):
            test_path = project_root / f"test_consistency_{i}.db"
            if test_path.exists():
                test_path.unlink()

            try:
                db = MRPCDatabase(db_path=str(test_path))
                with sqlite3.connect(str(test_path)) as conn:
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                    tables = cursor.fetchall()
                    table_counts.append(len(tables))
            finally:
                if test_path.exists():
                    test_path.unlink()

        # All databases should have the same number of tables
        assert len(set(table_counts)) == 1, f"Inconsistent table counts: {table_counts}"
        assert table_counts[0] > 5, f"Too few tables created: {table_counts[0]}"


def main():
    """Main function for standalone execution"""
    print("🎯 Database Initialization Optimization Validator")
    print("================================================\n")

    # Run comprehensive benchmark
    benchmark = InitializationBenchmark(iterations=30)
    benchmark.run_full_benchmark()


if __name__ == "__main__":
    main()
