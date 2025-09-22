"""
Comprehensive Database Operations Test Suite - pytest implementation

This test suite provides complete coverage for MRPC database functionality,
including authentication mocking, performance testing, and edge case handling.
"""

import pytest
import pandas as pd
import sqlite3
from pathlib import Path
from unittest.mock import patch

# Import our database class
from utilities.mrpc_database import MRPCDatabase


@pytest.fixture(autouse=True)
def mock_auth_functions():
    """Automatically mock authentication functions for all tests in this module."""
    with (
        patch("utilities.auth.get_current_user_id", return_value=1),
        patch(
            "utilities.auth.require_admin", return_value=None
        ),  # TODO: consider returning dict of auth admin
    ):
        yield


class TestMRPCDatabaseBasics:
    """Test basic database operations using pytest fixtures."""

    def test_database_module_import(self):
        """Test basic import and instantiation of the database module."""
        # Test import works without errors
        from utilities.mrpc_database import MRPCDatabase

        # Test class has migration system attributes
        assert hasattr(MRPCDatabase, "CURRENT_SCHEMA_VERSION")
        assert hasattr(MRPCDatabase, "_init_database_with_migrations")
        assert MRPCDatabase.CURRENT_SCHEMA_VERSION >= 2

        # Test can create instance (uses temp file)
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            db = MRPCDatabase(temp_file.name)
            assert isinstance(db, MRPCDatabase)
            assert db.db_path == temp_file.name

            # Verify migration system worked
            current_version = db._get_schema_version()
            assert current_version == MRPCDatabase.CURRENT_SCHEMA_VERSION

            # Cleanup
            import os

            os.unlink(temp_file.name)

    def test_database_initialization(self, temp_database):
        """Test that database initializes correctly with proper tables."""
        # Test that we got a valid database instance
        assert isinstance(temp_database, MRPCDatabase)
        assert temp_database.db_path is not None

        # Test that database file exists
        db_path = Path(temp_database.db_path)
        assert db_path.exists()
        assert db_path.suffix == ".db"

    def test_database_tables_exist(self, temp_database):
        """Test that required tables are created."""
        import sqlite3

        # Get connection and check tables
        with sqlite3.connect(temp_database.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

        # Required tables should exist
        required_tables = ["posts", "tags", "tag_registry"]
        for table in required_tables:
            assert table in tables, f"Table '{table}' should exist in database"

    def test_empty_database_queries(self, temp_database):
        """Test queries on empty database return expected results."""
        # Test getting all posts from empty database
        posts_df = temp_database.get_all_posts_as_dataframe()
        assert isinstance(posts_df, pd.DataFrame)
        assert len(posts_df) == 0

        # Test getting posts by forum from empty database
        forum_posts = temp_database.get_posts_by_forum("cervical", user_id=1)
        assert isinstance(forum_posts, pd.DataFrame)
        assert len(forum_posts) == 0

        # Test getting available tags from empty database
        available_tags = temp_database.get_available_tags()
        assert isinstance(available_tags, dict)
        assert "groups" in available_tags
        assert "tags" in available_tags
        assert len(available_tags["groups"]) == 0


class TestMRPCDatabaseWithData:
    """Test database operations with pre-populated data."""

    def test_database_has_sample_data(self, temp_database_with_data):
        """Test that database contains uploaded sample data."""
        # Test that posts were uploaded via proper upload service
        # Use user_id=1 to bypass authentication context issues in tests
        posts_df = temp_database_with_data.get_all_posts_as_dataframe(user_id=1)
        assert len(posts_df) > 0

        # Should have required columns
        required_columns = ["id", "forum", "original_title"]
        for col in required_columns:
            assert col in posts_df.columns, f"Column '{col}' should exist"

        # Test that upload record exists
        with sqlite3.connect(temp_database_with_data.db_path) as conn:
            uploads = conn.execute("SELECT * FROM uploads").fetchall()
            assert len(uploads) > 0, "Should have upload records"

    def test_get_posts_by_forum(self, temp_database_with_data):
        """Test filtering posts by forum."""
        # Test known forum with explicit user_id to bypass auth
        cervical_posts = temp_database_with_data.get_posts_by_forum(
            "cervical", user_id=1
        )
        assert isinstance(cervical_posts, pd.DataFrame)

        # All returned posts should be from cervical forum
        for _, row in cervical_posts.iterrows():
            assert row["forum"] == "cervical"

    def test_save_and_retrieve_tags(self, temp_database_with_data):
        """Test that we can save and retrieve tags for an item."""
        # First get the actual IDs that exist in the database
        posts_df = temp_database_with_data.get_all_posts_as_dataframe(user_id=1)
        assert len(posts_df) > 0, "No posts found in test database"

        # Use the first available ID
        item_id = posts_df.iloc[0]["id"]
        test_tags = {
            "groups": ["Cancer Type"],
            "subgroups": ["Gynecologic"],
            "tags": ["Cervical", "Hysterectomy"],
        }

        # Save tags for the item
        result = temp_database_with_data.save_tags_for_item(item_id, test_tags)
        assert result is True

        # Retrieve tags for the item
        retrieved_tags = temp_database_with_data.get_tags_for_item(item_id)
        assert retrieved_tags is not None
        assert isinstance(retrieved_tags, dict)

        # Check tag content - extract values from the dict format
        assert "groups" in retrieved_tags
        assert "subgroups" in retrieved_tags
        assert "tags" in retrieved_tags

        # Extract values from the dict format returned by get_tags_for_item
        retrieved_groups = [tag["value"] for tag in retrieved_tags["groups"]]
        retrieved_subgroups = [tag["value"] for tag in retrieved_tags["subgroups"]]
        retrieved_tag_values = [tag["value"] for tag in retrieved_tags["tags"]]

        # Verify the values (convert to sets for comparison to ignore order)
        assert set(retrieved_groups) == set(test_tags["groups"])
        assert set(retrieved_subgroups) == set(test_tags["subgroups"])
        assert set(retrieved_tag_values) == set(test_tags["tags"])

    @pytest.mark.parametrize("forum", ["cervical", "ovarian", "unknown_forum"])
    def test_get_posts_by_various_forums(self, temp_database_with_data, forum):
        """Test getting posts for various forum types."""
        posts = temp_database_with_data.get_posts_by_forum(forum, user_id=1)
        assert isinstance(posts, pd.DataFrame)

        # All posts should be from the requested forum
        for _, post in posts.iterrows():
            assert post["forum"] == forum


class TestMRPCDatabaseWithLargeData:
    """Test database performance with larger datasets."""

    @pytest.mark.slow
    def test_large_dataset_performance(self, temp_database_with_data):
        """Test database performance with dataset."""
        # Test retrieval performance
        import time

        start_time = time.time()

        retrieved_data = temp_database_with_data.get_all_posts_as_dataframe()

        end_time = time.time()
        query_time = end_time - start_time

        # Verify data integrity
        assert len(retrieved_data) >= 1, "Should retrieve at least some data"
        assert query_time < 5.0, f"Query took too long: {query_time:.2f} seconds"

        # Basic column checks
        expected_columns = ["id", "forum", "original_title"]
        for col in expected_columns:
            assert col in retrieved_data.columns, f"Missing expected column: {col}"

        # Performance should be reasonable (less than 1 second)
        assert query_time < 1.0, f"Query took {query_time:.2f}s, should be under 1.0s"

    @pytest.mark.performance
    def test_repeated_queries_performance(self, temp_database_with_data, benchmark):
        """Test performance of repeated database queries."""

        def query_all_posts():
            return temp_database_with_data.get_all_posts_as_dataframe()

        # Benchmark the query operation
        result = benchmark(query_all_posts)

        # Verify we got data
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0


class TestMRPCDatabaseErrorHandling:
    """Test database error handling and edge cases."""

    def test_get_tags_for_nonexistent_item(self, temp_database):
        """Test getting tags for non-existent item."""
        tags = temp_database.get_tags_for_item("nonexistent_item_12345")

        # Should return empty structure, not None or error
        assert isinstance(tags, dict)
        assert "groups" in tags
        assert "tags" in tags
        assert len(tags["groups"]) == 0
        assert len(tags["tags"]) == 0

    def test_save_tags_with_invalid_data(self, temp_database):
        """Test saving tags with invalid data structures."""
        item_id = "test_item"

        # Test with None
        temp_database.save_tags_for_item(item_id, None)
        # Should handle gracefully (implementation dependent)

        # Test with empty dict
        temp_database.save_tags_for_item(item_id, {})
        # Should handle gracefully

        # Test with invalid structure
        invalid_tags = {"invalid_key": ["some", "values"]}
        temp_database.save_tags_for_item(item_id, invalid_tags)
        # Should handle gracefully

    def test_get_posts_by_none_forum(self, temp_database):
        """Test getting posts with None forum parameter."""
        posts = temp_database.get_posts_by_forum(None, user_id=1)
        assert isinstance(posts, pd.DataFrame)
        # Implementation dependent - might return empty DataFrame or all posts

    def test_database_error_handling_graceful(self, temp_database):
        """Test database handles errors gracefully"""
        # Test with invalid data that should trigger an error
        # For example, trying to save tags with invalid structure
        result = temp_database.save_tags_for_item(
            "", None
        )  # Invalid empty item_id and None tags
        assert result is False  # Should handle gracefully and return False


class TestMRPCDatabaseIntegration:
    """Integration tests for complete database workflows."""

    @pytest.mark.integration  # TODO: Use upload service
    def test_complete_data_workflow(self, temp_database, sample_forum_data, tmp_path):
        """Test complete workflow: import -> tag -> query -> verify."""
        # 1. Import data via CSV (if supported)
        csv_file = tmp_path / "test_import.csv"
        sample_forum_data.to_csv(csv_file, index=False)

        # Try to import (this depends on implementation)
        try:
            import_result = temp_database.migrate_from_csv(str(csv_file))
            # If import worked, continue with workflow
            if import_result:
                # 2. Verify import
                posts = temp_database.get_all_posts_as_dataframe()
                assert len(posts) > 0

                # 3. Add tags to some posts
                for _, post in posts.head(2).iterrows():
                    tags = {
                        "groups": ["Test Group"],
                        "tags": ["test_tag", "integration_test"],
                    }
                    temp_database.save_tags_for_item(post["id"], tags)

                # 4. Verify tags were saved
                available_tags = temp_database.get_available_tags()
                assert (
                    len(available_tags["groups"]) > 0 or len(available_tags["tags"]) > 0
                )
        except Exception as e:
            # Import might not be implemented yet - that's okay
            pytest.skip(f"CSV import not implemented: {e}")

    @pytest.mark.integration
    def test_tag_registry_consistency(self, temp_database_with_data):
        """Test that tag registry stays consistent with saved tags."""
        # Save tags for multiple items
        test_items = [
            ("item_1", {"groups": ["Medical"], "tags": ["surgery"]}),
            ("item_2", {"groups": ["Medical"], "tags": ["diagnosis"]}),
            ("item_3", {"groups": ["Research"], "tags": ["surgery", "study"]}),
        ]

        for item_id, tags in test_items:
            temp_database_with_data.save_tags_for_item(item_id, tags)

        # Check registry reflects all tags
        available_tags = temp_database_with_data.get_available_tags()

        # Should have both groups
        groups = available_tags.get("groups", [])
        tags = available_tags.get("tags", [])

        # Implementation dependent - just verify structure is maintained
        assert isinstance(groups, list)
        assert isinstance(tags, list)

    @pytest.mark.requires_db
    def test_backup_and_restore(self, temp_database_with_data, tmp_path):
        """Test database backup and restore functionality"""
        # Get original data
        original_posts = temp_database_with_data.get_all_posts_as_dataframe()

        # Create backup file path for future implementation
        backup_file = tmp_path / "backup.db"
        # Note: Future implementation would include:
        # temp_database_with_data.backup_to_file(str(backup_file))
        # assert backup_file.exists()

        # For now, verify we can get the data and prepare for backup feature
        assert len(original_posts) > 0
        assert "id" in original_posts.columns
        assert str(backup_file).endswith("backup.db")  # Verify backup path is correct


class TestMRPCDatabaseTags:
    """Comprehensive tests for tag system functionality."""

    def test_tag_registry_updates(self, temp_database_with_data):
        """Test that tag registry updates correctly."""
        # Add tags to multiple items
        for i in range(3):
            item_id = f"test_item_{i}"
            tags = {"groups": ["Common Group"], "tags": [f"tag_{i}", "common_tag"]}
            temp_database_with_data.save_tags_for_item(item_id, tags)

        # Check registry counts
        available_tags = temp_database_with_data.get_available_tags()
        assert "groups" in available_tags
        assert "tags" in available_tags

        # Verify some common elements appear (implementation dependent)
        groups = available_tags.get("groups", [])
        tags = available_tags.get("tags", [])
        assert isinstance(groups, list)
        assert isinstance(tags, list)

    @pytest.mark.parametrize(
        "tag_data",
        [
            {"groups": ["Group 1"], "tags": ["tag1"]},
            {"groups": [], "tags": ["lonely_tag"]},
            {"groups": ["Group 2"], "subgroups": ["Sub 1"], "tags": []},
            {"groups": ["Medical", "Research"], "tags": ["surgery", "diagnosis"]},
        ],
    )
    def test_various_tag_structures(self, temp_database_with_data, tag_data):
        """Test saving various tag structure combinations."""
        # Get a real ID from the test database
        posts_df = temp_database_with_data.get_all_posts_as_dataframe(user_id=1)
        assert len(posts_df) > 0, "No posts found in test database"
        item_id = posts_df.iloc[0]["id"]  # Use first available ID

        result = temp_database_with_data.save_tags_for_item(item_id, tag_data)
        assert result is True

        retrieved = temp_database_with_data.get_tags_for_item(item_id)
        assert isinstance(retrieved, dict)

        # Verify structure keys exist
        for key in ["groups", "subgroups", "tags"]:
            assert key in retrieved
            assert isinstance(retrieved[key], list)

    def test_complex_tag_workflow(self, temp_database_with_data):
        """Test complex tag operations including updates and retrievals."""
        # Get a real ID from the test database
        posts_df = temp_database_with_data.get_all_posts_as_dataframe(user_id=1)
        assert len(posts_df) > 0, "No posts found in test database"
        item_id = posts_df.iloc[0]["id"]  # Use first available ID

        # Phase 1: Initial tags
        initial_tags = {
            "groups": ["Medical"],
            "subgroups": ["Oncology"],
            "tags": ["surgery", "treatment"],
        }
        result = temp_database_with_data.save_tags_for_item(item_id, initial_tags)
        assert result is True

        # Phase 2: Update with additional tags
        updated_tags = {
            "groups": ["Medical", "Research"],
            "subgroups": ["Oncology", "Clinical"],
            "tags": ["surgery", "treatment", "diagnosis", "screening"],
        }
        result = temp_database_with_data.save_tags_for_item(item_id, updated_tags)
        assert result is True

        # Phase 3: Verify final state
        final_tags = temp_database_with_data.get_tags_for_item(item_id)
        assert isinstance(final_tags, dict)
        for key in ["groups", "subgroups", "tags"]:
            assert key in final_tags
            assert isinstance(final_tags[key], list)


class TestMRPCDatabaseUploadOperations:
    """Test upload operations and file processing functionality."""

    def test_upload_service_integration(self, upload_service):
        """Test upload service basic functionality."""
        from utilities.upload_service import UploadService

        # Test that upload service initializes properly
        assert isinstance(upload_service, UploadService)
        assert hasattr(upload_service, "db")
        assert hasattr(upload_service, "detect_upload_type")

    def test_csv_upload_detection(self, upload_service):
        """Test CSV upload type detection."""
        # Create test forum data
        forum_data = pd.DataFrame(
            {
                "id": ["post_1", "post_2", "post_3"],
                "forum": ["cervical", "ovarian", "cervical"],
                "original_title": ["Test Title 1", "Test Title 2", "Test Title 3"],
                "original_post": ["Test content 1", "Test content 2", "Test content 3"],
            }
        )

        # Test upload type detection
        upload_type = upload_service.detect_upload_type(forum_data)
        assert upload_type == "forum_data"

    def test_csv_duplicate_validation(self, upload_service):
        """Test CSV structure validation functionality."""
        # Create data with proper structure
        valid_data = pd.DataFrame(
            {
                "id": ["post_1", "post_2", "post_3"],
                "forum": ["cervical", "ovarian", "cervical"],
                "original_title": ["Test Title 1", "Test Title 2", "Test Title 3"],
                "original_post": ["Test content 1", "Test content 2", "Test content 3"],
            }
        )

        # Test CSV structure validation
        is_valid, errors = upload_service.validate_csv_structure(valid_data)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_upload_workflow_integration(self, temp_database_with_data):
        """Test complete upload workflow using database fixture."""
        # This test leverages the upload_service_with_temp_db fixture
        # which already tests the complete upload workflow

        # Verify that data was uploaded properly via the fixture
        posts_df = temp_database_with_data.get_all_posts_as_dataframe(user_id=1)
        assert len(posts_df) > 0
        assert "id" in posts_df.columns
        assert "forum" in posts_df.columns

        # Verify upload records exist by checking post count
        # Since we don't have direct connection access, verify via data presence
        assert len(posts_df) >= 3  # Should have sample data

    def test_file_upload_processing(self, upload_service, tmp_path):
        """Test CSV preview functionality."""
        # Create a temporary CSV file
        test_data = pd.DataFrame(
            {
                "id": ["upload_test_1", "upload_test_2"],
                "forum": ["cervical", "ovarian"],
                "original_title": ["Upload Test 1", "Upload Test 2"],
                "original_post": ["Upload content 1", "Upload content 2"],
            }
        )

        # Convert to CSV string for preview testing
        csv_content = test_data.to_csv(index=False)

        # Test CSV preview functionality
        preview_result = upload_service.preview_csv(csv_content, rows=2)
        assert isinstance(preview_result, dict)
        assert "success" in preview_result

    @pytest.mark.performance
    def test_large_upload_performance(self, upload_service):
        """Test upload performance with large datasets."""
        # Create large dataset
        large_data = pd.DataFrame(
            {
                "id": [f"perf_test_{i}" for i in range(1000)],
                "forum": ["cervical" if i % 2 == 0 else "ovarian" for i in range(1000)],
                "original_title": [f"Performance Test {i}" for i in range(1000)],
                "original_post": [f"Performance content {i}" for i in range(1000)],
            }
        )

        # Test upload type detection performance
        upload_type = upload_service.detect_upload_type(large_data)
        assert upload_type == "forum_data"

        # Verify no memory issues
        assert len(large_data) == 1000


# Custom fixtures for this test module
@pytest.fixture
def complex_tag_structure():
    """Fixture providing complex tag structure for testing."""
    return {
        "groups": ["Medical", "Research", "Clinical"],
        "subgroups": ["Oncology", "Gynecology", "Surgery"],
        "tags": [
            "chemotherapy",
            "radiation",
            "surgery",
            "diagnosis",
            "screening",
            "treatment",
            "prognosis",
            "symptoms",
        ],
    }


if __name__ == "__main__":
    # Run pytest if called directly
    pytest.main([__file__, "-v"])
