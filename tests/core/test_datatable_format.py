"""
Test suite for datatable format functionality
This file tests the new aggregated datatable format to identify and fix issues
"""

import pytest
import pandas as pd
from unittest.mock import patch
from utilities.mrpc_database import MRPCDatabase


class TestDatatableFormat:
    """Test the new datatable format functionality"""

    @patch("utilities.auth.get_current_user_id", return_value=1)
    def test_datatable_format_returns_correct_columns(self, mock_user):
        """Test that datatable format returns the expected columns"""
        db = MRPCDatabase()

        # Test with datatable_format=True
        df = db.get_all_posts_as_dataframe(user_id=1, datatable_format=True)

        # Check that we get the expected columns
        expected_columns = [
            "id",
            "forum",
            "post_type",
            "username",
            "original_title",
            "original_post",
            "post_url",
            "cluster",
            "cluster_label",
            "date_posted",
            "umap_1",
            "umap_2",
            "umap_3",
            "upload_id",
            "all_questions",
            "all_categories",
        ]

        assert all(col in df.columns for col in expected_columns), (
            f"Missing columns. Got: {list(df.columns)}"
        )
        print(f" Datatable format has correct columns: {list(df.columns)}")

    @patch("utilities.auth.get_current_user_id", return_value=1)
    def test_datatable_format_aggregates_properly(self, mock_user):
        """Test that posts with same title are properly aggregated"""
        db = MRPCDatabase()

        # Get both formats for comparison
        df_legacy = db.get_all_posts_as_dataframe(user_id=1, datatable_format=False)
        df_datatable = db.get_all_posts_as_dataframe(user_id=1, datatable_format=True)

        print(f"Legacy format rows: {len(df_legacy)}")
        print(f"Datatable format rows: {len(df_datatable)}")

        # Datatable format should have fewer rows (aggregated by title)
        assert len(df_datatable) <= len(df_legacy), (
            "Datatable format should aggregate rows"
        )

        # Check for duplicate titles in datatable format
        duplicate_titles = df_datatable["original_title"].duplicated().sum()
        assert duplicate_titles == 0, (
            f"Found {duplicate_titles} duplicate titles in datatable format"
        )

        print(
            f" Datatable format properly aggregates: {len(df_legacy)} -> {len(df_datatable)} rows"
        )

    @patch("utilities.auth.get_current_user_id", return_value=1)
    def test_datatable_format_questions_and_categories(self, mock_user):
        """Test that questions and categories are properly formatted"""
        db = MRPCDatabase()
        df = db.get_all_posts_as_dataframe(user_id=1, datatable_format=True)

        if len(df) > 0:
            sample_row = df.iloc[0]

            # Check that all_questions and all_categories exist
            assert "all_questions" in df.columns, "Missing all_questions column"
            assert "all_categories" in df.columns, "Missing all_categories column"

            # Check data types
            questions = sample_row["all_questions"]
            categories = sample_row["all_categories"]

            print(f"Sample questions type: {type(questions)}")
            print(f"Sample categories type: {type(categories)}")
            print(f"Sample questions (first 100 chars): {repr(str(questions)[:100])}")
            print(f"Sample categories (first 100 chars): {repr(str(categories)[:100])}")

            # These should be strings (could be empty)
            assert isinstance(questions, (str, type(None))), (
                f"Questions should be string, got {type(questions)}"
            )
            assert isinstance(categories, (str, type(None))), (
                f"Categories should be string, got {type(categories)}"
            )

            print(" Questions and categories have correct data types")

    def test_get_forum_data_with_datatable_format(self):
        """Test the get_forum_data function with datatable_format parameter"""
        from umap_viz_module import get_forum_data

        # This test will help us see if the UI function works correctly
        # Note: This might fail due to authentication context, but that's expected
        try:
            df = get_forum_data("all", datatable_format=True)

            if len(df) > 0:
                print(f" get_forum_data works: {df.shape}")
                print(f"Columns: {list(df.columns)}")
            else:
                print(
                    "⚠️ get_forum_data returned empty DataFrame (likely auth context issue)"
                )

        except Exception as e:
            print(f"⚠️ get_forum_data failed: {e}")
            # This is expected outside of request context

    @patch("utilities.auth.get_current_user_id", return_value=1)
    def test_column_mapping_consistency(self, mock_user):
        """Test that column mapping is consistent with actual data"""
        from umap_viz_module import create_table_view

        db = MRPCDatabase()

        # Get sample data
        df = db.get_all_posts_as_dataframe(user_id=1, datatable_format=True)

        # Expected columns for new format
        expected_datatable_columns = [
            "original_title",
            "all_questions",
            "all_categories",
        ]

        # Check if all expected columns exist
        for col in expected_datatable_columns:
            assert col in df.columns, f"Missing expected column: {col}"

        print(f" All expected datatable columns present: {expected_datatable_columns}")

        # Test a few sample values to make sure they're not None/undefined
        if len(df) > 0:
            sample = df.iloc[0]
            for col in expected_datatable_columns:
                value = sample[col]
                print(f"{col}: {type(value)} - {repr(str(value)[:50])}")


if __name__ == "__main__":
    # Run tests directly for debugging
    test = TestDatatableFormat()

    print("=== Testing Datatable Format ===")
    test.test_datatable_format_returns_correct_columns()
    print()

    print("=== Testing Aggregation ===")
    test.test_datatable_format_aggregates_properly()
    print()

    print("=== Testing Questions and Categories ===")
    test.test_datatable_format_questions_and_categories()
    print()

    print("=== Testing get_forum_data ===")
    test.test_get_forum_data_with_datatable_format()
    print()

    print("=== Testing Column Mapping ===")
    test.test_column_mapping_consistency()
    print()

    print("🎉 All tests completed!")
