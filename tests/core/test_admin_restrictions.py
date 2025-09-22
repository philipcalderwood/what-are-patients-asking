"""
Admin Restriction Testing for MRPC Database System

This module tests admin privilege restrictions to ensure:
1. Only User ID 1 (Philip Calderwood) can access admin functions
2. User ID 2+ (regular users) are properly restricted
3. Admin override parameters work correctly
4. Security boundaries are maintained

Created: 2025-01-25
"""

import pytest
import sqlite3
from unittest.mock import patch
import pandas as pd
from utilities.mrpc_database import MRPCDatabase


class TestAdminPrivilegeRestrictions:
    """Test admin privilege restrictions with user_id=2 (non-admin user)"""

    @pytest.fixture
    def mock_regular_user_auth(self):
        """Mock authentication for regular user (user_id=2)"""
        with (
            patch("utilities.auth.get_current_user_id", return_value=2),
            patch(
                "utilities.auth.get_current_user",
                return_value={
                    "id": 2,
                    "first_name": "Mimi",
                    "last_name": "Reyburn",
                    "email": "mimi@example.com",
                },
            ),
        ):
            yield

    @pytest.fixture
    def mock_admin_user_auth(self):
        """Mock authentication for admin user (user_id=1)"""
        with (
            patch("utilities.auth.get_current_user_id", return_value=1),
            patch(
                "utilities.auth.get_current_user",
                return_value={
                    "id": 1,
                    "first_name": "Philip",
                    "last_name": "Calderwood",
                    "email": "philip@example.com",
                },
            ),
        ):
            yield

    @pytest.fixture
    def mock_no_auth(self):
        """Mock no authentication context"""
        with (
            patch("utilities.auth.get_current_user_id", return_value=None),
            patch("utilities.auth.get_current_user", return_value=None),
        ):
            yield

    @pytest.fixture
    def temp_database(self, tmp_path):
        """Create temporary database for testing"""
        db_path = tmp_path / "test_admin.db"

        # Initialize database first (this creates basic tables)
        db = MRPCDatabase(str(db_path))

        # Add test data to existing tables
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            # Clear any existing data
            cursor.execute("DELETE FROM posts")
            cursor.execute("DELETE FROM uploads")
            cursor.execute("DELETE FROM users")

            # Insert test users (with dummy password hashes)
            cursor.execute(
                "INSERT INTO users (id, first_name, last_name, email, password_hash) VALUES (1, 'Philip', 'Calderwood', 'philip@example.com', 'dummy_hash_1')"
            )
            cursor.execute(
                "INSERT INTO users (id, first_name, last_name, email, password_hash) VALUES (2, 'Mimi', 'Reyburn', 'mimi@example.com', 'dummy_hash_2')"
            )
            cursor.execute(
                "INSERT INTO users (id, first_name, last_name, email, password_hash) VALUES (3, 'Timothy', 'Bonnici', 'timothy@example.com', 'dummy_hash_3')"
            )

            # Insert test uploads (different owners)
            cursor.execute(
                "INSERT INTO uploads (id, filename, user_readable_name, uploaded_by, status) VALUES (1, 'admin_data.csv', 'Admin Data Set', 1, 'active')"
            )
            cursor.execute(
                "INSERT INTO uploads (id, filename, user_readable_name, uploaded_by, status) VALUES (2, 'mimi_data.csv', 'Mimi Data Set', 2, 'active')"
            )
            cursor.execute(
                "INSERT INTO uploads (id, filename, user_readable_name, uploaded_by, status) VALUES (3, 'timothy_data.csv', 'Timothy Data Set', 3, 'active')"
            )

            # Insert test posts (linked to different uploads)
            cursor.execute("""
                INSERT INTO posts (id, forum, original_title, cluster, upload_id) 
                VALUES ('1', 'cervical', 'Admin Post 1', 1, 1)
            """)
            cursor.execute("""
                INSERT INTO posts (id, forum, original_title, cluster, upload_id) 
                VALUES ('2', 'ovarian', 'Admin Post 2', 2, 1)
            """)
            cursor.execute("""
                INSERT INTO posts (id, forum, original_title, cluster, upload_id) 
                VALUES ('3', 'cervical', 'Mimi Post 1', 3, 2)
            """)
            cursor.execute("""
                INSERT INTO posts (id, forum, original_title, cluster, upload_id) 
                VALUES ('4', 'ovarian', 'Timothy Post 1', 4, 3)
            """)

            conn.commit()

        return db

    def test_admin_function_access_denied_for_regular_user(
        self, temp_database, mock_regular_user_auth
    ):
        """Test that regular user (user_id=2) cannot access admin functions"""
        db = temp_database

        # Test admin-only function access
        with pytest.raises(Exception) as exc_info:
            db.get_all_posts_as_dataframe_admin()

        assert "Admin privileges required" in str(exc_info.value)
        assert "User Mimi Reyburn (ID: 2) is not authorized" in str(exc_info.value)

    def test_admin_function_access_allowed_for_admin_user(
        self, temp_database, mock_admin_user_auth
    ):
        """Test that admin user (user_id=1) can access admin functions"""
        db = temp_database

        # Should work without exception
        df = db.get_all_posts_as_dataframe_admin()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4  # All posts visible to admin

    def test_include_all_users_parameter_denied_for_regular_user(
        self, temp_database, mock_regular_user_auth
    ):
        """Test that regular user cannot use include_all_users=True parameter"""
        db = temp_database

        with pytest.raises(Exception) as exc_info:
            db.get_all_posts_as_dataframe(include_all_users=True)

        assert "Admin privileges required" in str(exc_info.value)

    def test_include_all_users_parameter_allowed_for_admin(
        self, temp_database, mock_admin_user_auth
    ):
        """Test that admin user can use include_all_users=True parameter"""
        db = temp_database

        # Should work without exception and return all posts
        df = db.get_all_posts_as_dataframe(include_all_users=True)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4  # All posts visible to admin

    def test_regular_user_sees_only_own_data(
        self, temp_database, mock_regular_user_auth
    ):
        """Test that regular user (user_id=2) sees only their own data"""
        db = temp_database

        # Regular function should only return user's own data
        df = db.get_all_posts_as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1  # Only Mimi's post (upload_id=2)
        assert df.iloc[0]["original_title"] == "Mimi Post 1"

    def test_admin_sees_own_data_by_default(self, temp_database, mock_admin_user_auth):
        """Test that admin user sees only their own data without admin override"""
        db = temp_database

        # Admin should see only their own data by default (posts from upload_id=1)
        df = db.get_all_posts_as_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # Only admin's posts (upload_id=1)

    def test_forum_filtering_with_admin_override_denied(
        self, temp_database, mock_regular_user_auth
    ):
        """Test that regular user cannot use admin override in forum filtering"""
        db = temp_database

        with pytest.raises(Exception) as exc_info:
            db.get_posts_by_forum("cervical", include_all_users=True)

        assert "Admin privileges required" in str(exc_info.value)

    def test_forum_filtering_with_admin_override_allowed(
        self, temp_database, mock_admin_user_auth
    ):
        """Test that admin can use admin override in forum filtering"""
        db = temp_database

        # Should return all cervical posts across all users
        df = db.get_posts_by_forum("cervical", include_all_users=True)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # Both cervical posts (admin + mimi)

    def test_cluster_filtering_with_admin_override_denied(
        self, temp_database, mock_regular_user_auth
    ):
        """Test that regular user cannot use admin override in cluster filtering"""
        db = temp_database

        with pytest.raises(Exception) as exc_info:
            db.get_posts_by_cluster(1, include_all_users=True)

        assert "Admin privileges required" in str(exc_info.value)

    def test_cluster_filtering_with_admin_override_allowed(
        self, temp_database, mock_admin_user_auth
    ):
        """Test that admin can use admin override in cluster filtering"""
        db = temp_database

        # Should return all posts in cluster 1
        df = db.get_posts_by_cluster(1, include_all_users=True)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1  # Only admin's post in cluster 1

    def test_no_authentication_returns_empty_datasets(
        self, temp_database, mock_no_auth
    ):
        """Test that functions return empty datasets when no authentication"""
        db = temp_database

        # All functions should return empty DataFrames
        df_all = db.get_all_posts_as_dataframe()
        assert isinstance(df_all, pd.DataFrame)
        assert len(df_all) == 0

        df_forum = db.get_posts_by_forum("cervical")
        assert isinstance(df_forum, pd.DataFrame)
        assert len(df_forum) == 0

        df_cluster = db.get_posts_by_cluster(1)
        assert isinstance(df_cluster, pd.DataFrame)
        assert len(df_cluster) == 0

    def test_no_authentication_admin_functions_fail(self, temp_database, mock_no_auth):
        """Test that admin functions fail without authentication"""
        db = temp_database

        with pytest.raises(Exception) as exc_info:
            db.get_all_posts_as_dataframe_admin()

        assert "Authentication required for admin function" in str(exc_info.value)


