"""
Database Performance Benchmarking Module

This module provides comprehensive benchmarking tools for measuring
and analyzing database performance in the MRPC application.

Modules:
    test_database_performance: Comprehensive database operation benchmarking

Usage:
    # Run all benchmarking tests
    pytest tests/benchmarking/ -v

    # Run specific benchmark
    pytest tests/benchmarking/test_database_performance.py -v

    # Run standalone benchmarks
    python tests/benchmarking/test_database_performance.py
"""

__version__ = "1.0.0"
__author__ = "MRPC Development Team"

from .test_database_performance import DatabaseBenchmark

__all__ = ["DatabaseBenchmark"]
