"""
Enhanced SQLite database system for MRPC forum data
Clean migration from questions_with_clusters.csv with comprehensive tagging support
"""

import sqlite3
import pandas as pd
import json
import hashlib
from typing import Dict, List, Optional
from pathlib import Path


class MRPCDatabase:
    # Current schema version - increment this when making schema changes
    CURRENT_SCHEMA_VERSION = 3

    def __init__(self, db_path: str = "data/mrpc_new.db"):
        """Initialize MRPC SQLite database"""
        self.db_path = db_path

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database with migrations
        self._init_database_with_migrations()

        # print(f" MRPC Database initialized: {db_path}")

    def _init_database_with_migrations(self):
        """Initialize database with proper migration handling"""
        # Check if database exists and get current version

        current_version = self._get_schema_version()

        if current_version == 0:
            # New database - create full schema
            print("🆕 Creating new database with latest schema...")
            self._create_database_schema()
            self._set_schema_version(self.CURRENT_SCHEMA_VERSION)
            print(
                f" Database created with schema version {self.CURRENT_SCHEMA_VERSION}"
            )

        elif current_version < self.CURRENT_SCHEMA_VERSION:
            # Existing database needs migration
            print(
                f"🔄 Migrating database from version {current_version} to {self.CURRENT_SCHEMA_VERSION}..."
            )
            self._run_migrations(current_version)
            print(f" Database migrated to version {self.CURRENT_SCHEMA_VERSION}")

        else:
            # Database is up to date - no message needed for normal operation
            pass

    def _get_schema_version(self) -> int:
        """Get current schema version from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if schema_version table exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='schema_version'
                """)

                if cursor.fetchone():
                    # Check if the table has the correct structure
                    cursor = conn.execute("PRAGMA table_info(schema_version)")
                    columns = [row[1] for row in cursor.fetchall()]

                    if "version" in columns:
                        # Get current version
                        cursor = conn.execute(
                            "SELECT version FROM schema_version ORDER BY id DESC LIMIT 1"
                        )
                        result = cursor.fetchone()
                        return result[0] if result else 0
                    else:
                        # Corrupted schema_version table - treat as v1 if other tables exist
                        print(
                            "⚠️  Corrupted schema_version table detected, checking for existing tables..."
                        )
                        cursor = conn.execute("""
                            SELECT COUNT(*) FROM sqlite_master 
                            WHERE type='table' AND name IN ('posts', 'users')
                        """)
                        table_count = cursor.fetchone()[0]

                        if table_count > 0:
                            # Drop corrupted table and treat as v1
                            conn.execute("DROP TABLE schema_version")
                            return 1
                        else:
                            # No other tables, treat as new database
                            conn.execute("DROP TABLE schema_version")
                            return 0
                else:
                    # No schema_version table - check if other tables exist
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM sqlite_master 
                        WHERE type='table' AND name IN ('posts', 'users')
                    """)
                    table_count = cursor.fetchone()[0]

                    if table_count > 0:
                        # Existing database without version tracking - assume version 1
                        return 1
                    else:
                        # Empty database
                        return 0

        except sqlite3.Error:
            return 0

    def _set_schema_version(self, version: int):
        """Set schema version in database"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if schema_version table exists and has correct structure
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)

            if cursor.fetchone():
                # Table exists - check if it has correct structure
                try:
                    cursor = conn.execute("PRAGMA table_info(schema_version)")
                    columns = [row[1] for row in cursor.fetchall()]

                    if "version" not in columns:
                        # Table exists but is corrupted - drop and recreate
                        print(
                            "  ⚠️ Corrupted schema_version table detected - recreating..."
                        )
                        conn.execute("DROP TABLE schema_version")
                        conn.execute("""
                            CREATE TABLE schema_version (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                version INTEGER NOT NULL,
                                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                description TEXT
                            )
                        """)
                        print(
                            "   Recreated schema_version table with correct structure"
                        )
                except sqlite3.Error:
                    # If there's any error checking the table, recreate it
                    print("  ⚠️ Error accessing schema_version table - recreating...")
                    conn.execute("DROP TABLE schema_version")
                    conn.execute("""
                        CREATE TABLE schema_version (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            version INTEGER NOT NULL,
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            description TEXT
                        )
                    """)
                    print("   Recreated schema_version table")
            else:
                # Table doesn't exist - create it
                conn.execute("""
                    CREATE TABLE schema_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)

            # Insert new version record
            conn.execute(
                """
                INSERT INTO schema_version (version, description)
                VALUES (?, ?)
            """,
                (version, f"Schema version {version}"),
            )

    def _run_migrations(self, from_version: int):
        """Run database migrations from current version to latest"""
        # Migration from version 1 to 2: Add proper inference_feedback table
        if from_version < 2:
            print(
                "📋 Running migration: Add proper inference_feedback table with foreign keys"
            )
            self._migration_v1_to_v2()
            self._set_schema_version(2)

        # Migration from version 2 to 3: Single-row migration with post_id as PK
        if from_version < 3:
            print("📋 Running migration: Single-row migration with post_id as PK")
            print("⚠️  This migration was already completed externally")
            # The migration was run externally, just update the version
            self._set_schema_version(3)

    def _migration_v1_to_v2(self):
        """Migration from v1 to v2: Add proper inference_feedback table"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if inference_feedback table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='inference_feedback'
            """)

            if cursor.fetchone():
                # Table exists - check if it has the user_id column
                cursor = conn.execute("PRAGMA table_info(inference_feedback)")
                columns = [row[1] for row in cursor.fetchall()]

                if "user_id" not in columns:
                    print("  Adding user_id column to inference_feedback table...")
                    # Add user_id column
                    conn.execute(
                        "ALTER TABLE inference_feedback ADD COLUMN user_id INTEGER"
                    )

                    # Set all existing records to user_id = 1 (admin/test user)
                    conn.execute(
                        "UPDATE inference_feedback SET user_id = 1 WHERE user_id IS NULL"
                    )
                    print("   Added user_id column and set default values")
                else:
                    print("   inference_feedback table already has user_id column")
            else:
                # Table doesn't exist - create it with proper schema
                print("  Creating inference_feedback table with proper foreign keys...")
                self._ensure_inference_feedback_table_correct(conn)
                print("   Created inference_feedback table")

    def _init_database(self):
        """Initialize the database with required tables - optimized for existing databases."""
        # Quick existence check - if posts table exists, likely all tables exist
        if self._database_initialized():
            return

        # Full schema creation only for new/incomplete databases
        self._create_database_schema()

    def _database_initialized(self):
        """Fast check if database is already initialized."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='posts'"
                )
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def _create_database_schema(self):
        """Create the full database schema - only called when needed."""
        with sqlite3.connect(self.db_path) as conn:
            # Main forum posts table (new structure with post_id as PK)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT UNIQUE NOT NULL,
                    forum TEXT NOT NULL,
                    post_type TEXT,
                    username TEXT,
                    original_title TEXT,
                    original_post TEXT,
                    post_url TEXT,
                    LLM_inferred_question TEXT,
                    LLM_cluster_name TEXT,
                    cluster INTEGER,
                    cluster_label TEXT,
                    date_posted TIMESTAMP,
                    umap_1 REAL,
                    umap_2 REAL,
                    umap_3 REAL,
                    upload_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # AI Questions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    question_text TEXT,
                    confidence_score REAL,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
                )
            """)

            # AI Categories table (replaces tags table for AI-generated content)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    category_type TEXT NOT NULL,
                    category_value TEXT NOT NULL,
                    confidence_score REAL,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
                )
            """)

            # User Questions table (replaces user_questions)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    question_id TEXT NOT NULL,
                    question_text TEXT,
                    notes_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, question_id),
                    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
                )
            """)

            # User Categories table (replaces category_notes)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    note_id TEXT NOT NULL,
                    notes_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, note_id),
                    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
                )
            """)

            # Legacy tags table (for backward compatibility if needed)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    item_id TEXT NOT NULL,
                    tag_type TEXT NOT NULL,
                    tag_value TEXT NOT NULL,
                    source TEXT DEFAULT 'ai',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (item_id, tag_type, tag_value),
                    FOREIGN KEY (item_id) REFERENCES posts(id)
                )
            """)

            # Tag registry for dropdown options
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tag_registry (
                    tag_type TEXT NOT NULL,
                    tag_value TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tag_type, tag_value)
                )
            """)

            # AI inference feedback table - updated for new schema
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inference_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    inference_type TEXT NOT NULL,
                    rating TEXT,
                    feedback_text TEXT,
                    response_id TEXT NOT NULL,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, inference_type, response_id),
                    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Users table for authentication
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Uploads table for tracking CSV uploads
            conn.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    user_readable_name TEXT NOT NULL,
                    comment TEXT,
                    uploaded_by INTEGER,  -- foreign key to users.id
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    records_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',  -- 'active', 'deleted'
                    upload_type TEXT DEFAULT 'forum_data',  -- 'forum_data' or 'transcription_data'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (uploaded_by) REFERENCES users(id)
                )
            """)

            # Transcriptions table for experimental transcription data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    upload_id INTEGER NOT NULL,
                    
                    -- Basic transcription info
                    session_id TEXT,
                    participant_id TEXT,
                    session_date TIMESTAMP,
                    session_duration INTEGER, -- minutes
                    transcription_text TEXT,
                    
                    -- Digital Access (3 fields)
                    zoom_ease BOOLEAN,                    -- Binary: Whether patient found Zoom easy
                    poll_usability INTEGER,               -- Likert 1-5: Interactive tools usability
                    resource_access BOOLEAN,              -- Binary: Could access materials
                    
                    -- Emotional Response (2 fields)
                    presession_anxiety INTEGER,           -- Likert 1-5: Anxiety before session
                    reassurance_provided INTEGER,         -- Likert 1-5: Feeling reassured/supported
                    
                    -- Information Quality (3 fields)
                    info_useful INTEGER,                  -- Likert 1-5: Information usefulness
                    info_missing BOOLEAN,                 -- Binary: Missing information identified
                    info_takeaway_desired BOOLEAN,        -- Binary: Wanted materials
                    
                    -- Behavioural Outcomes (3 fields)
                    exercise_engaged BOOLEAN,             -- Binary: Started/continued exercise
                    lifestyle_change BOOLEAN,             -- Binary: Made changes (smoking/drinking)
                    postop_adherence BOOLEAN,             -- Binary: Followed post-op instructions
                    
                    -- Support Systems (2 fields)
                    family_involved BOOLEAN,              -- Binary: Family/carers involved
                    support_needed BOOLEAN,               -- Binary: Needed more help
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (upload_id) REFERENCES uploads(id)
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_id ON posts(id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_forum ON posts(forum)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_posts_cluster ON posts(cluster)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_posts_upload_id ON posts(upload_id)"
            )

            # AI content indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_questions_post_id ON ai_questions(post_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_categories_post_id ON ai_categories(post_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_categories_type ON ai_categories(category_type)"
            )

            # User content indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_questions_post_id ON users_questions(post_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_questions_question_id ON users_questions(question_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_categories_post_id ON users_categories(post_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_categories_note_id ON users_categories(note_id)"
            )

            # Legacy tags indexes (for backward compatibility)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags_item_id ON tags(item_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags_type ON tags(tag_type)")

            # Feedback and user indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_inference_feedback_post_id ON inference_feedback(post_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_inference_feedback_type ON inference_feedback(inference_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_inference_feedback_response_id ON inference_feedback(response_id)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

            # Upload indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_uploads_uploaded_by ON uploads(uploaded_by)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_uploads_type ON uploads(upload_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transcriptions_upload_id ON transcriptions(upload_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transcriptions_session ON transcriptions(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transcriptions_participant ON transcriptions(participant_id)"
            )

            # Initialize default users after schema creation
            self.initialize_default_users()

    def migrate_from_csv(self, csv_path: str) -> bool:
        """
        DEPRECATED: Internal migration method - do not use in tests or production

        This method bypasses the proper upload workflow and authentication.
        Use UploadService.process_file_upload() instead for proper testing.
        """
        import warnings

        warnings.warn(
            "migrate_from_csv is deprecated. Use UploadService.process_file_upload() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        try:
            print(f"🔄 Migrating data from {csv_path}...")
            df = pd.read_csv(csv_path)

            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM posts")
                conn.execute("DELETE FROM tags")
                conn.execute("DELETE FROM tag_registry")
                conn.execute("DELETE FROM uploads")
                conn.execute("DELETE FROM users")

                # Create a test user for authentication (user ID 1)
                conn.execute("""
                    INSERT INTO users (id, first_name, last_name, email, password_hash, is_active)
                    VALUES (1, 'Test', 'User', 'test@example.com', 'hashed_password', 1)
                """)

                # Create an upload record for the migrated data
                cursor = conn.execute(
                    """
                    INSERT INTO uploads (filename, user_readable_name, comment, uploaded_by, upload_type, status, records_count)
                    VALUES (?, 'Test Migration', 'Migrated from CSV for testing', 1, 'forum_data', 'active', ?)
                """,
                    (csv_path, len(df)),
                )

                upload_id = cursor.lastrowid

                # Add upload_id to the dataframe
                df["upload_id"] = upload_id

                # Create initial tag mappings based on cluster names BEFORE inserting posts
                self._create_initial_tag_mappings(conn, df)

                # Insert posts data with upload_id
                df.to_sql("posts", conn, if_exists="replace", index=False)

                print(f" Migrated {len(df)} posts to SQLite with upload_id {upload_id}")

            return True

        except Exception as e:
            print(f"❌ Error migrating from CSV: {e}")
            return False

    def _create_initial_tag_mappings(self, conn, df):
        """Create intelligent initial tag mappings from cluster data"""

        # Check if required columns exist
        if "id" not in df.columns:
            print(
                f"Warning: 'id' column not found in dataframe. Columns: {list(df.columns)}"
            )
            return
        if "cluster" not in df.columns:
            print(
                f"Warning: 'cluster' column not found in dataframe. Columns: {list(df.columns)}"
            )
            return

        # Define hierarchical mapping based on cluster analysis
        cluster_mappings = {
            0: {
                "group": "Medical",
                "subgroup": "Surgery Recovery",
                "tag": "Hysterectomy Recovery",
            },
            1: {
                "group": "Medical",
                "subgroup": "Procedures",
                "tag": "Gynecological Procedures",
            },
            2: {
                "group": "Medical",
                "subgroup": "Cancer Concerns",
                "tag": "Ovarian Cancer Concerns",
            },
            3: {
                "group": "Medical",
                "subgroup": "Treatment Side Effects",
                "tag": "Treatment Side Effects",
            },
            4: {
                "group": "Medical",
                "subgroup": "Diagnosis Process",
                "tag": "Diagnostic Testing",
            },
            5: {
                "group": "Medical",
                "subgroup": "Cancer Experience",
                "tag": "Gynecological Cancer Journeys",
            },
            6: {
                "group": "Medical",
                "subgroup": "Surgery Recovery",
                "tag": "Post-Hysterectomy Issues",
            },
            7: {
                "group": "Medical",
                "subgroup": "Treatment Side Effects",
                "tag": "Post-Treatment Bleeding",
            },
            8: {
                "group": "Support",
                "subgroup": "Emotional Support",
                "tag": "Treatment & Coping",
            },
            9: {
                "group": "Medical",
                "subgroup": "Diagnosis Process",
                "tag": "Diagnosis & Consultation",
            },
        }

        # Apply tags to all posts based on their cluster
        for _, row in df.iterrows():
            item_id = row["id"]
            cluster = row["cluster"]

            if cluster in cluster_mappings:
                mapping = cluster_mappings[cluster]

                # Insert tags for this item (marked as AI-generated)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO tags (item_id, tag_type, tag_value, source)
                    VALUES (?, 'group', ?, 'ai')
                """,
                    (item_id, mapping["group"]),
                )

                conn.execute(
                    """
                    INSERT OR REPLACE INTO tags (item_id, tag_type, tag_value, source)
                    VALUES (?, 'subgroup', ?, 'ai')
                """,
                    (item_id, mapping["subgroup"]),
                )

                conn.execute(
                    """
                    INSERT OR REPLACE INTO tags (item_id, tag_type, tag_value, source)
                    VALUES (?, 'tag', ?, 'ai')
                """,
                    (item_id, mapping["tag"]),
                )

        # Update registry counts
        self._update_registry_counts(conn)

        print(" Created initial tag mappings based on cluster analysis")

    def _update_registry_counts(self, conn):
        """Update the tag registry with current usage counts from ai_categories"""
        conn.execute("DELETE FROM tag_registry")
        conn.execute("""
            INSERT INTO tag_registry (tag_type, tag_value, usage_count)
            SELECT category_type as tag_type, category_value as tag_value, COUNT(*) as usage_count
            FROM ai_categories
            WHERE category_type IN ('group', 'subgroup', 'tag')
            GROUP BY category_type, category_value
        """)

    def get_tags_for_item(self, item_id: str) -> Dict[str, List[Dict]]:
        """Get all tags for a specific item with source information from new schema"""
        # Convert item_id (old id) to post_id (new PK)
        post_id = self._get_post_id_from_id(item_id)
        if post_id is None:
            return {"groups": [], "subgroups": [], "tags": []}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT category_type as tag_type, category_value as tag_value, 
                       CASE WHEN model_version LIKE '%user%' THEN 'user' ELSE 'ai' END as source
                FROM ai_categories 
                WHERE post_id = ? AND category_type IN ('group', 'subgroup', 'tag')
                ORDER BY category_type, category_value
            """,
                (post_id,),
            )

            results = cursor.fetchall()

            # Organize by type with source information
            tags_data = {"groups": [], "subgroups": [], "tags": []}
            for tag_type, tag_value, source in results:
                tag_dict = {"value": tag_value, "source": source or "ai"}
                if tag_type == "group":
                    tags_data["groups"].append(tag_dict)
                elif tag_type == "subgroup":
                    tags_data["subgroups"].append(tag_dict)
                elif tag_type == "tag":
                    tags_data["tags"].append(tag_dict)

            return tags_data

    def save_tags_for_item(
        self, item_id: str, tags_data: Dict, source: str = "user"
    ) -> bool:
        """Save tags for an item using new schema (replaces existing tags)"""
        try:
            # Convert item_id (old id) to post_id (new PK)
            post_id = self._get_post_id_from_id(item_id)
            if post_id is None:
                print(f"❌ Could not find post_id for item_id: {item_id}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                # Delete existing AI categories for this post
                conn.execute(
                    "DELETE FROM ai_categories WHERE post_id = ? AND category_type IN ('group', 'subgroup', 'tag')",
                    (post_id,),
                )

                # Insert new tags into ai_categories
                for tag_type, tags in tags_data.items():
                    # Convert plural to singular for database
                    db_type = tag_type.rstrip("s")  # groups -> group, tags -> tag

                    for tag_value in tags:
                        if isinstance(tag_value, dict):
                            # Handle new format with source info
                            value = tag_value.get("value", "").strip()
                            tag_source = tag_value.get("source", source)
                        else:
                            # Handle legacy format (plain strings)
                            value = str(tag_value).strip()
                            tag_source = source

                        if value:  # Only insert non-empty tags
                            # Determine model_version based on source
                            model_version = (
                                "user_migrated" if tag_source == "user" else "legacy_ai"
                            )

                            conn.execute(
                                """
                                INSERT OR REPLACE INTO ai_categories (post_id, category_type, category_value, model_version)
                                VALUES (?, ?, ?, ?)
                            """,
                                (post_id, db_type, value, model_version),
                            )

                # Update registry counts
                self._update_registry_counts(conn)

                print(f" Saved tags for {item_id} (post_id {post_id}): {tags_data}")
                return True

        except Exception as e:
            print(f"❌ Error saving tags for {item_id}: {e}")
            return False

    def get_available_tags(self) -> Dict[str, List[str]]:
        """Get all available tags from AI categories table (new schema)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get unique tag values from ai_categories table
            cursor.execute("""
                SELECT DISTINCT category_type as tag_type, category_value as tag_value
                FROM ai_categories
                WHERE category_type IN ('group', 'subgroup', 'tag')
                ORDER BY category_type, category_value
            """)

            results = cursor.fetchall()

            # Organize by type (simple string format for dropdown compatibility)
            available = {"groups": [], "subgroups": [], "tags": []}

            for tag_type, tag_value in results:
                if tag_type == "group":
                    available["groups"].append(tag_value)
                elif tag_type == "subgroup":
                    available["subgroups"].append(tag_value)
                elif tag_type == "tag":
                    available["tags"].append(tag_value)

            return available

    def get_all_posts_as_dataframe(
        self,
        user_id: int = None,
        status_filter: str = "active",
        include_all_users: bool = False,
        datatable_format: bool = False,
    ) -> pd.DataFrame:
        """
        Get all posts as a pandas DataFrame with user and status filtering

        Args:
            user_id: Filter by specific user (default: current authenticated user)
            status_filter: Filter by upload status (default: 'active')
            include_all_users: Admin override to see all users' data (default: False)
            datatable_format: Return aggregated format for datatable (default: False for compatibility)

        Returns:
            DataFrame filtered by user ownership and upload status
            If datatable_format=True: Returns with aggregated questions and categories
            If datatable_format=False: Returns legacy format for backward compatibility
        """
        from utilities.auth import get_current_user_id

        with sqlite3.connect(self.db_path) as conn:
            if datatable_format:
                # Enhanced query that aggregates all questions and categories per POST TITLE
                # This groups posts with the same title together
                query = """
                    SELECT 
                        MIN(p.id) as id,
                        p.forum, 
                        MIN(p.post_type) as post_type,
                        MIN(p.username) as username,
                        MIN(p.llm_cluster_name) as llm_cluster_name,
                        p.original_title,
                        MIN(p.original_post) as original_post,
                        MIN(p.post_url) as post_url,
                        MIN(p.cluster) as cluster,
                        MIN(p.cluster_label) as cluster_label,
                        MIN(p.date_posted) as date_posted,
                        MIN(p.umap_1) as umap_1, 
                        MIN(p.umap_2) as umap_2, 
                        MIN(p.umap_3) as umap_3,
                        MIN(p.upload_id) as upload_id,
                        
                        -- Aggregate all questions (AI + User) with newline separation
                        (CASE 
                            WHEN GROUP_CONCAT(aq.question_text, char(10)) IS NOT NULL 
                                 AND GROUP_CONCAT(uq.question_text, char(10)) IS NOT NULL THEN
                                GROUP_CONCAT(aq.question_text, char(10)) || char(10) || GROUP_CONCAT(uq.question_text, char(10))
                            WHEN GROUP_CONCAT(aq.question_text, char(10)) IS NOT NULL THEN
                                GROUP_CONCAT(aq.question_text, char(10))
                            WHEN GROUP_CONCAT(uq.question_text, char(10)) IS NOT NULL THEN
                                GROUP_CONCAT(uq.question_text, char(10))
                            ELSE ''
                        END) as all_questions,
                        
                        -- Aggregate all categories (AI categories + User notes) with newline separation  
                        (CASE 
                            WHEN GROUP_CONCAT(ac.category_value, char(10)) IS NOT NULL 
                                 AND GROUP_CONCAT(uc.notes_text, char(10)) IS NOT NULL THEN
                                GROUP_CONCAT(ac.category_value, char(10)) || char(10) || GROUP_CONCAT(uc.notes_text, char(10))
                            WHEN GROUP_CONCAT(ac.category_value, char(10)) IS NOT NULL THEN
                                GROUP_CONCAT(ac.category_value, char(10))
                            WHEN GROUP_CONCAT(uc.notes_text, char(10)) IS NOT NULL THEN
                                GROUP_CONCAT(uc.notes_text, char(10))
                            ELSE ''
                        END) as all_categories
                        
                    FROM posts p
                    INNER JOIN uploads u ON p.upload_id = u.id
                    LEFT JOIN ai_questions aq ON p.post_id = aq.post_id
                    LEFT JOIN ai_categories ac ON p.post_id = ac.post_id
                    LEFT JOIN users_questions uq ON p.post_id = uq.post_id
                    LEFT JOIN users_categories uc ON p.post_id = uc.post_id
                    WHERE u.status = ?
                """
            else:
                # Legacy query for backward compatibility
                query = """
                    SELECT p.id, p.forum, p.post_type, p.username, p.original_title, p.original_post, 
                           p.post_url, 
                           COALESCE(aq.question_text, '') as LLM_inferred_question,
                           p.cluster, p.cluster_label, 
                           COALESCE(p.llm_cluster_name, '') as llm_cluster_name,
                           p.date_posted, p.umap_1, p.umap_2, p.umap_3, p.upload_id
                    FROM posts p
                    INNER JOIN uploads u ON p.upload_id = u.id
                    LEFT JOIN ai_questions aq ON p.post_id = aq.post_id
                    WHERE u.status = ?
                """
            params = [status_filter]

            # Apply user filtering unless admin override is enabled
            if not include_all_users:
                # Use provided user_id or get current authenticated user
                filter_user_id = (
                    user_id if user_id is not None else get_current_user_id()
                )

                if filter_user_id is not None:
                    query += " AND u.uploaded_by = ?"
                    params.append(
                        str(filter_user_id)
                    )  # Convert to string for consistency
                else:
                    # No authenticated user and no admin override - return empty DataFrame
                    return pd.DataFrame()
            else:
                # Admin override requested - verify admin privileges
                from utilities.auth import require_admin

                require_admin()  # Raises exception if not admin (User ID 1)

            # Add appropriate ending based on query type
            if datatable_format:
                query += " GROUP BY p.original_title ORDER BY MIN(p.date_posted) DESC"
            else:
                query += " ORDER BY p.date_posted DESC"

            df = pd.read_sql_query(query, conn, params=params)

            # Post-process datatable format to remove duplicates in aggregated fields
            if datatable_format and len(df) > 0:

                def deduplicate_lines(text):
                    """Remove duplicate lines while preserving order"""
                    if not text or pd.isna(text):
                        return ""
                    lines = text.split("\n")
                    seen = set()
                    unique_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and line not in seen:
                            seen.add(line)
                            unique_lines.append(line)
                    return "\n".join(unique_lines)

                # Deduplicate questions and categories
                df["all_questions"] = df["all_questions"].apply(deduplicate_lines)
                df["all_categories"] = df["all_categories"].apply(deduplicate_lines)

            return df

    def get_all_posts_as_dataframe_admin(self) -> pd.DataFrame:
        """
        Admin function to get ALL posts with aggregated questions and categories
        ⚠️ This bypasses security filters - ONLY for Philip Calderwood (User ID 1)
        """
        from utilities.auth import require_admin

        # Check admin privileges - raises exception if not admin
        require_admin()

        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT 
                    p.id,
                    p.forum, 
                    p.post_type,
                    p.username,
                    p.original_title,
                    p.original_post,
                    p.post_url,
                    p.cluster,
                    p.cluster_label,
                    p.date_posted,
                    p.umap_1, 
                    p.umap_2, 
                    p.umap_3,
                    p.upload_id,
                    
                    -- Aggregate all questions (AI + User) with newline separation
                    CASE 
                        WHEN LENGTH(
                            COALESCE(
                                GROUP_CONCAT(DISTINCT aq.question_text, char(10)) || 
                                CASE WHEN GROUP_CONCAT(DISTINCT aq.question_text, char(10)) IS NOT NULL 
                                     AND GROUP_CONCAT(DISTINCT uq.question_text, char(10)) IS NOT NULL 
                                     THEN char(10) ELSE '' END ||
                                COALESCE(GROUP_CONCAT(DISTINCT uq.question_text, char(10)), ''), 
                                ''
                            )
                        ) > 0 
                        THEN COALESCE(
                            GROUP_CONCAT(DISTINCT aq.question_text, char(10)) || 
                            CASE WHEN GROUP_CONCAT(DISTINCT aq.question_text, char(10)) IS NOT NULL 
                                 AND GROUP_CONCAT(DISTINCT uq.question_text, char(10)) IS NOT NULL 
                                 THEN char(10) ELSE '' END ||
                            COALESCE(GROUP_CONCAT(DISTINCT uq.question_text, char(10)), ''), 
                            ''
                        )
                        ELSE ''
                    END as all_questions,
                    
                    -- Aggregate all categories (AI categories + User notes) with newline separation
                    CASE 
                        WHEN LENGTH(
                            COALESCE(
                                GROUP_CONCAT(DISTINCT ac.category_value, char(10)) || 
                                CASE WHEN GROUP_CONCAT(DISTINCT ac.category_value, char(10)) IS NOT NULL 
                                     AND GROUP_CONCAT(DISTINCT uc.notes_text, char(10)) IS NOT NULL 
                                     THEN char(10) ELSE '' END ||
                                COALESCE(GROUP_CONCAT(DISTINCT uc.notes_text, char(10)), ''), 
                                ''
                            )
                        ) > 0 
                        THEN COALESCE(
                            GROUP_CONCAT(DISTINCT ac.category_value, char(10)) || 
                            CASE WHEN GROUP_CONCAT(DISTINCT ac.category_value, char(10)) IS NOT NULL 
                                 AND GROUP_CONCAT(DISTINCT uc.notes_text, char(10)) IS NOT NULL 
                                 THEN char(10) ELSE '' END ||
                            COALESCE(GROUP_CONCAT(DISTINCT uc.notes_text, char(10)), ''), 
                            ''
                        )
                        ELSE ''
                    END as all_categories
                    
                FROM posts p
                LEFT JOIN ai_questions aq ON p.post_id = aq.post_id
                LEFT JOIN ai_categories ac ON p.post_id = ac.post_id
                LEFT JOIN users_questions uq ON p.post_id = uq.post_id
                LEFT JOIN users_categories uc ON p.post_id = uc.post_id
                GROUP BY p.post_id
                ORDER BY p.date_posted DESC
            """
            df = pd.read_sql_query(query, conn)
            return df

    def get_posts_by_cluster(
        self,
        cluster_id: int,
        user_id: int = None,
        status_filter: str = "active",
        include_all_users: bool = False,
    ) -> pd.DataFrame:
        """
        Get posts filtered by cluster with user and status filtering

        Args:
            cluster_id: Cluster ID to filter by
            user_id: Filter by specific user (default: current authenticated user)
            status_filter: Filter by upload status (default: 'active')
            include_all_users: Admin override to see all users' data (default: False)
        """
        from utilities.auth import get_current_user_id

        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT p.* FROM posts p
                INNER JOIN uploads u ON p.upload_id = u.id
                WHERE p.cluster = ? AND u.status = ?
            """
            params = [cluster_id, status_filter]

            # Apply user filtering unless admin override is enabled
            if not include_all_users:
                # Use provided user_id or get current authenticated user
                filter_user_id = (
                    user_id if user_id is not None else get_current_user_id()
                )

                if filter_user_id is not None:
                    query += " AND u.uploaded_by = ?"
                    params.append(
                        str(filter_user_id)
                    )  # Convert to string for consistency
                else:
                    # No authenticated user and no admin override - return empty DataFrame
                    return pd.DataFrame()
            else:
                # Admin override requested - verify admin privileges
                from utilities.auth import require_admin

                require_admin()  # Raises exception if not admin (User ID 1)

            query += " ORDER BY p.date_posted DESC"

            df = pd.read_sql_query(query, conn, params=params)
            return df

    def get_posts_by_forum(
        self,
        forum_name: str,
        user_id: int = None,
        status_filter: str = "active",
        include_all_users: bool = False,
    ) -> pd.DataFrame:
        """
        Get posts filtered by forum with user and status filtering

        Args:
            forum_name: Name of the forum to filter by
            user_id: Filter by specific user (default: current authenticated user)
            status_filter: Filter by upload status (default: 'active')
            include_all_users: Admin override to see all users' data (default: False)
        """
        from utilities.auth import get_current_user_id

        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT p.* FROM posts p
                INNER JOIN uploads u ON p.upload_id = u.id
                WHERE p.forum = ? AND u.status = ?
            """
            params = [forum_name, status_filter]

            # Apply user filtering unless admin override is enabled
            if not include_all_users:
                # Use provided user_id or get current authenticated user
                filter_user_id = (
                    user_id if user_id is not None else get_current_user_id()
                )

                if filter_user_id is not None:
                    query += " AND u.uploaded_by = ?"
                    params.append(
                        str(filter_user_id)
                    )  # Convert to string for consistency
                else:
                    # No authenticated user and no admin override - return empty DataFrame
                    return pd.DataFrame()
            else:
                # Admin override requested - verify admin privileges
                from utilities.auth import require_admin

                require_admin()  # Raises exception if not admin (User ID 1)

            query += " ORDER BY p.date_posted DESC"

            df = pd.read_sql_query(query, conn, params=params)
            return df

    def get_posts_by_tag(self, tag_type: str, tag_value: str) -> List[str]:
        """Get post IDs that have a specific tag

        Args:
            tag_type: One of 'groups', 'subgroups', 'tags'
            tag_value: The specific tag value to search for

        Returns:
            List of post IDs that have this tag
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Map plural forms to database column names
            tag_type_mapping = {
                "groups": "group",
                "subgroups": "subgroup",
                "tags": "tag",
            }

            db_tag_type = tag_type_mapping.get(tag_type, tag_type)

            query = """
                SELECT DISTINCT p.id
                FROM ai_categories ac
                JOIN posts p ON ac.post_id = p.post_id
                WHERE ac.category_type = ? AND ac.category_value = ?
            """
            cursor.execute(query, (db_tag_type, tag_value))
            results = cursor.fetchall()

            return [row[0] for row in results]

    def append_csv_data(self, csv_path: str) -> bool:
        """Append new data from CSV upload to existing database"""
        try:
            print(f"📥 Appending data from {csv_path}...")
            new_df = pd.read_csv(csv_path)

            with sqlite3.connect(self.db_path) as conn:
                # Get existing IDs to avoid duplicates
                existing_ids = pd.read_sql_query("SELECT id FROM posts", conn)[
                    "id"
                ].tolist()

                # Filter out duplicates
                new_df = new_df[~new_df["id"].isin(existing_ids)]

                if len(new_df) == 0:
                    print("⚠️ No new records to append (all IDs already exist)")
                    return True

                # Append new data
                new_df.to_sql("posts", conn, if_exists="append", index=False)

                # Create tag mappings for new posts if they have cluster info
                if "cluster" in new_df.columns:
                    self._create_initial_tag_mappings(conn, new_df)

                print(f" Appended {len(new_df)} new posts to database")

            return True

        except Exception as e:
            print(f"❌ Error appending CSV data: {e}")
            return False

    def get_post_by_id(self, item_id: str) -> Optional[Dict]:
        """Get a specific post by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE id = ?", (item_id,))
            result = cursor.fetchone()

            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            return None

    def get_posts_summary(self) -> Dict:
        """Get summary statistics about posts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total posts
            cursor.execute("SELECT COUNT(*) FROM posts")
            total_posts = cursor.fetchone()[0]

            # Posts by forum
            cursor.execute("SELECT forum, COUNT(*) FROM posts GROUP BY forum")
            by_forum = dict(cursor.fetchall())

            # Posts by cluster label (using the correct column name)
            cursor.execute(
                "SELECT cluster_label, COUNT(*) FROM posts WHERE cluster_label IS NOT NULL GROUP BY cluster_label"
            )
            by_cluster = dict(cursor.fetchall())

            return {
                "total_posts": total_posts,
                "by_forum": by_forum,
                "by_cluster": by_cluster,
            }

    def save_user_question(
        self,
        item_id: str,
        question_id: str,
        question_text: str = "",
        notes_text: str = "",
    ) -> bool:
        """Save or update a user inferred question with notes"""
        try:
            # Convert item_id (old id) to post_id (new PK)
            post_id = self._get_post_id_from_id(item_id)
            if post_id is None:
                print(f"❌ Could not find post_id for item_id: {item_id}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO users_questions 
                    (post_id, question_id, question_text, notes_text, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (post_id, question_id, question_text, notes_text),
                )

            print(
                f" Saved user question {question_id} for item {item_id} (post_id {post_id})"
            )
            return True

        except Exception as e:
            print(f"❌ Error saving user question: {e}")
            return False

    def get_user_questions(self, item_id: str) -> List[Dict]:
        """Get all user questions for a specific item by URL (same behavior as get_ai_questions)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # First get the URL for this post
                cursor.execute(
                    "SELECT post_url FROM posts WHERE id = ?",
                    (item_id,),
                )
                url_result = cursor.fetchone()
                if not url_result or not url_result[0]:
                    return []

                post_url = url_result[0]

                # Now get ALL user questions from users_questions table for ALL posts with this URL
                cursor.execute(
                    """
                    SELECT uq.question_id, uq.question_text, uq.notes_text, uq.created_at, uq.updated_at
                    FROM users_questions uq
                    JOIN posts p ON uq.post_id = p.post_id
                    WHERE p.post_url = ?
                    ORDER BY uq.created_at ASC
                """,
                    (post_url,),
                )

                results = cursor.fetchall()
                columns = [
                    "question_id",
                    "question_text",
                    "notes_text",
                    "created_at",
                    "updated_at",
                ]

                return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            print(f"❌ Error getting user questions: {e}")
            return []

    def delete_user_question(self, item_id: str, question_id: str) -> bool:
        """Delete a specific user question"""
        try:
            # Convert item_id (old id) to post_id (new PK)
            post_id = self._get_post_id_from_id(item_id)
            if post_id is None:
                print(f"❌ Could not find post_id for item_id: {item_id}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM users_questions 
                    WHERE post_id = ? AND question_id = ?
                """,
                    (post_id, question_id),
                )

                if cursor.rowcount > 0:
                    print(
                        f" Deleted user question {question_id} for item {item_id} (post_id {post_id})"
                    )
                    return True
                else:
                    print(
                        f"⚠️ No user question found with question_id {question_id} for item {item_id}"
                    )
                    return False

        except Exception as e:
            print(f"❌ Error deleting user question: {e}")
            return False

    def get_ai_questions(self, id: str) -> List[Dict]:
        """Get all AI questions for a specific item"""
        try:
            # # Convert item_id (old id) to post_id (new PK)
            # post_id = self._get_post_id_from_id(item_id)
            # if post_id is None:
            #     return []

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # First get the URL for this post
                cursor.execute(
                    "SELECT post_url FROM posts WHERE id = ?",
                    (id,),
                )
                url_result = cursor.fetchone()
                if not url_result or not url_result[0]:
                    return []

                post_url = url_result[0]

                # Now get the LLM_inferred_question from posts table using the URL
                cursor.execute(
                    """
                    SELECT id as id, LLM_inferred_question as question_text, 
                           NULL as confidence_score, 'Gemini' as model_version, 
                           'A long time ago' as created_at, NULL as updated_at
                    FROM posts 
                    WHERE post_url = ?
                    ORDER BY created_at ASC
                """,
                    (post_url,),
                )

                results = cursor.fetchall()
                columns = [
                    "id",
                    "question_text",
                    "confidence_score",
                    "model_version",
                    "created_at",
                    "updated_at",
                ]

                return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            print(f"❌ Error getting AI questions: {e}")
            return []

    def get_ai_categories(self, item_id: str) -> List[Dict]:
        """Get all AI categories for a specific item by URL (same behavior as get_ai_questions)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # First get the URL for this post
                cursor.execute(
                    "SELECT post_url FROM posts WHERE id = ?",
                    (item_id,),
                )
                url_result = cursor.fetchone()
                if not url_result or not url_result[0]:
                    return []

                post_url = url_result[0]

                # Now get ALL categories from ai_categories table for ALL posts with this URL
                cursor.execute(
                    """
                    SELECT ac.id, ac.category_type, ac.category_value, ac.confidence_score, 
                           ac.model_version, ac.created_at, ac.updated_at
                    FROM ai_categories ac
                    JOIN posts p ON ac.post_id = p.post_id
                    WHERE p.post_url = ?
                    ORDER BY ac.created_at ASC
                """,
                    (post_url,),
                )

                results = cursor.fetchall()
                columns = [
                    "id",
                    "category_type",
                    "category_value",
                    "confidence_score",
                    "model_version",
                    "created_at",
                    "updated_at",
                ]

                return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            print(f"❌ Error getting AI categories: {e}")
            return []
            print(f"❌ Error getting AI categories: {e}")
            return []

    def save_category_note(
        self, item_id: str, note_id: str, notes_text: str = ""
    ) -> bool:
        """Save or update a category note"""
        try:
            # Convert item_id (old id) to post_id (new PK)
            post_id = self._get_post_id_from_id(item_id)
            if post_id is None:
                print(f"❌ Could not find post_id for item_id: {item_id}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO users_categories 
                    (post_id, note_id, notes_text, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (post_id, note_id, notes_text),
                )

            print(
                f" Saved category note {note_id} for item {item_id} (post_id {post_id})"
            )
            return True

        except Exception as e:
            print(f"❌ Error saving category note: {e}")
            return False

    def get_category_notes(self, item_id: str) -> List[Dict]:
        """Get all category notes for a specific item by URL (same behavior as get_ai_categories)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # First get the URL for this post
                cursor.execute(
                    "SELECT post_url FROM posts WHERE id = ?",
                    (item_id,),
                )
                url_result = cursor.fetchone()
                if not url_result or not url_result[0]:
                    return []

                post_url = url_result[0]

                # Now get ALL user category notes from users_categories table for ALL posts with this URL
                cursor.execute(
                    """
                    SELECT uc.note_id, uc.notes_text, uc.created_at, uc.updated_at
                    FROM users_categories uc
                    JOIN posts p ON uc.post_id = p.post_id
                    WHERE p.post_url = ?
                    ORDER BY uc.created_at ASC
                """,
                    (post_url,),
                )

                results = cursor.fetchall()
                columns = ["note_id", "notes_text", "created_at", "updated_at"]

                return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            print(f"❌ Error getting category notes: {e}")
            return []

    def delete_category_note(self, item_id: str, note_id: str) -> bool:
        """Delete a specific category note"""
        try:
            # Convert item_id (old id) to post_id (new PK)
            post_id = self._get_post_id_from_id(item_id)
            if post_id is None:
                print(f"❌ Could not find post_id for item_id: {item_id}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM users_categories 
                    WHERE post_id = ? AND note_id = ?
                """,
                    (post_id, note_id),
                )

                if cursor.rowcount > 0:
                    print(
                        f" Deleted category note {note_id} for item {item_id} (post_id {post_id})"
                    )
                    return True
                else:
                    print(
                        f"⚠️ No category note found with note_id {note_id} for item {item_id}"
                    )
                    return False

        except Exception as e:
            print(f"❌ Error deleting category note: {e}")
            return False

    def _get_post_id_from_id(self, data_id: str) -> Optional[int]:
        """Helper method to get post_id from the original id field"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT post_id FROM posts WHERE id = ?", (data_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None

    def save_inference_feedback(
        self,
        data_id: str,
        inference_type: str,
        rating: str,
        feedback_text: str,
        response_id: str,
        user_id: int = None,
    ) -> bool:
        """Save or update inference feedback with user information"""
        try:
            # Get current user_id if not provided
            if user_id is None:
                from utilities.auth import get_current_user_id

                user_id = get_current_user_id()

            # Convert data_id (old id) to post_id (new PK)
            post_id = self._get_post_id_from_id(data_id)
            if post_id is None:
                print(f"❌ Could not find post_id for data_id: {data_id}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if a record already exists
                cursor.execute(
                    """
                    SELECT rating, feedback_text FROM inference_feedback 
                    WHERE post_id = ? AND inference_type = ? AND response_id = ?
                    """,
                    (post_id, inference_type, response_id),
                )
                existing_record = cursor.fetchone()

                if existing_record:
                    # Update existing record, preserving rating if only adding text
                    existing_rating, existing_text = existing_record

                    # Determine final rating and text to preserve existing data
                    if rating == "text_update" and existing_rating in [
                        "positive",
                        "negative",
                    ]:
                        # Text-only update: preserve existing rating
                        final_rating = existing_rating
                        final_text = feedback_text  # Use new text
                    elif rating in ["positive", "negative"] and existing_text:
                        # Rating update with existing comment: preserve existing text
                        final_rating = rating  # Use new rating
                        final_text = existing_text  # Preserve existing comment
                    else:
                        # New rating without existing comment, or text update without existing rating
                        final_rating = rating
                        final_text = feedback_text

                    cursor.execute(
                        """
                        UPDATE inference_feedback 
                        SET rating = ?, feedback_text = ?, user_id = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE post_id = ? AND inference_type = ? AND response_id = ?
                        """,
                        (
                            final_rating,
                            final_text,
                            user_id,
                            post_id,
                            inference_type,
                            response_id,
                        ),
                    )
                else:
                    # Insert new record
                    cursor.execute(
                        """
                        INSERT INTO inference_feedback 
                        (post_id, inference_type, rating, feedback_text, response_id, user_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            post_id,
                            inference_type,
                            rating,
                            feedback_text,
                            response_id,
                            user_id,
                        ),
                    )

                print(
                    f" Saved inference feedback: {rating} for {inference_type} on data_id {data_id} (post_id {post_id}) by user_id {user_id}"
                )
                return True

        except Exception as e:
            print(f"❌ Error saving inference feedback: {e}")
            return False

    def get_inference_feedback(
        self, data_id: str, inference_type: str
    ) -> Optional[Dict]:
        """Get existing inference feedback for a specific data point and inference type with user info"""
        try:
            # Convert data_id (old id) to post_id (new PK)
            post_id = self._get_post_id_from_id(data_id)
            if post_id is None:
                return None

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT p.id, f.inference_type, f.rating, f.feedback_text, f.response_id, 
                           f.created_at, f.updated_at, f.user_id,
                           u.first_name, u.last_name, u.email
                    FROM inference_feedback f
                    LEFT JOIN users u ON f.user_id = u.id
                    LEFT JOIN posts p ON f.post_id = p.post_id
                    WHERE f.post_id = ? AND f.inference_type = ?
                    ORDER BY f.updated_at DESC
                    LIMIT 1
                """,
                    (post_id, inference_type),
                )

                result = cursor.fetchone()

                if result:
                    columns = [
                        "data_id",
                        "inference_type",
                        "rating",
                        "feedback_text",
                        "response_id",
                        "created_at",
                        "updated_at",
                        "user_id",
                        "user_first_name",
                        "user_last_name",
                        "user_email",
                    ]
                    feedback = dict(zip(columns, result))

                    # Add formatted time for display
                    if feedback["updated_at"]:
                        try:
                            from datetime import datetime

                            dt = datetime.fromisoformat(feedback["updated_at"])
                            feedback["formatted_time"] = dt.strftime(
                                "%B %d, %Y at %H:%M"
                            )
                        except Exception:
                            feedback["formatted_time"] = feedback["updated_at"]

                    # Add user display name
                    if feedback["user_first_name"] and feedback["user_last_name"]:
                        feedback["user_display_name"] = (
                            f"{feedback['user_first_name']} {feedback['user_last_name']}"
                        )
                    elif feedback["user_email"]:
                        feedback["user_display_name"] = feedback["user_email"]
                    else:
                        feedback["user_display_name"] = "Unknown User"

                    return feedback
                else:
                    return None

        except Exception as e:
            print(f"❌ Error getting inference feedback: {e}")
            return None

    def get_all_inference_feedback(self, data_id: str) -> List[Dict]:
        """Get all inference feedback for a specific data point"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT data_id, inference_type, rating, feedback_text, response_id,
                           created_at, updated_at
                    FROM inference_feedback 
                    WHERE data_id = ?
                    ORDER BY inference_type, updated_at DESC
                """,
                    (data_id,),
                )

                results = cursor.fetchall()
                columns = [
                    "data_id",
                    "inference_type",
                    "rating",
                    "feedback_text",
                    "response_id",
                    "created_at",
                    "updated_at",
                ]

                return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            print(f"❌ Error getting all inference feedback: {e}")
            return []

    def delete_inference_feedback(
        self, data_id: str, inference_type: str, response_id: str
    ) -> bool:
        """Delete specific inference feedback"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM inference_feedback 
                    WHERE data_id = ? AND inference_type = ? AND response_id = ?
                """,
                    (data_id, inference_type, response_id),
                )

                if cursor.rowcount > 0:
                    print(
                        f" Deleted inference feedback for {inference_type} on data_id {data_id}"
                    )
                    return True
                else:
                    print(
                        f"⚠️ No inference feedback found for {inference_type} on data_id {data_id}"
                    )
                    return False

        except Exception as e:
            print(f"❌ Error deleting inference feedback: {e}")
            return False

    # User Authentication Methods

    def create_user(
        self, first_name: str, last_name: str, email: str, password: str
    ) -> bool:
        """Create a new user with hashed password"""
        try:
            # Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (first_name, last_name, email, password_hash)
                    VALUES (?, ?, ?, ?)
                    """,
                    (first_name, last_name, email, password_hash),
                )

                print(f" Created user: {first_name} {last_name} ({email})")
                return True

        except sqlite3.IntegrityError:
            print(f"❌ User with email {email} already exists")
            return False
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return False

    def verify_user(self, email: str, password: str) -> Optional[Dict]:
        """Verify user credentials and return user info if valid"""
        try:
            # Hash the provided password
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, first_name, last_name, email, is_active
                    FROM users 
                    WHERE email = ? AND password_hash = ? AND is_active = 1
                    """,
                    (email, password_hash),
                )

                user = cursor.fetchone()
                if user:
                    return {
                        "id": user[0],
                        "first_name": user[1],
                        "last_name": user[2],
                        "email": user[3],
                        "is_active": user[4],
                    }
                else:
                    return None

        except Exception as e:
            print(f"❌ Error verifying user: {e}")
            return None

    def get_all_users(self) -> List[Dict]:
        """Get all users (without password hashes)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, first_name, last_name, email, is_active, created_at
                    FROM users 
                    ORDER BY last_name, first_name
                    """
                )

                users = []
                for row in cursor.fetchall():
                    users.append(
                        {
                            "id": row[0],
                            "first_name": row[1],
                            "last_name": row[2],
                            "email": row[3],
                            "is_active": row[4],
                            "created_at": row[5],
                        }
                    )

                return users

        except Exception as e:
            print(f"❌ Error getting users: {e}")
            return []

    def initialize_default_users(self) -> bool:
        """Initialize the system with default users"""
        default_users = [
            ("Timothy", "Bonnici", "t.bonnici@nhs.net", "cdedemo1"),
            ("Mimi", "Reyburn", "mimi.reyburn@nhs.net", "temppass123"),
            ("Philip", "Calderwood", "philip.calderwood.24@ucl.ac.uk", "temppass123"),
        ]

        success_count = 0
        for first_name, last_name, email, password in default_users:
            if self.create_user(first_name, last_name, email, password):
                success_count += 1

        print(
            f" Successfully created {success_count}/{len(default_users)} default users"
        )
        return success_count == len(default_users)

    # ========================================
    # Upload Management Methods
    # ========================================

    def create_upload_record(
        self,
        filename: str,
        user_readable_name: str,
        uploaded_by: int,
        comment: str = None,
        upload_type: str = "forum_data",
    ) -> int:
        """
        Create a new upload record in the database

        Args:
            filename (str): Name of the uploaded file
            user_readable_name (str): Human-readable name for the upload
            uploaded_by (int): User ID of the uploader
            comment (str, optional): Comment about the upload
            upload_type (str, optional): Type of upload ('forum_data' or 'transcription_data')

        Returns:
            int: The ID of the created upload record
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO uploads (filename, user_readable_name, comment, uploaded_by, upload_type, status)
                    VALUES (?, ?, ?, ?, ?, 'active')
                """,
                    (filename, user_readable_name, comment, uploaded_by, upload_type),
                )

                upload_id = cursor.lastrowid
                print(
                    f" Created upload record {upload_id}: {filename} ({user_readable_name})"
                )
                return upload_id

        except Exception as e:
            print(f"❌ Error creating upload record: {e}")
            raise

    def upload_csv_data(
        self,
        upload_id: int,
        csv_data: pd.DataFrame,
        user_id: int,
    ) -> Dict:
        """
        Process and store CSV data from an upload with duplicate prevention

        Args:
            upload_id (int): ID of the upload record
            csv_data (pd.DataFrame): Pandas DataFrame containing the CSV data

        Returns:
            Dict: Result with success status, counts, and messages
        """
        try:
            import uuid

            # Make a copy to avoid SettingWithCopyWarning
            csv_data = csv_data.copy()

            with sqlite3.connect(self.db_path) as conn:
                # Add upload_id to each row
                csv_data["upload_id"] = upload_id

                # Handle column name mapping from CSV to database schema
                # Note: Database uses original CSV column names, not normalized ones
                column_mappings = {
                    "umap_x": "umap_1",
                    "umap_y": "umap_2",
                    "umap_z": "umap_3",
                }

                # Rename only UMAP columns to match database schema (LLM_inferred_question stays as-is)
                for csv_col, db_col in column_mappings.items():
                    if csv_col in csv_data.columns:
                        csv_data = csv_data.rename(columns={csv_col: db_col})

                # Separate data for posts table vs. AI tables
                # Posts table columns (including LLM data for backward compatibility)
                posts_columns = [
                    "forum",
                    "post_type",
                    "username",
                    "original_title",
                    "original_post",
                    "post_url",
                    "LLM_inferred_question",  # Include in posts table for compatibility
                    "cluster",
                    "cluster_label",
                    "llm_cluster_name",  # Include LLM cluster name for categorization
                    "date_posted",
                    "umap_1",
                    "umap_2",
                    "umap_3",
                    "upload_id",
                ]

                # Add missing posts columns with None values
                for col in posts_columns:
                    if col not in csv_data.columns:
                        csv_data[col] = None

                # Generate unique IDs for each record
                csv_data["id"] = [str(uuid.uuid4()) for _ in range(len(csv_data))]

                # Check for duplicates using composite key (original_title + ai_question_text)
                # Query existing data from normalized tables
                existing_composites = set()
                cursor = conn.execute(
                    """
                    SELECT p.original_title, COALESCE(aq.question_text, '') as question_text
                    FROM posts p
                    LEFT JOIN ai_questions aq ON p.post_id = aq.post_id
                    INNER JOIN uploads u ON p.upload_id = u.id
                    WHERE p.original_title IS NOT NULL 
                    AND aq.question_text IS NOT NULL
                                      AND u.uploaded_by = ?
                """,
                    (user_id,),
                )
                existing_composites = {
                    (row[0], row[1]) for row in cursor.fetchall() if row[0] and row[1]
                }

                # Create composite keys for new data using AI question data
                csv_data["composite_key"] = csv_data.apply(
                    lambda row: (
                        row["original_title"],
                        row.get("LLM_inferred_question", ""),
                    )
                    if pd.notna(row["original_title"])
                    and pd.notna(row.get("LLM_inferred_question"))
                    else None,
                    axis=1,
                )

                # Separate new records from duplicates based on composite key
                if existing_composites:
                    mask = ~csv_data["composite_key"].isin(existing_composites)
                    new_records = csv_data[mask]
                    duplicate_records = csv_data[~mask]
                    duplicates_count = len(duplicate_records)

                    if duplicates_count > 0:
                        duplicate_titles = duplicate_records["original_title"].tolist()[
                            :5
                        ]  # Show first 5
                        print(
                            f"⚠️ Found {duplicates_count} duplicate record(s) based on composite key"
                        )
                        print(f"   Sample duplicate titles: {duplicate_titles}")
                else:
                    new_records = csv_data
                    duplicates_count = 0

                # Remove the temporary composite_key column before insertion
                new_records = new_records.drop("composite_key", axis=1)

                # Insert new data into posts table first (without AI data)
                new_count = len(new_records)
                if new_count > 0:
                    # Prepare posts data (exclude AI columns)
                    posts_data = new_records[["id"] + posts_columns]
                    posts_data.to_sql("posts", conn, if_exists="append", index=False)

                    # Get the post_ids for the inserted records
                    post_ids = []
                    for _, row in new_records.iterrows():
                        cursor = conn.execute(
                            "SELECT post_id FROM posts WHERE id = ?", (row["id"],)
                        )
                        result = cursor.fetchone()
                        if result:
                            post_ids.append(result[0])

                    # Insert AI questions if available
                    if "LLM_inferred_question" in new_records.columns:
                        ai_questions = []
                        for idx, (_, row) in enumerate(new_records.iterrows()):
                            if pd.notna(row.get("LLM_inferred_question")) and idx < len(
                                post_ids
                            ):
                                ai_questions.append(
                                    {
                                        "post_id": post_ids[idx],
                                        "question_text": row["LLM_inferred_question"],
                                        "confidence_score": None,
                                        "model_version": "upload_v1",
                                    }
                                )

                        if ai_questions:
                            ai_questions_df = pd.DataFrame(ai_questions)
                            ai_questions_df.to_sql(
                                "ai_questions", conn, if_exists="append", index=False
                            )

                    # Insert AI categories if available
                    if "llm_cluster_name" in new_records.columns:
                        ai_categories = []
                        for idx, (_, row) in enumerate(new_records.iterrows()):
                            if pd.notna(row.get("llm_cluster_name")) and idx < len(
                                post_ids
                            ):
                                # Store as 'group' (standard category type)
                                ai_categories.append(
                                    {
                                        "post_id": post_ids[idx],
                                        "category_type": "group",
                                        "category_value": row["llm_cluster_name"],
                                        "confidence_score": None,
                                        "model_version": "upload_v1",
                                    }
                                )

                        if ai_categories:
                            ai_categories_df = pd.DataFrame(ai_categories)
                            ai_categories_df.to_sql(
                                "ai_categories", conn, if_exists="append", index=False
                            )

                # Update upload record with count
                conn.execute(
                    """
                    UPDATE uploads 
                    SET records_count = ?
                    WHERE id = ?
                """,
                    (new_count, upload_id),
                )

                result_message = f"Added {new_count} new records"
                if duplicates_count > 0:
                    result_message += f", skipped {duplicates_count} duplicates"

                print(f" Successfully processed upload {upload_id}: {result_message}")

                return {
                    "success": True,
                    "new_records": new_count,
                    "duplicates_skipped": duplicates_count,
                    "total_processed": len(csv_data),
                    "message": result_message,
                }

        except Exception as e:
            print(f"❌ Error uploading CSV data for upload {upload_id}: {e}")
            return {
                "success": False,
                "new_records": 0,
                "duplicates_skipped": 0,
                "total_processed": 0,
                "message": f"Upload failed: {str(e)}",
            }

    def save_transcription_data(self, df: pd.DataFrame, upload_id: int) -> Dict:
        """
        Save transcription data to database

        Args:
            df (pd.DataFrame): Transcription data DataFrame
            upload_id (int): Upload ID to associate with transcriptions

        Returns:
            Dict: Result with success status, message, and records_saved count
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                records_saved = 0

                for _, row in df.iterrows():
                    # Map CSV columns to database columns with type conversion
                    transcription_data = {
                        "upload_id": upload_id,
                        "session_id": row.get("session_id"),
                        "participant_id": row.get("participant_id"),
                        "session_date": self._convert_to_timestamp(
                            row.get("session_date")
                        ),
                        "session_duration": self._convert_to_int(
                            row.get("session_duration")
                        ),
                        "transcription_text": row.get("transcription_text"),
                        # Convert boolean columns (handle various formats)
                        "zoom_ease": self._convert_to_boolean(row.get("zoom_ease")),
                        "resource_access": self._convert_to_boolean(
                            row.get("resource_access")
                        ),
                        "info_missing": self._convert_to_boolean(
                            row.get("info_missing")
                        ),
                        "info_takeaway_desired": self._convert_to_boolean(
                            row.get("info_takeaway_desired")
                        ),
                        "exercise_engaged": self._convert_to_boolean(
                            row.get("exercise_engaged")
                        ),
                        "lifestyle_change": self._convert_to_boolean(
                            row.get("lifestyle_change")
                        ),
                        "postop_adherence": self._convert_to_boolean(
                            row.get("postop_adherence")
                        ),
                        "family_involved": self._convert_to_boolean(
                            row.get("family_involved")
                        ),
                        "support_needed": self._convert_to_boolean(
                            row.get("support_needed")
                        ),
                        # Convert Likert scale columns
                        "poll_usability": self._convert_to_likert(
                            row.get("poll_usability")
                        ),
                        "presession_anxiety": self._convert_to_likert(
                            row.get("presession_anxiety")
                        ),
                        "reassurance_provided": self._convert_to_likert(
                            row.get("reassurance_provided")
                        ),
                        "info_useful": self._convert_to_likert(row.get("info_useful")),
                    }

                    # Insert transcription record
                    conn.execute(
                        """
                        INSERT INTO transcriptions (
                            upload_id, session_id, participant_id, session_date, session_duration, 
                            transcription_text, zoom_ease, poll_usability, resource_access,
                            presession_anxiety, reassurance_provided, info_useful, info_missing,
                            info_takeaway_desired, exercise_engaged, lifestyle_change,
                            postop_adherence, family_involved, support_needed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        tuple(transcription_data.values()),
                    )

                    records_saved += 1

                # Update upload record with actual record count
                conn.execute(
                    """
                    UPDATE uploads SET records_count = ? WHERE id = ?
                """,
                    (records_saved, upload_id),
                )

                print(
                    f" Successfully saved {records_saved} transcription records for upload {upload_id}"
                )

                return {
                    "success": True,
                    "message": f"Successfully saved {records_saved} transcription records",
                    "records_saved": records_saved,
                }

        except Exception as e:
            print(f"❌ Error saving transcription data for upload {upload_id}: {e}")
            return {
                "success": False,
                "message": f"Error saving transcription data: {str(e)}",
                "records_saved": 0,
            }

    def _convert_to_boolean(self, value) -> bool:
        """Convert boolean representations to Python bool - STRICT: Only True/False accepted"""
        if pd.isna(value):
            return None
        if isinstance(value, bool):
            return value  # Already a proper boolean
        if isinstance(value, str):
            lower_val = value.lower().strip()
            if lower_val == "true":
                return True
            elif lower_val == "false":
                return False
            elif lower_val == "1":
                return True
            elif lower_val == "0":
                return False
            else:
                # Strict mode: Only accept True/False/1/0, reject all other formats
                raise ValueError(
                    f"Invalid boolean value '{value}' - only 'True'/'False'/'1'/'0' accepted"
                )
        if isinstance(value, int):
            if value == 1:
                return True
            elif value == 0:
                return False
            else:
                raise ValueError(f"Invalid boolean value '{value}' - only 0/1 accepted")
        if isinstance(value, float):
            # Reject all floats for strict validation
            raise ValueError(f"Invalid boolean value '{value}' - floats not accepted")
        raise ValueError(
            f"Invalid boolean value '{value}' (type: {type(value)}) - only True/False accepted"
        )

    def _convert_to_likert(self, value) -> int:
        """Validate Likert scale values - MUST be integers 1-5, no conversion"""
        if pd.isna(value):
            return None

        # Explicitly reject boolean values (even though True/False could be int 1/0)
        if isinstance(value, bool):
            raise ValueError(
                f"Boolean value '{value}' not allowed for Likert scale - must be integer 1-5"
            )

        # Assert it's already an integer in the correct range
        if isinstance(value, int) and 1 <= value <= 5:
            return value

        # If it's a string representation of a valid integer, accept it
        if isinstance(value, str):
            try:
                int_val = int(value)
                if 1 <= int_val <= 5:
                    return int_val
                else:
                    raise ValueError(
                        f"Likert value '{value}' out of range - must be integer 1-5"
                    )
            except ValueError:
                raise ValueError(
                    f"Invalid Likert value '{value}' - could not be converted to integer"
                )

        # Reject any other type or value
        raise ValueError(
            f"Invalid Likert value '{value}' (type: {type(value)}) - must be integer 1-5"
        )

    def _convert_to_timestamp(self, value) -> str:
        """Convert timestamp values to ISO format string"""
        if pd.isna(value):
            return None
        try:
            return pd.to_datetime(value).isoformat()
        except Exception:
            return str(value) if value else None

    def _convert_to_int(self, value) -> int:
        """Convert values to integer"""
        if pd.isna(value):
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def get_all_uploads(
        self, user_id: int = None, status: str = None, upload_type: str = None
    ) -> List[Dict]:
        """
        Get all upload records, optionally filtered by user, status, and/or upload type

        Args:
            user_id (int, optional): Filter uploads by user ID
            status (str, optional): Filter uploads by status ('active', 'archived', 'deleted')
            upload_type (str, optional): Filter uploads by type ('forum_data', 'transcription_data')

        Returns:
            List[Dict]: List of upload records with user information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Build query with optional filters
                base_query = """
                    SELECT u.*, us.first_name, us.last_name, us.email
                    FROM uploads u
                    LEFT JOIN users us ON u.uploaded_by = us.id
                """

                where_conditions = []
                params = []

                if user_id:
                    where_conditions.append("u.uploaded_by = ?")
                    params.append(user_id)

                if status:
                    where_conditions.append("u.status = ?")
                    params.append(status)

                if upload_type:
                    where_conditions.append("u.upload_type = ?")
                    params.append(upload_type)

                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)

                base_query += " ORDER BY u.upload_date DESC"

                cursor = conn.execute(base_query, params)

                uploads = []
                for row in cursor.fetchall():
                    upload = dict(row)
                    # Add formatted uploader name
                    if upload["first_name"] and upload["last_name"]:
                        upload["uploader_name"] = (
                            f"{upload['first_name']} {upload['last_name']}"
                        )
                    else:
                        upload["uploader_name"] = upload["email"] or "Unknown"

                    # Add status badge styling info
                    status_styles = {
                        "active": {"color": "success", "icon": ""},
                        "archived": {"color": "warning", "icon": ""},
                        "deleted": {"color": "danger", "icon": "🗑️"},
                    }
                    upload["status_style"] = status_styles.get(
                        upload["status"], {"color": "secondary", "icon": "❓"}
                    )

                    uploads.append(upload)

                return uploads

        except Exception as e:
            print(f"❌ Error getting uploads: {e}")
            return []

    def get_upload_by_id(self, upload_id: int) -> Dict:
        """
        Get a specific upload record by ID

        Args:
            upload_id (int): Upload ID to retrieve

        Returns:
            Dict: Upload record with user information, or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                cursor = conn.execute(
                    """
                    SELECT u.*, us.first_name, us.last_name, us.email
                    FROM uploads u
                    LEFT JOIN users us ON u.uploaded_by = us.id
                    WHERE u.id = ?
                """,
                    (upload_id,),
                )

                row = cursor.fetchone()
                if row:
                    upload = dict(row)
                    # Add formatted uploader name
                    if upload["first_name"] and upload["last_name"]:
                        upload["uploader_name"] = (
                            f"{upload['first_name']} {upload['last_name']}"
                        )
                    else:
                        upload["uploader_name"] = upload["email"] or "Unknown"
                    return upload
                return None

        except Exception as e:
            print(f"❌ Error getting upload {upload_id}: {e}")
            return None

    def delete_upload_and_data(self, upload_id: int, user_id: int = None) -> bool:
        """
        Delete an upload record and all associated post data

        Args:
            upload_id (int): Upload ID to delete
            user_id (int, optional): User ID for authorization check

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if upload exists and user has permission
                if user_id:
                    check_cursor = conn.execute(
                        """
                        SELECT uploaded_by FROM uploads WHERE id = ?
                    """,
                        (upload_id,),
                    )
                    result = check_cursor.fetchone()

                    if not result:
                        print(f"❌ Upload {upload_id} not found")
                        return False

                    if int(result[0]) != user_id:
                        print(
                            f"❌ User {user_id} not authorized to delete upload {upload_id}"
                        )
                        return False

                # Get record count before deletion
                count_cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM posts WHERE upload_id = ?
                """,
                    (upload_id,),
                )
                record_count = count_cursor.fetchone()[0]

                # Delete associated posts first (foreign key constraint)
                conn.execute("DELETE FROM posts WHERE upload_id = ?", (upload_id,))

                # Delete upload record
                conn.execute("DELETE FROM uploads WHERE id = ?", (upload_id,))

                print(
                    f" Deleted upload {upload_id} and {record_count} associated posts"
                )
                return True

        except Exception as e:
            print(f"❌ Error deleting upload {upload_id}: {e}")
            return False

    def get_upload_statistics(self) -> Dict:
        """
        Get statistics about uploads in the system for the current authenticated user

        Returns:
            Dict: Statistics including total uploads, total records, by status, etc.
        """
        try:
            # Get current authenticated user
            from utilities.auth import get_current_user_id

            current_user_id = get_current_user_id()

            if not current_user_id:
                return {
                    "total_uploads": 0,
                    "total_records": 0,
                    "recent_uploads": 0,
                    "by_status": {},
                    "top_uploaders": [],
                }

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                stats = {}

                # Total uploads and records for current user
                cursor = conn.execute(
                    """
                    SELECT 
                        COUNT(*) as total_uploads,
                        COALESCE(SUM(records_count), 0) as total_records
                    FROM uploads
                    WHERE uploaded_by = ?
                """,
                    (current_user_id,),
                )
                row = cursor.fetchone()
                stats.update(dict(row))

                # Upload statistics by type for current user
                cursor = conn.execute(
                    """
                    SELECT 
                        upload_type,
                        COUNT(*) as upload_count,
                        COALESCE(SUM(records_count), 0) as total_records
                    FROM uploads
                    WHERE uploaded_by = ?
                    GROUP BY upload_type
                """,
                    (current_user_id,),
                )

                # Create type-specific stats
                type_stats = {}
                for row in cursor.fetchall():
                    type_stats[row["upload_type"]] = {
                        "upload_count": row["upload_count"],
                        "total_records": row["total_records"],
                    }

                # Ensure both types are represented (with 0 counts if missing)
                stats["forum_data"] = type_stats.get(
                    "forum_data", {"upload_count": 0, "total_records": 0}
                )
                stats["transcription_data"] = type_stats.get(
                    "transcription_data", {"upload_count": 0, "total_records": 0}
                )

                # Uploads by status for current user
                cursor = conn.execute(
                    """
                    SELECT status, COUNT(*) as count
                    FROM uploads
                    WHERE uploaded_by = ?
                    GROUP BY status
                """,
                    (current_user_id,),
                )
                stats["by_status"] = {
                    row["status"]: row["count"] for row in cursor.fetchall()
                }

                # Recent uploads (last 7 days) for current user
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) as recent_uploads
                    FROM uploads
                    WHERE uploaded_by = ? AND upload_date >= datetime('now', '-7 days')
                """,
                    (current_user_id,),
                )
                stats["recent_uploads"] = cursor.fetchone()["recent_uploads"]

                # Current user's upload details (instead of top uploaders since we're filtering by user)
                cursor = conn.execute(
                    """
                    SELECT 
                        u.uploaded_by,
                        us.first_name,
                        us.last_name,
                        us.email,
                        COUNT(*) as upload_count,
                        COALESCE(SUM(u.records_count), 0) as total_records
                    FROM uploads u
                    LEFT JOIN users us ON u.uploaded_by = us.id
                    WHERE u.uploaded_by = ?
                    GROUP BY u.uploaded_by
                """,
                    (current_user_id,),
                )
                user_data = cursor.fetchone()
                stats["current_user"] = dict(user_data) if user_data else None

                return stats

        except Exception as e:
            print(f"❌ Error getting upload statistics: {e}")
            return {
                "total_uploads": 0,
                "total_records": 0,
                "recent_uploads": 0,
                "by_status": {},
                "current_user": None,
            }

    def archive_upload(self, upload_id: int, user_id: int = None) -> Dict:
        """
        Archive an upload (only active uploads, user can only archive their own)

        Args:
            upload_id (int): Upload ID to archive
            user_id (int, optional): User ID for permission check

        Returns:
            Dict: Result with success status, message, and details
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Check if upload exists and get details
                cursor = conn.execute(
                    """
                    SELECT id, user_readable_name, status, uploaded_by, records_count
                    FROM uploads 
                    WHERE id = ?
                """,
                    (upload_id,),
                )
                upload = cursor.fetchone()

                if not upload:
                    return {
                        "success": False,
                        "message": f"Upload {upload_id} not found",
                    }

                # Check permission - user can only archive their own uploads
                if user_id and str(upload["uploaded_by"]) != str(user_id):
                    return {
                        "success": False,
                        "message": "You can only archive your own uploads",
                    }

                # Check if upload is active
                if upload["status"] != "active":
                    return {
                        "success": False,
                        "message": f"Cannot archive upload with status '{upload['status']}' - only active uploads can be archived",
                    }

                # Archive the upload
                conn.execute(
                    """
                    UPDATE uploads 
                    SET status = 'archived', 
                        status_changed_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """,
                    (upload_id,),
                )

                print(
                    f" Archived upload '{upload['user_readable_name']}' (ID: {upload_id})"
                )
                return {
                    "success": True,
                    "upload_name": upload["user_readable_name"],
                    "records_count": upload["records_count"],
                }

        except Exception as e:
            print(f"❌ Error archiving upload {upload_id}: {e}")
            return {
                "success": False,
                "message": f"Error archiving upload: {str(e)}",
            }

    def restore_upload(self, upload_id: int, user_id: int = None) -> Dict:
        """
        Restore an archived upload to active status (user can only restore their own)

        Args:
            upload_id (int): Upload ID to restore
            user_id (int, optional): User ID for permission check

        Returns:
            Dict: Result with success status, message, and details
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Check if upload exists and get details
                cursor = conn.execute(
                    """
                    SELECT id, user_readable_name, status, uploaded_by, records_count
                    FROM uploads 
                    WHERE id = ?
                """,
                    (upload_id,),
                )
                upload = cursor.fetchone()

                if not upload:
                    return {
                        "success": False,
                        "message": f"Upload {upload_id} not found",
                    }

                # Check permission - user can only restore their own uploads
                if user_id and str(upload["uploaded_by"]) != str(user_id):
                    return {
                        "success": False,
                        "message": "You can only restore your own uploads",
                    }

                # Check if upload is archived
                if upload["status"] != "archived":
                    return {
                        "success": False,
                        "message": f"Cannot restore upload with status '{upload['status']}' - only archived uploads can be restored",
                    }

                # Restore the upload
                conn.execute(
                    """
                    UPDATE uploads 
                    SET status = 'active', 
                        status_changed_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """,
                    (upload_id,),
                )

                print(
                    f" Restored upload '{upload['user_readable_name']}' (ID: {upload_id})"
                )
                return {
                    "success": True,
                    "upload_name": upload["user_readable_name"],
                    "records_count": upload["records_count"],
                }

        except Exception as e:
            print(f"❌ Error restoring upload {upload_id}: {e}")
            return {
                "success": False,
                "message": f"Error restoring upload: {str(e)}",
            }

    def delete_upload_soft(self, upload_id: int, user_id: int = None) -> Dict:
        """
        Soft delete an upload (ONLY archived uploads, user can only delete their own)

        Args:
            upload_id (int): Upload ID to delete
            user_id (int, optional): User ID for permission check

        Returns:
            Dict: Result with success status, message, and details
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Check if upload exists and get details
                cursor = conn.execute(
                    """
                    SELECT id, user_readable_name, status, uploaded_by, records_count
                    FROM uploads 
                    WHERE id = ?
                """,
                    (upload_id,),
                )
                upload = cursor.fetchone()

                if not upload:
                    return {
                        "success": False,
                        "message": f"Upload {upload_id} not found",
                    }

                # Check permission - user can only delete their own uploads
                if user_id and str(upload["uploaded_by"]) != str(user_id):
                    return {
                        "success": False,
                        "message": "You can only delete your own uploads",
                    }

                # Check if upload is archived (ONLY archived uploads can be deleted)
                if upload["status"] != "archived":
                    return {
                        "success": False,
                        "message": f"Cannot delete upload with status '{upload['status']}' - only archived uploads can be deleted. Archive the upload first.",
                    }

                # Soft delete the upload
                conn.execute(
                    """
                    UPDATE uploads 
                    SET status = 'deleted', 
                        status_changed_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """,
                    (upload_id,),
                )

                print(
                    f" Soft deleted upload '{upload['user_readable_name']}' (ID: {upload_id})"
                )
                return {
                    "success": True,
                    "upload_name": upload["user_readable_name"],
                    "records_count": upload["records_count"],
                }

        except Exception as e:
            print(f"❌ Error soft deleting upload {upload_id}: {e}")
            return {
                "success": False,
                "message": f"Error deleting upload: {str(e)}",
            }

    def delete_upload_permanent(self, upload_id: int, user_id: int = None) -> Dict:
        """
        Permanently delete an upload and all associated data (ADMIN ONLY, only deleted uploads)

        Args:
            upload_id (int): Upload ID to permanently delete
            user_id (int, optional): User ID for admin permission check

        Returns:
            Dict: Result with success status, message, and details
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Check if upload exists and get details
                cursor = conn.execute(
                    """
                    SELECT id, user_readable_name, status, uploaded_by, records_count
                    FROM uploads 
                    WHERE id = ?
                """,
                    (upload_id,),
                )
                upload = cursor.fetchone()

                if not upload:
                    return {
                        "success": False,
                        "message": f"Upload {upload_id} not found",
                    }

                # Check admin permission - only Philip Calderwood (User ID 1) can permanently delete
                from utilities.auth import require_admin

                try:
                    require_admin()  # This will raise an exception if not admin
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Admin privileges required for permanent deletion: {str(e)}",
                    }

                # Check if upload is in deleted status (ONLY deleted uploads can be permanently deleted)
                if upload["status"] != "deleted":
                    return {
                        "success": False,
                        "message": f"Cannot permanently delete upload with status '{upload['status']}' - only deleted uploads can be permanently removed. Delete the upload first.",
                    }

                # Count associated posts before deletion
                count_cursor = conn.execute(
                    "SELECT COUNT(*) FROM posts WHERE upload_id = ?",
                    (upload_id,),
                )
                record_count = count_cursor.fetchone()[0]

                # Permanently delete associated posts first (foreign key constraint)
                conn.execute("DELETE FROM posts WHERE upload_id = ?", (upload_id,))

                # Permanently delete upload record
                conn.execute("DELETE FROM uploads WHERE id = ?", (upload_id,))

                print(
                    f"🔥 PERMANENTLY deleted upload '{upload['user_readable_name']}' (ID: {upload_id}) and {record_count} posts"
                )
                return {
                    "success": True,
                    "upload_name": upload["user_readable_name"],
                    "records_deleted": record_count,
                }

        except Exception as e:
            print(f"❌ Error permanently deleting upload {upload_id}: {e}")
            return {
                "success": False,
                "message": f"Error permanently deleting upload: {str(e)}",
            }

    def get_transcription_data_by_upload_id(self, upload_id: int) -> List[Dict]:
        """
        Retrieve transcription data for a specific upload

        Args:
            upload_id (int): Upload ID to get transcription data for

        Returns:
            List[Dict]: List of transcription records with all experimental fields
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Check if transcriptions table exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='transcriptions'
                """)

                if not cursor.fetchone():
                    print("⚠️ Transcriptions table does not exist")
                    return []

                # Get transcription data for the upload
                cursor = conn.execute(
                    """
                    SELECT 
                        id,
                        upload_id,
                        session_id,
                        participant_id,
                        session_date,
                        session_duration,
                        transcription_text,
                        -- Digital Access fields
                        zoom_ease,
                        poll_usability,
                        resource_access,
                        -- Emotional Response fields
                        presession_anxiety,
                        reassurance_provided,
                        -- Information Quality fields
                        info_useful,
                        info_missing,
                        info_takeaway_desired,
                        -- Behavioral Outcomes fields
                        exercise_engaged,
                        lifestyle_change,
                        postop_adherence,
                        -- Support Systems fields
                        family_involved,
                        support_needed,
                        created_at
                    FROM transcriptions 
                    WHERE upload_id = ?
                    ORDER BY created_at DESC
                """,
                    (upload_id,),
                )

                transcriptions = []
                for row in cursor.fetchall():
                    transcription_dict = dict(row)
                    transcriptions.append(transcription_dict)

                print(
                    f" Retrieved {len(transcriptions)} transcription records for upload {upload_id}"
                )
                return transcriptions

        except Exception as e:
            print(f"❌ Error retrieving transcription data for upload {upload_id}: {e}")
            return []

    def get_all_transcription_data(self, user_id: int = None) -> List[Dict]:
        """
        Retrieve all transcription data for the current user

        Args:
            user_id (int, optional): User ID to filter transcriptions (defaults to current user)

        Returns:
            List[Dict]: List of all transcription records with upload information
        """
        try:
            # Get current user if not provided
            if user_id is None:
                from utilities.auth import get_current_user

                current_user = get_current_user()
                if not current_user:
                    print("⚠️ No authenticated user found")
                    return []
                user_id = current_user.get("id")

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Check if transcriptions table exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='transcriptions'
                """)

                if not cursor.fetchone():
                    print("⚠️ Transcriptions table does not exist")
                    return []

                # Get all transcription data for user's uploads
                cursor = conn.execute(
                    """
                    SELECT 
                        t.id,
                        t.upload_id,
                        t.session_id,
                        t.participant_id,
                        t.session_date,
                        t.session_duration,
                        t.transcription_text,
                        -- Digital Access fields
                        t.zoom_ease,
                        t.poll_usability,
                        t.resource_access,
                        -- Emotional Response fields
                        t.presession_anxiety,
                        t.reassurance_provided,
                        -- Information Quality fields
                        t.info_useful,
                        t.info_missing,
                        t.info_takeaway_desired,
                        -- Behavioral Outcomes fields
                        t.exercise_engaged,
                        t.lifestyle_change,
                        t.postop_adherence,
                        -- Support Systems fields
                        t.family_involved,
                        t.support_needed,
                        t.created_at,
                        -- Upload information
                        u.user_readable_name as upload_name,
                        u.created_at as upload_date
                    FROM transcriptions t
                    JOIN uploads u ON t.upload_id = u.id
                    WHERE u.uploaded_by = ? AND u.status = 'active'
                    ORDER BY t.created_at DESC
                """,
                    (user_id,),
                )

                transcriptions = []
                for row in cursor.fetchall():
                    transcription_dict = dict(row)
                    transcriptions.append(transcription_dict)

                print(
                    f" Retrieved {len(transcriptions)} total transcription records for user {user_id}"
                )
                return transcriptions

        except Exception as e:
            print(f"❌ Error retrieving all transcription data: {e}")
            return []


