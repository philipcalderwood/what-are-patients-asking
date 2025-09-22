#!/usr/bin/env python3
"""
Test script to upload CSV to a temp database and examine the             # Verify posts have data including post_url
            required_post_columns = ['id', 'forum', 'original_title', 'original_post', 
                                   'LLM_inferred_question', 'post_url', 'cluster', 'umap_1', 'umap_2', 'umap_3']
            for col in required_post_columns:
                assert col in posts_df.columns, f"Missing required column in posts: {col}"
            
            # Verify posts have data
            first_post = posts_df.iloc[0]
            assert first_post['LLM_inferred_question'] == 'Question 1?', f"Unexpected LLM question: {first_post['LLM_inferred_question']}"
            assert first_post['forum'] == 'cervical', f"Unexpected forum: {first_post['forum']}"
            assert first_post['post_url'] == 'https://forum.cervical.com/post/test_1', f"Unexpected post_url: {first_post['post_url']}"
            print(f"   ✅ Posts table verified: {len(posts_df)} rows with correct data including URLs")ata structure
"""

import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utilities.mrpc_database import MRPCDatabase
from utilities.upload_service import UploadService


def create_temp_database_and_test_upload():
    """Create a temporary database, upload CSV, and examine the data structure"""
    
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    print(f"🗄️ Created temporary database: {temp_db_path}")
    
    # Mock authentication to return user ID 1 and admin privileges
    with patch("utilities.auth.get_current_user_id", return_value=1), \
         patch("utilities.auth.require_admin", return_value=None), \
         patch("utilities.upload_service.get_current_user_id", return_value=1):
        try:
            # Initialize database
            db = MRPCDatabase(db_path=temp_db_path)
            upload_service = UploadService()
            upload_service.db = db  # Use our temp database
            
            print("✅ Database initialized with schema")
            
            # Test 1: Verify full schema is created
            print("\n🏗️ Testing Schema Creation...")
            assert_schema_exists(db)
            
            # Try to create a test user
            try:
                user_created = db.create_user(
                    first_name="Test",
                    last_name="User", 
                    email="test@example.com",
                    password="testpass"
                )
                print(f"👤 Test user created: {user_created}")
                assert user_created, "Failed to create test user"
            except Exception as e:
                print(f"⚠️ Could not create test user: {e}")
                raise
            
            # Load the sample CSV
            csv_path = Path(__file__).parent / "test_data" / "forum_sample.csv"
            sample_df = pd.read_csv(csv_path)
            print(f"📄 Loaded sample CSV with {len(sample_df)} rows")
            print(f"📄 CSV columns: {list(sample_df.columns)}")
            
            # Convert to base64 (like a real upload)
            csv_content = sample_df.to_csv(index=False)
            import base64
            csv_base64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
            csv_with_prefix = f"data:text/csv;base64,{csv_base64}"
            
            # Test 2: Process upload
            print("\n🔄 Testing Upload Process...")
            upload_result = upload_service.process_file_upload(
                contents=csv_with_prefix,
                filename="forum_sample.csv",
                user_readable_name="Test Forum Sample",
                comment="Test upload from script"
            )
            
            print(f"📤 Upload result: {upload_result}")
            assert upload_result['success'], f"Upload failed: {upload_result.get('message', 'Unknown error')}"
            assert upload_result['new_records'] == 3, f"Expected 3 new records, got {upload_result['new_records']}"
            
            # Test 3: Verify posts table data
            print("\n📋 Testing Posts Table...")
            posts_df = db.get_all_posts_as_dataframe(user_id=1, include_all_users=True)
            assert len(posts_df) == 3, f"Expected 3 posts, found {len(posts_df)}"
            
            # Verify posts have required columns
            required_post_columns = ['id', 'forum', 'original_title', 'original_post', 
                                   'LLM_inferred_question', 'cluster', 'umap_1', 'umap_2', 'umap_3']
            for col in required_post_columns:
                assert col in posts_df.columns, f"Missing required column in posts: {col}"
            
            # Verify posts have data
            first_post = posts_df.iloc[0]
            assert first_post['LLM_inferred_question'] == 'Question 1?', f"Unexpected LLM question: {first_post['LLM_inferred_question']}"
            assert first_post['forum'] == 'cervical', f"Unexpected forum: {first_post['forum']}"
            print(f"   ✅ Posts table verified: {len(posts_df)} rows with correct data")
            
            # Test 4: Verify ai_questions table is populated
            print("\n🤖 Testing AI Questions Table...")
            first_post_id = first_post['id']
            
            # Check that ai_questions table was populated during upload
            import sqlite3
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ai_questions")
                total_ai_questions = cursor.fetchone()[0]
                print(f"   ✅ AI questions table populated: {total_ai_questions} records")
                
                # Verify ai_questions have proper post_id foreign keys
                cursor.execute("""
                    SELECT aq.id, aq.post_id, aq.question_text, p.id as post_text_id
                    FROM ai_questions aq 
                    JOIN posts p ON aq.post_id = p.post_id
                    ORDER BY aq.id
                """)
                ai_questions_with_posts = cursor.fetchall()
                print(f"   ✅ AI questions with valid post relationships: {len(ai_questions_with_posts)}")
                
                # Verify each AI question corresponds to LLM_inferred_question in posts
                for aq_id, post_id, question_text, post_text_id in ai_questions_with_posts:
                    cursor.execute("SELECT LLM_inferred_question FROM posts WHERE post_id = ?", (post_id,))
                    original_question = cursor.fetchone()[0]
                    assert question_text == original_question, "AI question text should match original LLM_inferred_question"
                
                print("   ✅ All AI questions match their source LLM_inferred_question data")
            
            # Test the get_ai_questions method (which uses URL-based lookup from posts table)
            ai_questions = db.get_ai_questions(first_post_id)
            
            # ASSERTION: ai_questions table should be populated from the CSV data
            assert total_ai_questions > 0, "AI questions table should be populated from CSV LLM_inferred_question column"
            
            # ASSERTION: get_ai_questions method should return data (from posts table via URL lookup)
            assert len(ai_questions) > 0, "get_ai_questions method should return data from posts table via URL lookup"
            
            # Verify the content of the AI question returned by get_ai_questions
            assert ai_questions[0]['question_text'] == 'Question 1?', f"Expected 'Question 1?', got '{ai_questions[0]['question_text']}'"
            assert 'confidence_score' in ai_questions[0], "AI question should have confidence_score"
            assert 'model_version' in ai_questions[0], "AI question should have model_version"
            print(f"   ✅ get_ai_questions method verified: returns {len(ai_questions)} questions for post {first_post_id}")
            
            # Verify the AI question matches the CSV data
            assert ai_questions[0]['question_text'] == 'Question 1?', f"Expected 'Question 1?', got '{ai_questions[0]['question_text']}'"
            assert 'confidence_score' in ai_questions[0], "AI question should have confidence_score"
            assert 'model_version' in ai_questions[0], "AI question should have model_version"
            print(f"   ✅ AI Questions verified: {len(ai_questions)} questions for post {first_post_id}")
            
            # Test 5: Verify ai_categories table is populated (if cluster data exists)
            print("\n🏷️ Testing AI Categories Table...")
            ai_categories = db.get_ai_categories(first_post_id)
            
            # ASSERTION: If we have cluster data, it should create categories
            if first_post['cluster'] is not None:
                assert len(ai_categories) > 0, "AI categories should be created from cluster data"
                print(f"   ✅ AI Categories verified: {len(ai_categories)} categories for post {first_post_id}")
            else:
                print("   ℹ️ No cluster data, skipping category verification")
            
            # Test 6: Verify uploads table
            print("\n📁 Testing Uploads Table...")
            uploads = upload_service.get_all_uploads()
            assert len(uploads) == 1, f"Expected 1 upload record, found {len(uploads)}"
            
            upload_record = uploads[0]
            assert upload_record['filename'] == 'forum_sample.csv', f"Unexpected filename: {upload_record['filename']}"
            assert upload_record['upload_type'] == 'forum_data', f"Unexpected upload type: {upload_record['upload_type']}"
            assert upload_record['records_count'] == 3, f"Expected 3 records, got {upload_record['records_count']}"
            print(f"   ✅ Uploads table verified: {len(uploads)} upload records")
            
            # Test 7: Verify data relationships
            print("\n🔗 Testing Data Relationships...")
            
            # Check that all posts have valid upload_id references
            for _, post in posts_df.iterrows():
                assert post['upload_id'] == upload_record['id'], f"Post upload_id {post['upload_id']} doesn't match upload record {upload_record['id']}"
            
            # Check that AI questions reference valid posts
            for post_row in posts_df.itertuples():
                post_ai_questions = db.get_ai_questions(post_row.id)
                if len(post_ai_questions) > 0:
                    # Verify the questions relate to the correct post
                    post_id_from_db = db._get_post_id_from_id(post_row.id)
                    assert post_id_from_db is not None, f"Could not find post_id for {post_row.id}"
            
            print("   ✅ Data relationships verified")
            
            print("\n🎉 All tests passed! Database structure and population is correct.")
            
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            print("\n🔧 This indicates missing functionality that needs to be implemented.")
            raise
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
            raise
            
        finally:
            # Clean up temp database
            try:
                os.unlink(temp_db_path)
                print(f"🧹 Cleaned up temporary database: {temp_db_path}")
            except Exception:
                pass