class TestAdminUserIdentification:
    """Test proper identification of admin vs regular users"""

    def test_is_admin_function_for_various_user_ids(self):
        """Test is_admin function for different user IDs"""
        from utilities.auth import is_admin

        # Test admin user
        assert is_admin(1), "User ID 1 should be admin"

        # Test regular users
        assert not is_admin(2), "User ID 2 should not be admin"
        assert not is_admin(3), "User ID 3 should not be admin"
        assert not is_admin(999), "User ID 999 should not be admin"
        assert not is_admin(0), "User ID 0 should not be admin"
        assert not is_admin(-1), "Negative user ID should not be admin"

        # Test None user ID
        assert not is_admin(None), "None user ID should not be admin"

    @patch("utilities.auth.get_current_user_id")
    def test_is_admin_with_current_user_context(self, mock_get_user_id):
        """Test is_admin function with current user context"""
        from utilities.auth import is_admin

        # Test with admin user as current user
        mock_get_user_id.return_value = 1
        assert is_admin(), "Current user ID 1 should be admin"

        # Test with regular user as current user
        mock_get_user_id.return_value = 2
        assert not is_admin(), "Current user ID 2 should not be admin"

        # Test with no current user
        mock_get_user_id.return_value = None
        assert not is_admin(), "No current user should not be admin"

    def test_require_admin_with_different_users(self):
        """Test require_admin function behavior with different user contexts"""
        from utilities.auth import require_admin

        # Test with admin user
        with patch(
            "utilities.auth.get_current_user",
            return_value={"id": 1, "first_name": "Philip", "last_name": "Calderwood"},
        ):
            user = require_admin()  # Should not raise exception
            assert user["id"] == 1
            assert user["first_name"] == "Philip"

        # Test with regular user
        with patch(
            "utilities.auth.get_current_user",
            return_value={"id": 2, "first_name": "Mimi", "last_name": "Reyburn"},
        ):
            with pytest.raises(Exception) as exc_info:
                require_admin()
            assert "Admin privileges required" in str(exc_info.value)
            assert "User Mimi Reyburn (ID: 2) is not authorized" in str(exc_info.value)

        # Test with no user
        with patch("utilities.auth.get_current_user", return_value=None):
            with pytest.raises(Exception) as exc_info:
                require_admin()
            assert "Authentication required for admin function" in str(exc_info.value)


