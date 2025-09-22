"""
Pytest fixtures and test utilities for MRPC testing
Provides common setup, teardown, and utility functions
"""

import pytest
import tempfile
import os
import shutil
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

# Import your modules
from utilities.mrpc_database import MRPCDatabase
from utilities.upload_service import UploadService


@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture providing path to test data directory"""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def sample_forum_data(test_data_dir):
    """Fixture providing sample forum CSV data"""
    forum_file = test_data_dir / "forum_sample.csv"
    if forum_file.exists():
        return pd.read_csv(forum_file)
    else:
        # Create minimal sample data if file doesn't exist
        return pd.DataFrame(
            {
                "id": ["test_1", "test_2"],
                "forum": ["cervical", "ovarian"],
                "post_type": ["question", "discussion"],
                "username": ["user1", "user2"],
                "original_title": ["Test post 1", "Test post 2"],
                "original_post": [
                    "This is test post 1 content",
                    "This is test post 2 content",
                ],
                "post_url": ["http://example.com/1", "http://example.com/2"],
                "llm_inferred_question": ["What is test 1?", "What is test 2?"],
                "cluster": [1, 2],
                "cluster_label": ["group_1", "group_2"],
                "llm_cluster_name": ["Test Group 1", "Test Group 2"],
                "date_posted": ["2025-01-01", "2025-01-02"],
                "umap_1": [0.1, 0.2],
                "umap_2": [0.3, 0.4],
                "umap_3": [0.5, 0.6],
            }
        )


@pytest.fixture(scope="session")
def sample_transcription_data(test_data_dir):
    """Fixture providing sample transcription CSV data"""
    trans_file = test_data_dir / "transcription_sample.csv"
    if trans_file.exists():
        return pd.read_csv(trans_file)
    else:
        # Create minimal sample transcription data
        return pd.DataFrame(
            {
                "participant_id": ["P001", "P002"],
                "interview_date": ["2025-01-01", "2025-01-02"],
                "age": [45, 52],
                "diagnosis": ["cervical", "ovarian"],
                "treatment_received": ["surgery", "chemotherapy"],
                "transcript_text": ["Sample transcript 1", "Sample transcript 2"],
            }
        )


@pytest.fixture
def temp_database():
    """Fixture providing a temporary test database"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Create database instance
        db = MRPCDatabase(db_path=db_path)
        yield db
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def temp_database_with_data(temp_database, sample_forum_data):
    """Fixture providing a temporary database with sample data using proper upload service"""
    import base64
    import io
    from utilities.upload_service import UploadService

    # Convert DataFrame to CSV string
    csv_buffer = io.StringIO()
    sample_forum_data.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()

    # Encode as base64 (like a real file upload)
    csv_b64 = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")
    contents = f"data:text/csv;base64,{csv_b64}"

    # Mock the authentication to return user ID 1
    with patch("utilities.upload_service.get_current_user_id", return_value=1):
        # Create a test user first
        import sqlite3

        with sqlite3.connect(temp_database.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO users (id, first_name, last_name, email, password_hash, is_active)
                VALUES (1, 'Test', 'User', 'test@example.com', 'hashed_password', 1)
            """)

        # Use the proper upload service
        upload_service = UploadService()
        upload_service.db = temp_database  # Use our test database

        result = upload_service.process_file_upload(
            contents=contents,
            filename="test_data.csv",
            user_readable_name="Test Upload",
            comment="Test data for testing",
        )

        if not result.get("success"):
            raise Exception(f"Upload failed: {result.get('message')}")

    yield temp_database


@pytest.fixture
def upload_service():
    """Fixture providing UploadService instance"""
    return UploadService()


@pytest.fixture
def mock_dash_app():
    """Fixture providing a mock Dash app for UI testing"""
    from dash import Dash

    app = Dash(__name__, suppress_callback_exceptions=True)
    return app


@pytest.fixture
def temp_upload_dir():
    """Fixture providing temporary upload directory"""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def reset_environment():
    """Automatically reset environment variables after each test"""
    original_env = os.environ.copy()
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Performance testing utilities
@pytest.fixture
def benchmark_database_ops(temp_database_with_data):
    """Fixture for benchmarking database operations"""

    def _benchmark(operation_func, *args, **kwargs):
        import time

        start = time.time()
        result = operation_func(*args, **kwargs)
        end = time.time()
        return result, end - start

    return _benchmark


# Test data generators
def generate_test_posts(count=10, forum="test_forum"):
    """Generate test post data"""
    import random

    posts = []
    for i in range(count):
        posts.append(
            {
                "id": f"test_post_{i}",
                "forum": forum,
                "original_title": f"Test Post {i}",
                "llm_inferred_question": f"What is test question {i}?",
                "cluster": random.randint(1, 5),
                "umap_1": random.uniform(-1, 1),
                "umap_2": random.uniform(-1, 1),
                "umap_3": random.uniform(-1, 1),
            }
        )

    return pd.DataFrame(posts)


def generate_test_tags(item_id="test_item"):
    """Generate test tag data"""
    return {
        "groups": ["Test Group 1", "Test Group 2"],
        "subgroups": ["Test Subgroup A", "Test Subgroup B"],
        "tags": ["tag1", "tag2", "tag3"],
    }


# Assertion helpers
def assert_dataframe_equal(df1, df2, check_dtype=False):
    """Enhanced DataFrame comparison with better error messages"""
    try:
        pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtype)
    except AssertionError as e:
        # Add more context to the error
        print("DataFrames are not equal:")
        print(f"DF1 shape: {df1.shape}, DF2 shape: {df2.shape}")
        print(f"DF1 columns: {list(df1.columns)}")
        print(f"DF2 columns: {list(df2.columns)}")
        raise e


def assert_database_has_table(db, table_name):
    """Assert that database contains specific table"""
    import sqlite3

    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """,
            (table_name,),
        )
        assert cursor.fetchone() is not None, (
            f"Table {table_name} not found in database"
        )


def assert_file_exists_and_readable(file_path):
    """Assert file exists and is readable"""
    assert os.path.exists(file_path), f"File {file_path} does not exist"
    assert os.access(file_path, os.R_OK), f"File {file_path} is not readable"


# Test categories/markers
def requires_database(func):
    """Decorator to mark tests that require database setup"""
    return pytest.mark.requires_db(func)


def slow_test(func):
    """Decorator to mark slow tests"""
    return pytest.mark.slow(func)


def integration_test(func):
    """Decorator to mark integration tests"""
    return pytest.mark.integration(func)


def unit_test(func):
    """Decorator to mark unit tests"""
    return pytest.mark.unit(func)