# Dash callback functions (compatible with existing app structure)
def setup_mrpc_database_callbacks(app):
    """Setup Dash callbacks for MRPC database system"""
    from dash import Input, Output, State, no_update
    import dash

    # Initialize the database
    db = MRPCDatabase()

    @app.callback(
        [
            Output(
                {"type": "sidebar-group-dropdown", "item_id": dash.dependencies.MATCH},
                "value",
            ),
            Output(
                {
                    "type": "sidebar-subgroup-dropdown",
                    "item_id": dash.dependencies.MATCH,
                },
                "value",
            ),
            Output(
                {"type": "sidebar-tags-dropdown", "item_id": dash.dependencies.MATCH},
                "value",
            ),
        ],
        [
            Input(
                {"type": "sidebar-group-dropdown", "item_id": dash.dependencies.MATCH},
                "id",
            )
        ],
        prevent_initial_call=False,
    )
    def populate_dropdown_values(dropdown_id):
        """Populate dropdown values when sidebar opens"""
        if not dropdown_id:
            return no_update, no_update, no_update

        item_id = dropdown_id["item_id"]
        tags_data = db.get_tags_for_item(item_id)

        # Extract just the values for dropdowns (they expect strings, not dicts)
        groups = [
            tag.get("value", tag) if isinstance(tag, dict) else tag
            for tag in tags_data.get("groups", [])
        ]
        subgroups = [
            tag.get("value", tag) if isinstance(tag, dict) else tag
            for tag in tags_data.get("subgroups", [])
        ]
        tags = [
            tag.get("value", tag) if isinstance(tag, dict) else tag
            for tag in tags_data.get("tags", [])
        ]

        return (groups, subgroups, tags)

    @app.callback(
        [
            Output(
                {"type": "sidebar-group-dropdown", "item_id": dash.dependencies.MATCH},
                "options",
            ),
            Output(
                {
                    "type": "sidebar-subgroup-dropdown",
                    "item_id": dash.dependencies.MATCH,
                },
                "options",
            ),
            Output(
                {"type": "sidebar-tags-dropdown", "item_id": dash.dependencies.MATCH},
                "options",
            ),
        ],
        [
            Input(
                {"type": "sidebar-group-dropdown", "item_id": dash.dependencies.MATCH},
                "id",
            )
        ],
        prevent_initial_call=False,
    )
    def populate_dropdown_options(dropdown_id):
        """Populate dropdown options with source-based styling for this specific item"""
        if not dropdown_id:
            return [], [], []

        item_id = dropdown_id["item_id"]

        # Get available options (all possible tags)
        available = db.get_available_tags()

        # Get existing tags for this specific item (with source info)
        existing_tags = db.get_tags_for_item(item_id)

        # Create source lookup for this specific item
        def create_source_lookup(tag_list):
            lookup = {}
            for tag in tag_list:
                if isinstance(tag, dict):
                    lookup[tag.get("value", "")] = tag.get("source", "ai")
            return lookup

        groups_sources = create_source_lookup(existing_tags.get("groups", []))
        subgroups_sources = create_source_lookup(existing_tags.get("subgroups", []))
        tags_sources = create_source_lookup(existing_tags.get("tags", []))

        # Create styled options for each dropdown
        def create_styled_options(tag_list, source_lookup):
            """Create dropdown options with proper Dash styling using html.Span"""
            from dash import html

            options = []
            for tag_value in tag_list:
                source = source_lookup.get(
                    tag_value, "user"
                )  # Default to user for new tags

                # Create styled label using html.Span based on source
                if source == "ai":
                    styled_label = html.Span(
                        [tag_value],
                        style={
                            "color": "#856404",
                            "backgroundColor": "#fff3cd",
                            "borderLeft": "4px solid #ffc107",
                            "padding": "8px 12px",
                            "margin": "2px 0",
                            "display": "block",
                        },
                    )
                else:
                    styled_label = html.Span(
                        [tag_value],
                        style={
                            "color": "#0c5460",
                            "backgroundColor": "#d1ecf1",
                            "borderLeft": "4px solid #17a2b8",
                            "padding": "8px 12px",
                            "margin": "2px 0",
                            "display": "block",
                        },
                    )

                options.append({"label": styled_label, "value": tag_value})
            return options

        group_options = create_styled_options(
            available.get("groups", []), groups_sources
        )
        subgroup_options = create_styled_options(
            available.get("subgroups", []), subgroups_sources
        )
        tag_options = create_styled_options(available.get("tags", []), tags_sources)

        return group_options, subgroup_options, tag_options

    @app.callback(
        Output(
            {"type": "sidebar-save-feedback", "item_id": dash.dependencies.MATCH},
            "children",
        ),
        [
            Input(
                {"type": "sidebar-save-tags-btn", "item_id": dash.dependencies.MATCH},
                "n_clicks",
            )
        ],
        [
            State(
                {"type": "sidebar-group-dropdown", "item_id": dash.dependencies.MATCH},
                "value",
            ),
            State(
                {
                    "type": "sidebar-subgroup-dropdown",
                    "item_id": dash.dependencies.MATCH,
                },
                "value",
            ),
            State(
                {"type": "sidebar-tags-dropdown", "item_id": dash.dependencies.MATCH},
                "value",
            ),
            State(
                {"type": "sidebar-save-tags-btn", "item_id": dash.dependencies.MATCH},
                "id",
            ),
        ],
        prevent_initial_call=True,
    )
    def save_tags(n_clicks, groups, subgroups, tags, button_id):
        """Save tags when save button is clicked"""
        print("🔍 DEBUG: Save tags callback triggered!")
        print(f"🔍 DEBUG: n_clicks={n_clicks}, button_id={button_id}")
        print(f"🔍 DEBUG: groups={groups}, subgroups={subgroups}, tags={tags}")

        if not n_clicks or not button_id:
            print("🔍 DEBUG: No clicks or no button_id, returning empty")
            return ""

        item_id = button_id["item_id"]
        print(f"🔍 DEBUG: Extracted item_id={item_id}")

        tags_data = {
            "groups": groups or [],
            "subgroups": subgroups or [],
            "tags": tags or [],
        }

        print(f"🔍 DEBUG: Calling save_tags_for_item with: {tags_data}")
        success = db.save_tags_for_item(item_id, tags_data, source="user")

        if success:
            print("🔍 DEBUG: Save successful!")
            return " Tags saved successfully!"
        else:
            print("🔍 DEBUG: Save failed!")
            return "❌ Error saving tags"

    # print(" MRPC Database callbacks registered")


