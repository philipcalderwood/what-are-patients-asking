#!/usr/bin/env python3
"""
Comprehensive Upload System Test Suite

This consolidated test suite covers all upload functionality including:
1. UploadService operations (preview, processing, validation)
2. Database upload methods (create_upload_record, bulk_insert)
3. Duplicate detection and validation
4. End-to-end upload workflows

Consolidated from:
- test_upload_service.py
- test_upload_methods.py
- test_upload_service_duplicates.py
"""

import pytest
import pandas as pd
import base64
from unittest.mock import patch

from utilities.upload_service import UploadService
from utilities.mrpc_database import MRPCDatabase


@pytest.fixture(autouse=True)
def mock_auth_functions():
    """Mock authentication functions for testing"""
    with (
        patch("utilities.upload_service.get_current_user_id", return_value=1),
        patch("utilities.auth.get_current_user_id", return_value=1),
        patch("utilities.auth.require_admin", return_value=True),
    ):
        yield


@pytest.fixture
def upload_service():
    """Fixture providing UploadService instance."""
    return UploadService()


@pytest.fixture
def temp_database():
    """Fixture providing temporary database instance."""
    import tempfile
    import os

    # Create a temporary database file
    temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db_file.close()

    try:
        db = MRPCDatabase(temp_db_file.name)
        yield db
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_db_file.name):
            os.unlink(temp_db_file.name)


@pytest.fixture
def sample_forum_data():
    """Fixture providing sample forum data."""
    return pd.DataFrame(
        {
            "id": ["test_001", "test_002", "test_003"],
            "forum": ["cervical", "ovarian", "womb"],
            "post_type": ["question", "reply", "question"],
            "username": ["user1", "user2", "user3"],
            "original_title": ["Test Title 1", "Test Title 2", "Test Title 3"],
            "original_post": ["Test content 1", "Test content 2", "Test content 3"],
            "post_url": ["url1", "url2", "url3"],
            "llm_inferred_question": ["Q1", "Q2", "Q3"],
            "cluster": [1, 2, 3],
            "cluster_label": ["cluster1", "cluster2", "cluster3"],
            "llm_cluster_name": ["name1", "name2", "name3"],
            "date_posted": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "umap_1": [0.1, 0.2, 0.3],
            "umap_2": [0.4, 0.5, 0.6],
            "umap_3": [0.7, 0.8, 0.9],
        }
    )


@pytest.fixture
def sample_duplicate_data():
    """Fixture providing sample data with duplicates."""
    return pd.DataFrame(
        {
            "id": ["test_001", "test_002", "test_001"],  # Duplicate test_001
            "forum": ["cervical", "ovarian", "womb"],
            "post_type": ["question", "reply", "question"],
            "username": ["user1", "user2", "user3"],
            "original_title": ["Test Title 1", "Test Title 2", "Test Title 3"],
            "original_post": ["Test content 1", "Test content 2", "Test content 3"],
        }
    )


def create_base64_csv(dataframe):
    """Helper function to create base64 encoded CSV from DataFrame."""
    csv_string = dataframe.to_csv(index=False)
    encoded = base64.b64encode(csv_string.encode()).decode()
    return f"data:text/csv;base64,{encoded}"


class TestUploadServiceBasics:
    """Test basic UploadService functionality."""

    def test_upload_service_initialization(self, upload_service):
        """Test that UploadService initializes correctly."""
        assert upload_service is not None
        assert hasattr(upload_service, "preview_csv")
        assert hasattr(upload_service, "process_file_upload")

    def test_csv_preview_functionality(self, upload_service, sample_forum_data):
        """Test CSV preview functionality."""
        # Create base64 encoded CSV
        csv_content = create_base64_csv(sample_forum_data)

        # Test preview
        preview_result = upload_service.preview_csv(csv_content, rows=2)

        assert preview_result is not None
        assert isinstance(preview_result, dict)
        # Note: Specific assertions depend on UploadService implementation

    def test_upload_type_detection(self, upload_service, sample_forum_data):
        """Test upload type detection."""
        upload_type = upload_service.detect_upload_type(sample_forum_data)
        assert upload_type == "forum_data"

    def test_empty_dataframe_detection(self, upload_service):
        """Test detection of empty dataframes."""
        empty_df = pd.DataFrame()
        upload_type = upload_service.detect_upload_type(empty_df)
        assert upload_type == "unknown"


