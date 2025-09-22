#!/usr/bin/env python3
"""
Migration script to implement single-row plan:
- Change posts table to use auto-incrementing post_id as primary key
- Create AI_questions, AI_categories, USERS_questions, USERS_categories tables
- Maintain data integrity and foreign key relationships
"""

import sqlite3


def migrate_database(db_path: str = "data/mrpc.db"):
    return
    pass
    """Execute the single-row migration plan"""

    print("🚀 Starting single-row migration...")

    try:
        with sqlite3.connect(db_path) as conn:
            # Disable foreign key constraints during migration
            conn.execute("PRAGMA foreign_keys = OFF")

            print("📋 Step 1: Create new posts table with post_id as PK...")

            # Create new posts table with post_id as primary key
            conn.execute("""
                CREATE TABLE posts_new (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT UNIQUE NOT NULL,  -- Keep original id as unique but not PK
                    forum TEXT NOT NULL,
                    post_type TEXT,
                    username TEXT,
                    original_title TEXT,
                    original_post TEXT,
                    post_url TEXT,
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

            print("📋 Step 2: Fix NULL/empty IDs and migrate data...")

            # First, fix any NULL or empty IDs
            conn.execute("""
                UPDATE posts 
                SET id = 'generated_id_' || rowid 
                WHERE id IS NULL OR id = ''
            """)

            # Copy data from old posts table to new one
            conn.execute("""
                INSERT INTO posts_new (
                    id, forum, post_type, username, original_title, original_post, 
                    post_url, cluster, cluster_label, date_posted, 
                    umap_1, umap_2, umap_3, upload_id
                )
                SELECT 
                    id, forum, post_type, username, original_title, original_post,
                    post_url, cluster, cluster_label, date_posted,
                    umap_1, 
                    CASE WHEN umap_2 = 'NULL' OR umap_2 = '' THEN NULL ELSE CAST(umap_2 AS REAL) END,
                    umap_3, upload_id
                FROM posts
            """)

            print("📋 Step 3: Create AI content tables...")

            # Create AI questions table
            conn.execute("""
                CREATE TABLE ai_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    question_text TEXT,
                    confidence_score REAL,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts_new(post_id) ON DELETE CASCADE
                )
            """)

            # Create AI categories table
            conn.execute("""
                CREATE TABLE ai_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    category_type TEXT NOT NULL,  -- 'group', 'subgroup', 'tag'
                    category_value TEXT NOT NULL,
                    confidence_score REAL,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts_new(post_id) ON DELETE CASCADE
                )
            """)

            print("📋 Step 4: Create user content tables...")

            # Create user questions table (rename existing user_questions)
            conn.execute("""
                CREATE TABLE users_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    question_id TEXT NOT NULL,
                    question_text TEXT,
                    notes_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, question_id),
                    FOREIGN KEY (post_id) REFERENCES posts_new(post_id) ON DELETE CASCADE
                )
            """)

            # Create user categories table (rename existing category_notes)
            conn.execute("""
                CREATE TABLE users_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    note_id TEXT NOT NULL,
                    notes_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, note_id),
                    FOREIGN KEY (post_id) REFERENCES posts_new(post_id) ON DELETE CASCADE
                )
            """)

            print("📋 Step 5: Migrate AI content from posts table...")

            # Migrate LLM inferred questions from posts to ai_questions
            conn.execute("""
                INSERT INTO ai_questions (post_id, question_text, model_version)
                SELECT 
                    pn.post_id,
                    p.LLM_inferred_question,
                    'legacy'
                FROM posts p
                JOIN posts_new pn ON p.id = pn.id
                WHERE p.LLM_inferred_question IS NOT NULL 
                AND p.LLM_inferred_question != ''
            """)

            # Migrate LLM cluster names from posts to ai_categories
            conn.execute("""
                INSERT INTO ai_categories (post_id, category_type, category_value, model_version)
                SELECT 
                    pn.post_id,
                    'cluster_name',
                    p.llm_cluster_name,
                    'legacy'
                FROM posts p
                JOIN posts_new pn ON p.id = pn.id
                WHERE p.llm_cluster_name IS NOT NULL 
                AND p.llm_cluster_name != ''
            """)

            print("📋 Step 6: Migrate existing user content...")

            # Migrate user_questions to users_questions
            conn.execute("""
                INSERT INTO users_questions (post_id, question_id, question_text, notes_text, created_at, updated_at)
                SELECT 
                    pn.post_id,
                    uq.question_id,
                    uq.question_text,
                    uq.notes_text,
                    uq.created_at,
                    uq.updated_at
                FROM user_questions uq
                JOIN posts_new pn ON uq.item_id = pn.id
            """)

            # Migrate category_notes to users_categories
            conn.execute("""
                INSERT INTO users_categories (post_id, note_id, notes_text, created_at, updated_at)
                SELECT 
                    pn.post_id,
                    cn.note_id,
                    cn.notes_text,
                    cn.created_at,
                    cn.updated_at
                FROM category_notes cn
                JOIN posts_new pn ON cn.item_id = pn.id
            """)

            print("📋 Step 7: Migrate tags to ai_categories...")

            # Migrate existing tags to ai_categories, preserving source information
            conn.execute("""
                INSERT INTO ai_categories (post_id, category_type, category_value, model_version, created_at, updated_at)
                SELECT 
                    pn.post_id,
                    t.tag_type,
                    t.tag_value,
                    CASE WHEN t.source = 'ai' THEN 'legacy_ai' ELSE 'user_migrated' END,
                    t.created_at,
                    t.updated_at
                FROM tags t
                JOIN posts_new pn ON t.item_id = pn.id
            """)

            print("📋 Step 8: Update other tables to reference post_id...")

            # Create new inference_feedback table with post_id reference
            conn.execute("""
                CREATE TABLE inference_feedback_new (
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
                    FOREIGN KEY (post_id) REFERENCES posts_new(post_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Migrate inference_feedback data
            conn.execute("""
                INSERT INTO inference_feedback_new (
                    post_id, inference_type, rating, feedback_text, response_id, 
                    user_id, created_at, updated_at
                )
                SELECT 
                    pn.post_id,
                    inf.inference_type,
                    inf.rating,
                    inf.feedback_text,
                    inf.response_id,
                    inf.user_id,
                    inf.created_at,
                    inf.updated_at
                FROM inference_feedback inf
                JOIN posts_new pn ON inf.data_id = pn.id
            """)

            print("📋 Step 9: Drop old tables and rename new ones...")

            # Drop old tables
            conn.execute("DROP TABLE posts")
            conn.execute("DROP TABLE tags")
            conn.execute("DROP TABLE user_questions")
            conn.execute("DROP TABLE category_notes")
            conn.execute("DROP TABLE inference_feedback")

            # Rename new tables
            conn.execute("ALTER TABLE posts_new RENAME TO posts")
            conn.execute(
                "ALTER TABLE inference_feedback_new RENAME TO inference_feedback"
            )

            print("📋 Step 10: Create indexes for performance...")

            # Create indexes
            indexes = [
                "CREATE INDEX idx_posts_id ON posts(id)",
                "CREATE INDEX idx_posts_forum ON posts(forum)",
                "CREATE INDEX idx_posts_cluster ON posts(cluster)",
                "CREATE INDEX idx_posts_upload_id ON posts(upload_id)",
                "CREATE INDEX idx_ai_questions_post_id ON ai_questions(post_id)",
                "CREATE INDEX idx_ai_categories_post_id ON ai_categories(post_id)",
                "CREATE INDEX idx_ai_categories_type ON ai_categories(category_type)",
                "CREATE INDEX idx_users_questions_post_id ON users_questions(post_id)",
                "CREATE INDEX idx_users_questions_question_id ON users_questions(question_id)",
                "CREATE INDEX idx_users_categories_post_id ON users_categories(post_id)",
                "CREATE INDEX idx_users_categories_note_id ON users_categories(note_id)",
                "CREATE INDEX idx_inference_feedback_post_id ON inference_feedback(post_id)",
                "CREATE INDEX idx_inference_feedback_type ON inference_feedback(inference_type)",
                "CREATE INDEX idx_inference_feedback_response_id ON inference_feedback(response_id)",
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

            print("📋 Step 11: Update schema version...")

            # Update schema version to indicate this migration
            conn.execute("""
                INSERT INTO schema_version (version, description)
                VALUES (3, 'Single-row migration: post_id as PK, separated AI/user content')
            """)

            # Re-enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")

            # Verify migration
            cursor = conn.execute("SELECT COUNT(*) FROM posts")
            posts_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM ai_questions")
            ai_questions_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM ai_categories")
            ai_categories_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM users_questions")
            users_questions_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM users_categories")
            users_categories_count = cursor.fetchone()[0]

            print(" Migration completed successfully!")
            print(f"   Posts: {posts_count}")
            print(f"   🤖 AI Questions: {ai_questions_count}")
            print(f"   🤖 AI Categories: {ai_categories_count}")
            print(f"   👤 User Questions: {users_questions_count}")
            print(f"   👤 User Categories: {users_categories_count}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    migrate_database()