class TestTagSaveAdminRestrictions:
    """Test admin restrictions in tag saving functionality"""

    @pytest.fixture
    def temp_database_with_tags(self, tmp_path):
        """Create temporary database with tag tables for testing"""
        db_path = tmp_path / "test_tags_admin.db"

        # Initialize database first (this creates basic tables)
        db = MRPCDatabase(str(db_path))

        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            # Clear any existing data
            cursor.execute("DELETE FROM posts")
            cursor.execute("DELETE FROM uploads")
            cursor.execute("DELETE FROM users")

            # Clear tag tables if they exist
            try:
                cursor.execute("DELETE FROM tags")
                cursor.execute("DELETE FROM tag_registry")
            except sqlite3.OperationalError:
                # Tables may not exist yet, create them
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY,
                        item_id TEXT NOT NULL,
                        item_type TEXT NOT NULL,
                        tag_type TEXT NOT NULL,
                        tag_value TEXT NOT NULL,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users (id)
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tag_registry (
                        id INTEGER PRIMARY KEY,
                        tag_value TEXT UNIQUE NOT NULL,
                        tag_type TEXT NOT NULL,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users (id)
                    )
                """)

            # Insert test data
            cursor.execute(
                "INSERT INTO users (id, first_name, last_name, email, password_hash) VALUES (1, 'Philip', 'Calderwood', 'philip@example.com', 'dummy_hash_1')"
            )
            cursor.execute(
                "INSERT INTO users (id, first_name, last_name, email, password_hash) VALUES (2, 'Mimi', 'Reyburn', 'mimi@example.com', 'dummy_hash_2')"
            )
            cursor.execute(
                "INSERT INTO uploads (id, filename, user_readable_name, uploaded_by, status) VALUES (1, 'test.csv', 'Test Data', 1, 'active')"
            )
            cursor.execute(
                "INSERT INTO uploads (id, filename, user_readable_name, uploaded_by, status) VALUES (2, 'mimi_test.csv', 'Mimi Test Data', 2, 'active')"
            )
            cursor.execute(
                "INSERT INTO posts (id, forum, original_title, upload_id) VALUES ('1', 'cervical', 'Test Post 1', 1)"
            )
            cursor.execute(
                "INSERT INTO posts (id, forum, original_title, upload_id) VALUES ('2', 'ovarian', 'Test Post 2', 2)"
            )

            conn.commit()

        return db

    def test_save_tags_basic_functionality(self, temp_database_with_tags):
        """Test that save_tags_for_item works for basic functionality"""
        db = temp_database_with_tags

        # Test basic tag saving functionality (no privilege restrictions currently implemented)
        with patch("utilities.auth.get_current_user_id", return_value=2):
            result = db.save_tags_for_item(
                "2",
                {
                    "groups": ["Test Group"],
                    "subgroups": ["Test Subgroup"],
                    "tags": ["Test Tag"],
                },
            )
            assert result, "Tag saving should work for authenticated users"

        # Test admin tag saving functionality
        with patch("utilities.auth.get_current_user_id", return_value=1):
            result = db.save_tags_for_item(
                "1",
                {
                    "groups": ["Admin Group"],
                    "subgroups": ["Admin Subgroup"],
                    "tags": ["Admin Tag"],
                },
            )
            assert result, "Tag saving should work for admin users"

    def test_save_tags_admin_can_edit_any_post(self, temp_database_with_tags):
        """Test that admin can save tags for any post"""
        db = temp_database_with_tags

        # Admin should be able to save tags for any post
        with (
            patch("utilities.auth.get_current_user_id", return_value=1),
            patch(
                "utilities.auth.get_current_user",
                return_value={
                    "id": 1,
                    "first_name": "Philip",
                    "last_name": "Calderwood",
                },
            ),
        ):
            # Admin editing their own post
            result1 = db.save_tags_for_item(
                "1",
                {
                    "groups": ["Admin Group"],
                    "subgroups": ["Admin Subgroup"],
                    "tags": ["Admin Tag"],
                },
            )
            assert result1

            # Admin editing another user's post
            result2 = db.save_tags_for_item(
                "2",
                {
                    "groups": ["Admin Override Group"],
                    "subgroups": [],
                    "tags": ["Admin Override Tag"],
                },
            )
            assert result2


class TestSecurityBoundaryValidation:
    """Test that security boundaries are properly maintained"""

    def test_admin_function_names_are_protected(self):
        """Verify that admin function names indicate their restricted nature"""
        db = MRPCDatabase()

        # Check that admin functions have clear naming
        assert hasattr(db, "get_all_posts_as_dataframe_admin"), (
            "Admin function should exist"
        )

        # Check that admin functions are documented as admin-only
        admin_func = getattr(db, "get_all_posts_as_dataframe_admin")
        docstring = admin_func.__doc__ or ""
        assert "admin" in docstring.lower() or "Admin" in docstring, (
            "Admin function should be documented as admin-only"
        )

    def test_regular_functions_have_user_filtering(self):
        """Verify that regular functions implement user-based filtering"""
        from utilities.mrpc_database import MRPCDatabase
        import inspect

        # Check that regular functions accept include_all_users parameter
        regular_func = getattr(MRPCDatabase, "get_all_posts_as_dataframe")
        sig = inspect.signature(regular_func)

        # Should have include_all_users parameter for admin override
        params = list(sig.parameters.keys())
        assert "include_all_users" in params, (
            "Regular function should have admin override parameter"
        )

    def test_consistent_authentication_patterns(self):
        """Test that all admin functions use consistent authentication patterns"""
        from utility import auth

        # Verify core auth functions exist
        assert hasattr(auth, "get_current_user_id"), "Core auth function missing"
        assert hasattr(auth, "get_current_user"), "Core auth function missing"
        assert hasattr(auth, "is_admin"), "Core auth function missing"
        assert hasattr(auth, "require_admin"), "Core auth function missing"

        # Verify auth functions have proper signatures
        import inspect

        require_admin_sig = inspect.signature(auth.require_admin)
        assert len(require_admin_sig.parameters) == 0, (
            "require_admin should take no parameters"
        )

        is_admin_sig = inspect.signature(auth.is_admin)
        params = list(is_admin_sig.parameters.keys())
        assert "user_id" in params, "is_admin should accept user_id parameter"


if __name__ == "__main__":
    # Run tests directly for development
    pytest.main([__file__, "-v", "--tb=short"])