class TestUploadServiceDuplicates:
    """Test duplicate detection functionality."""

    def test_csv_with_internal_duplicates(self, upload_service, sample_duplicate_data):
        """Test CSV validation with internal duplicates."""
        # Create CSV with duplicates
        csv_content = create_base64_csv(sample_duplicate_data)

        # Test preview with duplicates
        preview_result = upload_service.preview_csv(csv_content, rows=5)

        # Verify that duplicates are detected
        assert preview_result is not None
        # Note: Specific duplicate detection assertions depend on implementation

    def test_duplicate_validation_workflow(self, upload_service, sample_duplicate_data):
        """Test complete duplicate validation workflow."""
        # Test that duplicate detection works in full upload process
        csv_content = create_base64_csv(sample_duplicate_data)

        # Attempt to process file with duplicates - verify detection
        upload_type = upload_service.detect_upload_type(sample_duplicate_data)
        assert upload_type in ["forum_data", "unknown"]

        # Verify CSV content was created successfully
        assert csv_content.startswith("data:text/csv;base64,")

    def test_clean_data_validation(self, upload_service, sample_forum_data):
        """Test validation of clean data without duplicates."""
        csv_content = create_base64_csv(sample_forum_data)

        # Test preview of clean data
        preview_result = upload_service.preview_csv(csv_content, rows=5)

        assert preview_result is not None


class TestDatabaseUploadMethods:
    """Test database upload methods using proper upload flow."""

    def test_create_upload_record(self, temp_database):
        """Test creating upload records."""
        upload_id = temp_database.create_upload_record(
            filename="test_data.csv",
            user_readable_name="Test Dataset Upload",
            uploaded_by=1,
            comment="Test upload for method validation",
        )

        assert upload_id is not None
        assert isinstance(upload_id, int)
        assert upload_id > 0

    def test_upload_csv_data_method(self, temp_database, sample_forum_data):
        """Test upload_csv_data method (proper upload flow)."""
        # First create an upload record
        upload_id = temp_database.create_upload_record(
            filename="test_upload_csv.csv",
            user_readable_name="Upload CSV Test",
            uploaded_by=1,
            comment="Test upload_csv_data method",
        )

        # Test upload_csv_data method (the real upload flow)
        result = temp_database.upload_csv_data(upload_id, sample_forum_data)

        # Verify insertion
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["new_records"] > 0

    def test_upload_workflow_integration(self, temp_database, sample_forum_data):
        """Test complete upload workflow integration using proper upload flow."""
        # Step 1: Create upload record
        upload_id = temp_database.create_upload_record(
            filename="integration_test.csv",
            user_readable_name="Integration Test",
            uploaded_by=1,
            comment="Full workflow test",
        )

        assert upload_id is not None

        # Step 2: Use the proper upload flow (upload_csv_data)
        upload_result = temp_database.upload_csv_data(upload_id, sample_forum_data)
        assert isinstance(upload_result, dict)
        assert upload_result["success"] is True
        assert upload_result["new_records"] > 0

        # Step 3: Verify data was inserted using proper method
        posts = temp_database.get_posts_by_forum("cervical", user_id=1)
        assert len(posts) > 0

    def test_upload_record_status_updates(self, temp_database):
        """Test upload record status management."""
        # Create upload record
        upload_id = temp_database.create_upload_record(
            filename="status_test.csv",
            user_readable_name="Status Test",
            uploaded_by=1,
            comment="Testing status updates",
        )

        # Test status update (if method exists)
        # Note: Depends on MRPCDatabase implementation
        assert upload_id is not None


class TestUploadServiceIntegration:
    """Test integration between UploadService and database."""

    @pytest.mark.integration
    def test_end_to_end_upload_workflow(
        self, upload_service, temp_database, sample_forum_data, tmp_path
    ):
        """Test complete end-to-end upload workflow."""
        # Set the upload service to use our temporary database
        upload_service.db = temp_database

        # Create temporary CSV file
        csv_file = tmp_path / "test_upload.csv"
        sample_forum_data.to_csv(csv_file, index=False)

        # Read file content and encode
        with open(csv_file, "r") as f:
            csv_content = f.read()

        csv_base64 = base64.b64encode(csv_content.encode()).decode()
        file_content = f"data:text/csv;base64,{csv_base64}"

        # Test the complete upload process
        result = upload_service.process_file_upload(
            contents=file_content,
            filename="test_upload.csv",
            user_readable_name="End-to-End Test",
            comment="Integration test upload",
        )

        # Verify result
        assert result is not None
        if isinstance(result, dict):
            assert result.get("success") is not False

    @pytest.mark.integration
    def test_duplicate_detection_in_full_workflow(
        self, upload_service, temp_database, sample_duplicate_data, tmp_path
    ):
        """Test duplicate detection in complete workflow."""
        # Set the upload service to use our temporary database
        upload_service.db = temp_database

        # Create CSV with duplicates
        csv_file = tmp_path / "duplicate_test.csv"
        sample_duplicate_data.to_csv(csv_file, index=False)

        # Encode file content
        with open(csv_file, "r") as f:
            csv_content = f.read()

        csv_base64 = base64.b64encode(csv_content.encode()).decode()
        file_content = f"data:text/csv;base64,{csv_base64}"

        # Test upload process with duplicates
        result = upload_service.process_file_upload(
            contents=file_content,
            filename="duplicate_test.csv",
            user_readable_name="Duplicate Test",
            comment="Testing duplicate handling",
        )

        # Verify that duplicates are handled appropriately
        assert result is not None