def assert_schema_exists(db: 'MRPCDatabase'):
    """Assert that all required tables exist in the database schema"""
    import sqlite3
    
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Required tables based on the schema
        required_tables = [
            'posts',
            'ai_questions', 
            'ai_categories',
            'users_questions',
            'users_categories',
            'uploads',
            'users',
            'inference_feedback',
            'transcriptions',
            'schema_version'
        ]
        
        print(f"   📊 Found tables: {sorted(tables)}")
        
        for table in required_tables:
            assert table in tables, f"Required table '{table}' is missing from database schema"
        
        # Verify key table structures
        print(f"   ✅ All required tables present: {len(required_tables)} tables")
        
        # Check posts table structure
        cursor.execute("PRAGMA table_info(posts)")
        posts_columns = [row[1] for row in cursor.fetchall()]
        required_posts_columns = ['post_id', 'id', 'forum', 'original_title', 'original_post', 'LLM_inferred_question']
        for col in required_posts_columns:
            assert col in posts_columns, f"Required column '{col}' missing from posts table"
        
        # Check ai_questions table structure  
        cursor.execute("PRAGMA table_info(ai_questions)")
        ai_questions_columns = [row[1] for row in cursor.fetchall()]
        required_ai_questions_columns = ['id', 'post_id', 'question_text', 'confidence_score', 'model_version']
        for col in required_ai_questions_columns:
            assert col in ai_questions_columns, f"Required column '{col}' missing from ai_questions table"
        
        print("   ✅ Table structures validated")


if __name__ == "__main__":
    create_temp_database_and_test_upload()
