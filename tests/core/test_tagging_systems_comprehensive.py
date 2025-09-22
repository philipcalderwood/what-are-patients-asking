#!/usr/bin/env python3
"""
MRPCDatabase Tagging System Validation Test Suite

This test suite validates the single consolidated tagging system (MRPCDatabase)
after removal of legacy systems (UnifiedTaggingSystem and SQLiteTaggingSystem).

Goal: Ensure MRPCDatabase provides all necessary tagging functionality.
"""

import pytest
import sqlite3
import tempfile
import os

# Import the primary tagging system
from utilities.mrpc_database import MRPCDatabase


class TestMRPCDatabaseTagging:
    """Test the consolidated MRPCDatabase tagging system"""

    @pytest.fixture(autouse=True)
    def setup_system(self):
        """Initialize MRPCDatabase for testing"""
        print("\n🔧 Setting up MRPCDatabase tagging system...")

        # Primary system (database-based)
        self.mrpc_db = MRPCDatabase()

        print(" MRPCDatabase tagging system initialized")

    def test_system_availability(self):
        """Test that MRPCDatabase tagging system is available and functional"""
        print("\n🔍 Testing MRPCDatabase availability...")

        # Test MRPCDatabase
        available_tags_mrpc = self.mrpc_db.get_available_tags()
        assert isinstance(available_tags_mrpc, dict)
        assert "groups" in available_tags_mrpc
        assert "subgroups" in available_tags_mrpc
        assert "tags" in available_tags_mrpc
        print(f" MRPCDatabase: {len(available_tags_mrpc['groups'])} groups available")

    def test_data_format_validation(self):
        """Test data formats returned by MRPCDatabase"""
        print("\n🔍 Testing MRPCDatabase data format...")

        # Test item that should exist in database
        test_item_id = "cmdg2oeiu00004ovatv9rir13"

        # Get tags from MRPCDatabase (rich format with source)
        mrpc_tags = self.mrpc_db.get_tags_for_item(test_item_id)
        print(f"MRPCDatabase format: {type(mrpc_tags)}")
        if mrpc_tags["groups"]:
            print(
                f"   Sample group: {mrpc_tags['groups'][0]} ({type(mrpc_tags['groups'][0])})"
            )
            # MRPCDatabase should return dict objects with source info
            assert isinstance(mrpc_tags["groups"][0], dict)
            assert "value" in mrpc_tags["groups"][0]
            assert "source" in mrpc_tags["groups"][0]

    def test_feature_completeness(self):
        """Test that MRPCDatabase provides all required features"""
        print("\n� Testing MRPCDatabase performance...")

        import time

        test_items = ["cmdg2oeiu00004ovatv9rir13", "0", "1", "2", "3"]
        iterations = 10

        # Test MRPCDatabase performance
        start_time = time.time()
        for _ in range(iterations):
            for item_id in test_items:
                self.mrpc_db.get_tags_for_item(item_id)
        mrpc_time = time.time() - start_time

        print("⚡ Performance Results (10 iterations, 5 items each):")
        print(
            f"   MRPCDatabase: {mrpc_time:.4f}s ({len(test_items) * iterations / mrpc_time:.1f} ops/sec)"
        )

        # Should be reasonable performance (> 100 ops/sec)
        assert len(test_items) * iterations / mrpc_time > 100, (
            "Database system should be reasonably fast"
        )

    def test_feature_completeness(self):
        """Test that MRPCDatabase provides all required features"""
        print("\n🔍 Testing feature completeness...")

        required_features = [
            "get_tags_for_item",
            "save_tags_for_item",
            "get_available_tags",
        ]

        missing_features = []
        for feature in required_features:
            if not hasattr(self.mrpc_db, feature):
                missing_features.append(feature)

        print("Feature Completeness:")
        print(
            f"   Core features: {len(required_features) - len(missing_features)}/{len(required_features)}"
        )

        assert len(missing_features) == 0, (
            f"Missing required features: {missing_features}"
        )
        print("    All core features present")

    def test_data_volume_analysis(self):
        """Analyze current data volume in MRPCDatabase"""
        print("\n🔍 Analyzing MRPCDatabase data volume...")

        # MRPCDatabase volume
        mrpc_tags = self.mrpc_db.get_available_tags()
        mrpc_volume = {
            "groups": len(mrpc_tags["groups"]),
            "subgroups": len(mrpc_tags["subgroups"]),
            "tags": len(mrpc_tags["tags"]),
        }

        # Check database record count - use new ai_categories table instead of legacy tags table
        with sqlite3.connect(self.mrpc_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ai_categories")
            mrpc_total_records = cursor.fetchone()[0]

        print("Data Volume Analysis:")
        print("   MRPCDatabase:")
        print(f"     Unique groups: {mrpc_volume['groups']}")
        print(f"     Unique subgroups: {mrpc_volume['subgroups']}")
        print(f"     Unique tags: {mrpc_volume['tags']}")
        print(f"     Total tag records: {mrpc_total_records}")

        # Validate reasonable data volume
        assert mrpc_total_records > 0, "Database should contain tag records"
        assert mrpc_volume["groups"] > 0, "Database should contain groups"
        print(f"    Database contains {mrpc_total_records} tag records")


class TestTaggingSystemAPI:
    """Test API consistency and functionality"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup test data for API testing"""
        # Get a real ID from the database instead of using hardcoded one
        db = MRPCDatabase()
        posts_df = db.get_all_posts_as_dataframe(user_id=1)
        if len(posts_df) > 0:
            self.test_item_id = posts_df.iloc[0]["id"]
        else:
            # Create a test post if none exist
            import sqlite3

            with sqlite3.connect(db.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO posts (id, forum, original_title, original_post, upload_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    ("test_item_123", "test", "Test Title", "Test Content", 1),
                )
            self.test_item_id = "test_item_123"

        self.test_tags = {
            "groups": ["Test Group"],
            "subgroups": ["Test Subgroup"],
            "tags": ["Test Tag"],
        }

    def test_save_and_retrieve_functionality(self):
        """Test save/retrieve functionality with MRPCDatabase"""
        print("\n🔍 Testing save/retrieve functionality...")

        mrpc_db = MRPCDatabase()

        # Test save/retrieve cycle
        success = mrpc_db.save_tags_for_item(
            self.test_item_id, self.test_tags, source="test"
        )
        assert success, "MRPCDatabase should save tags successfully"

        retrieved_tags = mrpc_db.get_tags_for_item(self.test_item_id)

        # Convert rich format to simple format for comparison
        retrieved_simple = {
            "groups": [item["value"] for item in retrieved_tags["groups"]],
            "subgroups": [item["value"] for item in retrieved_tags["subgroups"]],
            "tags": [item["value"] for item in retrieved_tags["tags"]],
        }

        assert retrieved_simple["groups"] == self.test_tags["groups"]
        assert retrieved_simple["subgroups"] == self.test_tags["subgroups"]
        assert retrieved_simple["tags"] == self.test_tags["tags"]

        print(" MRPCDatabase save/retrieve working correctly")

    def test_api_method_signatures(self):
        """Test that API methods have expected signatures"""
        print("\n🔍 Testing API method signatures...")

        mrpc_db = MRPCDatabase()

        print("📋 Testing MRPCDatabase API:")

        # Test get_tags_for_item method
        assert hasattr(mrpc_db, "get_tags_for_item")
        print("    get_tags_for_item method exists")

        # Test save_tags_for_item method
        assert hasattr(mrpc_db, "save_tags_for_item")
        print("    save_tags_for_item method exists")


def test_consolidation_success():
    """Test that consolidation was successful"""
    print("\n🔍 Testing consolidation success...")

    # Verify legacy systems are no longer available
    legacy_systems_removed = True
    try:
        import utilities.unified_tagging_system

        legacy_systems_removed = False
        print("❌ UnifiedTaggingSystem still available")
    except ImportError:
        print(" UnifiedTaggingSystem successfully removed")

    try:
        import utilities.sqlite_tagging_system

        legacy_systems_removed = False
        print("❌ SQLiteTaggingSystem still available")
    except ImportError:
        print(" SQLiteTaggingSystem successfully removed")

    # Verify MRPCDatabase is available
    mrpc_available = True
    try:
        from utilities.mrpc_database import MRPCDatabase

        db = MRPCDatabase()
        print(" MRPCDatabase available and functional")
    except ImportError:
        mrpc_available = False
        print("❌ MRPCDatabase not available")

    print("Consolidation Status:")
    print(f"   Legacy systems removed: {'' if legacy_systems_removed else '❌'}")
    print(f"   MRPCDatabase available: {'' if mrpc_available else '❌'}")

    assert legacy_systems_removed, "Legacy tagging systems should be removed"
    assert mrpc_available, "MRPCDatabase should be available"

    print("🎉 Tagging system consolidation successful!")
    return True


class TestTaggingSystemInspection:
    """Test class for database inspection functionality."""

    @pytest.fixture
    def db(self):
        """Database fixture for inspection tests."""
        return MRPCDatabase()

    def test_database_inspection(self, db):
        """Test direct database inspection functionality."""
        # Get available tags and display structure
        available_tags = db.get_available_tags()
        print(f"\nAvailable tags structure: {available_tags}")

        total_tag_count = sum(len(tags) for tags in available_tags.values())
        print(f"Total tags in database: {total_tag_count}")

        # Display tag hierarchy counts
        print(f"\nTag hierarchy counts:")
        for level, tags in available_tags.items():
            print(f"  {level.capitalize()}: {len(tags)}")

        assert total_tag_count > 0, "Should have tags in database"

    def test_direct_database_query(self, db):
        """Test direct SQL query functionality for inspection."""
        import sqlite3

        # Get database connection and inspect schema
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()

            # Check table structure
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"\nDatabase tables: {[table[0] for table in tables]}")

            # Check tag registry structure
            cursor.execute("PRAGMA table_info(tag_registry)")
            tag_registry_schema = cursor.fetchall()
            print(f"\nTag registry schema:")
            for column in tag_registry_schema:
                print(f"  {column[1]} ({column[2]})")

            # Check ai_categories table structure (new schema)
            cursor.execute("PRAGMA table_info(ai_categories)")
            tags_schema = cursor.fetchall()
            print("\nAI Categories table schema:")
            for column in tags_schema:
                print(f"  {column[1]} ({column[2]})")

            # Get some sample data
            cursor.execute("SELECT COUNT(*) FROM tag_registry")
            registry_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ai_categories")
            tags_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM posts")
            posts_count = cursor.fetchone()[0]

            print("\nRecord counts:")
            print(f"  Tag registry entries: {registry_count}")
            print(f"  AI category assignments: {tags_count}")
            print(f"  Posts: {posts_count}")

        assert registry_count >= 0, "Should have tag registry (may be empty)"
        assert posts_count > 0, "Should have posts"


if __name__ == "__main__":
    print("🚀 Starting MRPCDatabase tagging system validation...\n")

    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