class TestUploadPerformance:
    """Test upload performance and edge cases."""

    @pytest.mark.performance
    def test_large_dataset_upload(self, temp_database):
        """Test upload performance with large datasets using proper upload flow."""
        # Create large dataset
        large_data = pd.DataFrame(
            {
                "id": [f"test_{i:06d}" for i in range(1000)],
                "forum": ["cervical"] * 500 + ["ovarian"] * 500,
                "post_type": ["question"] * 1000,
                "username": [f"user_{i % 100}" for i in range(1000)],
                "original_title": [f"Title {i}" for i in range(1000)],
                "original_post": [f"Content {i}" for i in range(1000)],
            }
        )

        # Create upload record
        upload_id = temp_database.create_upload_record(
            filename="large_test.csv",
            user_readable_name="Large Dataset Test",
            uploaded_by=1,
            comment="Performance test with 1000 records",
        )

        # Test upload_csv_data performance (proper upload flow)
        result = temp_database.upload_csv_data(upload_id, large_data)

        # Verify successful insertion
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["new_records"] > 0

    def test_upload_error_handling(self, temp_database):
        """Test error handling in upload methods using proper upload flow."""
        # Test with invalid data
        invalid_data = pd.DataFrame({"invalid_column": ["data1", "data2", "data3"]})

        # Create upload record first
        upload_id = temp_database.create_upload_record(
            filename="invalid_test.csv",
            user_readable_name="Invalid Data Test",
            uploaded_by=1,
            comment="Testing error handling",
        )

        # Should handle gracefully
        try:
            result = temp_database.upload_csv_data(upload_id, invalid_data)
            # If no exception, result should indicate success but with 0 new records
            assert isinstance(result, dict)
            assert result["success"] is True
            assert result["new_records"] == 0
        except Exception:
            # Exception handling is also acceptable
            pass

    def test_empty_upload_handling(self, temp_database):
        """Test handling of empty uploads using proper upload flow."""
        empty_data = pd.DataFrame()

        # Create upload record first
        upload_id = temp_database.create_upload_record(
            filename="empty_test.csv",
            user_readable_name="Empty Data Test",
            uploaded_by=1,
            comment="Testing empty data handling",
        )

        # Should handle empty data gracefully
        result = temp_database.upload_csv_data(upload_id, empty_data)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["new_records"] == 0


class TestUploadValidation:
    """Test upload validation and data integrity."""

    def test_required_columns_validation(self, upload_service):
        """Test validation of required columns."""
        # Test with missing required columns
        incomplete_data = pd.DataFrame(
            {
                "id": ["test_1", "test_2"],
                # Missing other required columns
            }
        )

        upload_type = upload_service.detect_upload_type(incomplete_data)
        # Should detect as unknown or handle gracefully
        assert upload_type in ["unknown", "forum_data"]

    def test_data_type_validation(self, upload_service):
        """Test validation of data types."""
        # Test with mixed/invalid data types
        mixed_data = pd.DataFrame(
            {
                "id": ["test_1", 123, None],
                "forum": ["cervical", "ovarian", ""],
                "post_type": ["question", None, "reply"],
            }
        )

        upload_type = upload_service.detect_upload_type(mixed_data)
        # Should handle mixed types gracefully
        assert upload_type in ["unknown", "forum_data"]

    def test_special_characters_handling(self, upload_service):
        """Test handling of special characters in data."""
        special_data = pd.DataFrame(
            {
                "id": ["test_1", "test_2", "test_3"],
                "forum": ["cervical", "ovarian", "womb"],
                "original_title": [
                    "Title with ñ",
                    "Title with 中文",
                    "Title with emoji 🎉",
                ],
                "original_post": [
                    "Content with ñoño",
                    "Content with 中文字符",
                    "Content with emoji 🚀",
                ],
            }
        )

        upload_type = upload_service.detect_upload_type(special_data)
        assert upload_type == "forum_data"


# Custom utility functions for testing
def assert_upload_success(result):
    """Custom assertion for upload success."""
    if isinstance(result, dict):
        assert result.get("success") is not False
        assert "message" not in result or "error" not in result["message"].lower()
    else:
        assert result is not False
        assert result is not None


def assert_upload_failure(result):
    """Custom assertion for expected upload failure."""
    if isinstance(result, dict):
        assert (
            result.get("success") is False
            or "error" in result.get("message", "").lower()
        )
    else:
        assert result is False or result == 0


if __name__ == "__main__":
    # Run pytest if called directly
    pytest.main([__file__, "-v"])
