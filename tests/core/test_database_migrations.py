"""
Comprehensive Database Migration and Schema Test Suite

This test suite provides complete coverage for the MRPC database migration system,
schema versioning, and specific database operations including the inference_feedback table.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

# Import our database class
from utilities.mrpc_database import MRPCDatabase


@pytest.fixture(autouse=True)
def mock_auth_functions():
    """Automatically mock authentication functions for all tests in this module."""
    with (
        patch("utilities.auth.get_current_user_id", return_value=1),
        patch("utilities.auth.require_admin", return_value=None),
        patch(
            "utilities.auth.get_current_user",
            return_value={"id": 1, "email": "test@example.com"},
        ),
    ):
        yield


class TestDatabaseMigrationSystem:
    """Test the database migration system functionality."""

    def test_database_import_basic(self):
        """Test basic import of the database module."""
        # Test that we can import the database module without errors
        from utilities.mrpc_database import MRPCDatabase

        # Test that the class has the expected attributes
        assert hasattr(MRPCDatabase, "CURRENT_SCHEMA_VERSION")
        assert hasattr(MRPCDatabase, "_init_database_with_migrations")
        assert hasattr(MRPCDatabase, "_get_schema_version")
        assert hasattr(MRPCDatabase, "_run_migrations")

        # Test schema version is set correctly
        assert MRPCDatabase.CURRENT_SCHEMA_VERSION >= 2

    def test_new_database_creation_with_latest_schema(self):
        """Test that new databases are created with the latest schema version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_new_db.db"

            # Create new database - should get latest schema
            db = MRPCDatabase(str(db_path))

            # Verify database exists
            assert db_path.exists()

            # Check schema version is set to current version
            current_version = db._get_schema_version()
            assert current_version == MRPCDatabase.CURRENT_SCHEMA_VERSION

            # Verify schema_version table exists and has correct record
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute(
                    "SELECT version FROM schema_version ORDER BY id DESC LIMIT 1"
                )
                result = cursor.fetchone()
                assert result is not None
                assert result[0] == MRPCDatabase.CURRENT_SCHEMA_VERSION

    def test_database_migration_from_v1_to_v2(self):
        """Test migration from schema version 1 to version 2."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_migration_db.db"

            # Create a version 1 database (without schema version tracking)
            with sqlite3.connect(str(db_path)) as conn:
                # Create basic v1 schema (posts and users tables exist)
                conn.execute("""
                    CREATE TABLE posts (
                        id TEXT PRIMARY KEY,
                        forum TEXT NOT NULL,
                        original_title TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL
                    )
                """)

                # Create old inference_feedback table without user_id
                conn.execute("""
                    CREATE TABLE inference_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_id TEXT NOT NULL,
                        inference_type TEXT NOT NULL,
                        rating TEXT NOT NULL,
                        feedback_text TEXT,
                        response_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert test data
                conn.execute(
                    "INSERT INTO posts (id, forum, original_title) VALUES ('test1', 'cervical', 'Test Post')"
                )
                conn.execute(
                    "INSERT INTO users (id, first_name, last_name, email) VALUES (1, 'Test', 'User', 'test@example.com')"
                )
                conn.execute("""
                    INSERT INTO inference_feedback (data_id, inference_type, rating, response_id) 
                    VALUES ('test1', 'llm_question', 'positive', 'resp1')
                """)

            # Now initialize the database with migration system - should trigger migration
            db = MRPCDatabase(str(db_path))

            # Verify migration occurred
            current_version = db._get_schema_version()
            assert current_version == MRPCDatabase.CURRENT_SCHEMA_VERSION

            # Verify inference_feedback table now has user_id column
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute("PRAGMA table_info(inference_feedback)")
                columns = [row[1] for row in cursor.fetchall()]
                assert "user_id" in columns, (
                    "user_id column should be added after migration"
                )

                # Verify existing data still exists and has default user_id
                cursor = conn.execute(
                    "SELECT * FROM inference_feedback WHERE data_id = 'test1'"
                )
                feedback_record = cursor.fetchone()
                assert feedback_record is not None

                # Find user_id column index
                cursor = conn.execute("PRAGMA table_info(inference_feedback)")
                column_info = cursor.fetchall()
                user_id_index = None
                for i, (_, col_name, _, _, _, _) in enumerate(column_info):
                    if col_name == "user_id":
                        user_id_index = i
                        break

                assert user_id_index is not None
                assert (
                    feedback_record[user_id_index] == 1
                )  # Default user_id should be set

    def test_database_schema_version_tracking(self):
        """Test that schema version tracking works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_version_tracking.db"

            # Create database
            db = MRPCDatabase(str(db_path))

            # Test schema version methods
            current_version = db._get_schema_version()
            assert current_version == MRPCDatabase.CURRENT_SCHEMA_VERSION

            # Verify schema_version table structure
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute("PRAGMA table_info(schema_version)")
                columns = [row[1] for row in cursor.fetchall()]
                expected_columns = ["id", "version", "applied_at", "description"]
                for col in expected_columns:
                    assert col in columns, (
                        f"schema_version table should have {col} column"
                    )

    def test_database_already_up_to_date(self):
        """Test that already up-to-date databases don't get migrated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_up_to_date.db"

            # Create database with current schema
            db1 = MRPCDatabase(str(db_path))
            initial_version = db1._get_schema_version()

            # Get initial record count in schema_version table
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM schema_version")
                initial_count = cursor.fetchone()[0]

            # Create second database instance - should not create additional migration records
            db2 = MRPCDatabase(str(db_path))
            final_version = db2._get_schema_version()

            # Version should remain the same
            assert final_version == initial_version
            assert final_version == MRPCDatabase.CURRENT_SCHEMA_VERSION

            # Should not have created additional version records
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM schema_version")
                final_count = cursor.fetchone()[0]
                assert final_count == initial_count