def get_styled_dropdown_options(item_id: str):
    """Get styled dropdown options for a specific item - helper function for UMAP module"""
    db = MRPCDatabase()

    # Get available options (all possible tags)
    available = db.get_available_tags()

    # Get existing tags for this specific item (with source info)
    existing_tags = db.get_tags_for_item(item_id)

    # Create source lookup for this specific item
    def create_source_lookup(tag_list):
        lookup = {}
        for tag in tag_list:
            if isinstance(tag, dict):
                lookup[tag.get("value", "")] = tag.get("source", "ai")
        return lookup

    groups_sources = create_source_lookup(existing_tags.get("groups", []))
    subgroups_sources = create_source_lookup(existing_tags.get("subgroups", []))
    tags_sources = create_source_lookup(existing_tags.get("tags", []))

    # Create styled options for each dropdown
    def create_styled_options(tag_list, source_lookup):
        """Create dropdown options with proper Dash styling using html.Span"""
        from dash import html

        options = []
        for tag_value in tag_list:
            source = source_lookup.get(
                tag_value, "user"
            )  # Default to user for new tags

            # Create styled label using html.Span based on source
            if source == "ai":
                styled_label = html.Span(
                    [tag_value],
                    style={
                        "color": "#856404",
                        "backgroundColor": "#fff3cd",
                        "borderLeft": "4px solid #ffc107",
                        "padding": "8px 12px",
                        "margin": "2px 0",
                        "display": "block",
                    },
                )
            else:
                styled_label = html.Span(
                    [tag_value],
                    style={
                        "color": "#0c5460",
                        "backgroundColor": "#d1ecf1",
                        "borderLeft": "4px solid #17a2b8",
                        "padding": "8px 12px",
                        "margin": "2px 0",
                        "display": "block",
                    },
                )

            options.append({"label": styled_label, "value": tag_value})
        return options

    group_options = create_styled_options(available.get("groups", []), groups_sources)
    subgroup_options = create_styled_options(
        available.get("subgroups", []), subgroups_sources
    )
    tag_options = create_styled_options(available.get("tags", []), tags_sources)

    return group_options, subgroup_options, tag_options