class TestInferenceFeedbackTable:
    """Test the inference_feedback table operations specifically."""

    @pytest.fixture
    def db_with_inference_data(self):
        """Create a database with test inference feedback data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_inference_db.db"
            db = MRPCDatabase(str(db_path))

            # Add test data
            with sqlite3.connect(str(db_path)) as conn:
                # Insert test post (using current schema structure)
                conn.execute("""
                    INSERT INTO posts (id, forum, original_title)
                    VALUES ('post1', 'cervical', 'Test Post')
                """)

                # Get the post_id for the AI questions table
                cursor = conn.execute("SELECT post_id FROM posts WHERE id = 'post1'")
                post_id = cursor.fetchone()[0]

                # Insert AI question separately in ai_questions table
                conn.execute(
                    """
                    INSERT INTO ai_questions (post_id, question_text, confidence_score, model_version)
                    VALUES (?, 'What is this about?', 0.95, 'gpt-4')
                """,
                    (post_id,),
                )

                # Insert test user
                conn.execute("""
                    INSERT INTO users (id, first_name, last_name, email, password_hash)
                    VALUES (1, 'Test', 'User', 'test@example.com', 'hash123')
                """)

            yield db

    def test_inference_feedback_table_exists_with_correct_schema(
        self, db_with_inference_data
    ):
        """Test that inference_feedback table has correct schema."""
        with sqlite3.connect(db_with_inference_data.db_path) as conn:
            # Check table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='inference_feedback'"
            )
            assert cursor.fetchone() is not None, (
                "inference_feedback table should exist"
            )

            # Check table schema
            cursor = conn.execute("PRAGMA table_info(inference_feedback)")
            columns = {
                row[1]: row[2] for row in cursor.fetchall()
            }  # column_name: data_type

            expected_columns = {
                "id": "INTEGER",
                "post_id": "INTEGER",
                "inference_type": "TEXT",
                "rating": "TEXT",
                "feedback_text": "TEXT",
                "response_id": "TEXT",
                "user_id": "INTEGER",
                "created_at": "TIMESTAMP",
                "updated_at": "TIMESTAMP",
            }

            for col_name, expected_type in expected_columns.items():
                assert col_name in columns, f"Column {col_name} should exist"
                if (
                    expected_type != "TEXT"
                ):  # SQLite stores most types as TEXT, so only check specific types
                    assert expected_type.upper() in columns[col_name].upper()

    def test_save_inference_feedback(self, db_with_inference_data):
        """Test saving inference feedback data."""
        # Test saving feedback
        result = db_with_inference_data.save_inference_feedback(
            data_id="post1",
            inference_type="llm_question",
            rating="positive",
            feedback_text="Great question inference",
            response_id="resp123",
            user_id=1,
        )

        assert result is True, "Saving feedback should succeed"

        # Verify data was saved
        with sqlite3.connect(db_with_inference_data.db_path) as conn:
            cursor = conn.execute("""
                SELECT f.post_id, f.inference_type, f.rating, f.feedback_text, f.user_id, p.id
                FROM inference_feedback f
                JOIN posts p ON f.post_id = p.post_id
                WHERE f.response_id = 'resp123'
            """)
            record = cursor.fetchone()
            assert record is not None, "Feedback record should exist"
            assert record[5] == "post1"  # p.id (original data_id)
            assert record[1] == "llm_question"
            assert record[2] == "positive"
            assert record[3] == "Great question inference"
            assert record[4] == 1

    def test_get_inference_feedback(self, db_with_inference_data):
        """Test retrieving inference feedback data."""
        # First save some feedback
        db_with_inference_data.save_inference_feedback(
            data_id="post1",
            inference_type="llm_question",
            rating="negative",
            feedback_text="Poor question inference",
            response_id="resp456",
            user_id=1,
        )

        # Test retrieving feedback
        feedback = db_with_inference_data.get_inference_feedback(
            "post1", "llm_question"
        )

        assert feedback is not None, "Should retrieve saved feedback"
        assert feedback["data_id"] == "post1"
        assert feedback["inference_type"] == "llm_question"
        assert feedback["rating"] == "negative"
        assert feedback["feedback_text"] == "Poor question inference"
        assert feedback["user_id"] == 1

        # Should include user information
        assert "user_display_name" in feedback
        assert feedback["user_display_name"] == "Test User"

    def test_inference_feedback_foreign_key_constraints(self, db_with_inference_data):
        """Test that foreign key constraints work for inference_feedback table."""
        # Test that we can save feedback for existing post and user
        result = db_with_inference_data.save_inference_feedback(
            data_id="post1",  # exists
            inference_type="llm_question",
            rating="positive",
            feedback_text="Test feedback",
            response_id="resp789",
            user_id=1,  # exists
        )
        assert result is True

    def test_inference_feedback_with_user_info(self, db_with_inference_data):
        """Test that inference feedback includes user information when retrieved."""
        # Save feedback
        db_with_inference_data.save_inference_feedback(
            data_id="post1",
            inference_type="llm_question",
            rating="positive",
            feedback_text="Test feedback with user",
            response_id="resp_user_test",
            user_id=1,
        )

        # Retrieve and check user info is included
        feedback = db_with_inference_data.get_inference_feedback(
            "post1", "llm_question"
        )

        assert feedback is not None
        assert "user_first_name" in feedback
        assert "user_last_name" in feedback
        assert "user_email" in feedback
        assert "user_display_name" in feedback

        assert feedback["user_first_name"] == "Test"
        assert feedback["user_last_name"] == "User"
        assert feedback["user_email"] == "test@example.com"
        assert feedback["user_display_name"] == "Test User"


class TestDatabaseTableStructure:
    """Test that all required database tables exist with correct structure."""

    def test_all_required_tables_exist(self):
        """Test that all required tables are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_structure.db"
            db = MRPCDatabase(str(db_path))

            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "ai_categories",
                "ai_questions",
                "inference_feedback",
                "posts",
                "schema_version",
                "tag_registry",
                "tags",
                "transcriptions",
                "uploads",
                "users_categories",
                "users_questions",
                "users",
            ]

            for table in expected_tables:
                assert table in tables, f"Required table '{table}' should exist"

    def test_database_indexes_exist(self):
        """Test that required database indexes are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_indexes.db"
            db = MRPCDatabase(str(db_path))

            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                )
                indexes = [row[0] for row in cursor.fetchall() if row[0] is not None]

            expected_indexes = [
                "idx_posts_cluster",
                "idx_posts_forum",
                "idx_tags_item_id",
                "idx_tags_type",
                "idx_inference_feedback_post_id",
                "idx_users_email",
            ]

            for index in expected_indexes:
                assert index in indexes, f"Required index '{index}' should exist"

    def test_foreign_key_constraints_defined(self):
        """Test that foreign key constraints are properly defined."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_fk.db"
            db = MRPCDatabase(str(db_path))

            with sqlite3.connect(str(db_path)) as conn:
                # Check inference_feedback foreign keys
                cursor = conn.execute("PRAGMA foreign_key_list(inference_feedback)")
                foreign_keys = cursor.fetchall()

                # Should have foreign keys to posts and users tables
                fk_tables = [fk[2] for fk in foreign_keys]  # table referenced
                assert "posts" in fk_tables, (
                    "inference_feedback should reference posts table"
                )
                assert "users" in fk_tables, (
                    "inference_feedback should reference users table"
                )


class TestDatabaseMigrationEdgeCases:
    """Test edge cases and error conditions in database migrations."""

    def test_empty_database_migration(self):
        """Test migration system with completely empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "empty_db.db"

            # Create empty database file
            with sqlite3.connect(str(db_path)) as conn:
                pass  # Just create empty file

            # Initialize with migration system
            db = MRPCDatabase(str(db_path))

            # Should create full schema with current version
            current_version = db._get_schema_version()
            assert current_version == MRPCDatabase.CURRENT_SCHEMA_VERSION

    def test_database_permissions_and_access(self):
        """Test database creation and access with various conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with nested directory creation
            nested_path = Path(temp_dir) / "nested" / "directory" / "test.db"

            # Should create nested directories
            db = MRPCDatabase(str(nested_path))
            assert nested_path.exists()
            assert nested_path.parent.exists()

            # Verify database is functional
            current_version = db._get_schema_version()
            assert current_version == MRPCDatabase.CURRENT_SCHEMA_VERSION
