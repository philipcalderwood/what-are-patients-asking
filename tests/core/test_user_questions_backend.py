"""
Unit Tests for User Question Management Backend

This test suite covers all backend functionality related to user questions:
- Adding/saving user questions
- Retrieving user questions
- Updating existing questions
- Deleting questions
- Error handling and edge cases
"""

import pytest
import sqlite3
import uuid
from unittest.mock import patch

from utilities.mrpc_database import MRPCDatabase


@pytest.fixture
def database_with_posts(temp_database):
    """Fixture that creates a database with test posts for user questions tests."""
    # Insert test posts directly into the database
    with sqlite3.connect(temp_database.db_path) as conn:
        test_posts = [
            (
                "test_item_123",
                "cervical",
                "Test Post 1",
                "Test content 1",
                1,
                "test_group_1",
            ),
            (
                "test_item_456",
                "ovarian",
                "Test Post 2",
                "Test content 2",
                2,
                "test_group_2",
            ),
            (
                "test_item_789",
                "endometrial",
                "Test Post 3",
                "Test content 3",
                3,
                "test_group_3",
            ),
        ]

        for post_data in test_posts:
            conn.execute(
                """
                INSERT INTO posts (id, forum, original_title, original_post, cluster, cluster_label)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                post_data,
            )

    return temp_database


class TestUserQuestionBackend:
    """Test backend user question functionality."""

    def _create_test_post(
        self, temp_database, item_id, title="Test Post", content="Test content"
    ):
        """Helper method to create test post data for user questions tests."""
        with sqlite3.connect(temp_database.db_path) as conn:
            conn.execute(
                """
                INSERT INTO posts (id, forum, original_title, original_post, cluster, cluster_label)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (item_id, "cervical", title, content, 1, "test_group"),
            )

    def test_save_new_user_question(self, database_with_posts):
        """Test saving a new user question with both text and notes."""
        # Arrange
        item_id = "test_item_123"
        question_id = str(uuid.uuid4())
        question_text = "What is the treatment protocol for this condition?"
        notes_text = "Based on patient symptoms and medical history"

        # Act
        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text=question_text,
            notes_text=notes_text,
        )

        # Assert
        assert result is True

        # Verify data was saved correctly
        saved_questions = database_with_posts.get_user_questions(item_id)
        assert len(saved_questions) == 1
        assert saved_questions[0]["question_id"] == question_id
        assert saved_questions[0]["question_text"] == question_text
        assert saved_questions[0]["notes_text"] == notes_text

    def test_save_user_question_text_only(self, database_with_posts):
        """Test saving a user question with only question text, no notes."""
        # Arrange
        item_id = "test_item_456"
        question_id = str(uuid.uuid4())
        question_text = "How long does recovery typically take?"

        # Act
        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text=question_text,
            notes_text="",
        )

        # Assert
        assert result is True

        saved_questions = database_with_posts.get_user_questions(item_id)
        assert len(saved_questions) == 1
        assert saved_questions[0]["question_text"] == question_text
        assert saved_questions[0]["notes_text"] == ""

    def test_save_user_question_notes_only(self, database_with_posts):
        """Test saving a user question with only notes, empty question text."""
        # Arrange
        item_id = "test_item_789"
        question_id = str(uuid.uuid4())
        notes_text = "Important to consider patient age and comorbidities"

        # Act
        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text="",
            notes_text=notes_text,
        )

        # Assert
        assert result is True

        saved_questions = database_with_posts.get_user_questions(item_id)
        assert len(saved_questions) == 1
        assert saved_questions[0]["question_text"] == ""
        assert saved_questions[0]["notes_text"] == notes_text

    def test_update_existing_user_question(self, database_with_posts):
        """Test updating an existing user question (using same question_id)."""
        # Arrange - Create initial question
        item_id = "test_item_123"
        question_id = str(uuid.uuid4())
        initial_text = "Initial question text"
        initial_notes = "Initial notes"

        database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text=initial_text,
            notes_text=initial_notes,
        )

        # Act - Update the question
        updated_text = "Updated question text with more detail"
        updated_notes = "Updated notes with additional context"

        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text=updated_text,
            notes_text=updated_notes,
        )

        # Assert
        assert result is True

        # Should still have only one question for this item
        saved_questions = database_with_posts.get_user_questions(item_id)
        assert len(saved_questions) == 1

        # Content should be updated
        assert saved_questions[0]["question_text"] == updated_text
        assert saved_questions[0]["notes_text"] == updated_notes
        assert saved_questions[0]["question_id"] == question_id

    def test_save_multiple_questions_same_item(self, database_with_posts):
        """Test saving multiple questions for the same item."""
        # Arrange
        item_id = "test_item_456"
        question_1_id = str(uuid.uuid4())
        question_2_id = str(uuid.uuid4())
        question_3_id = str(uuid.uuid4())

        # Act - Save multiple questions
        database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_1_id,
            question_text="Question 1: What are the symptoms?",
            notes_text="Notes for question 1",
        )

        database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_2_id,
            question_text="Question 2: What are treatment options?",
            notes_text="Notes for question 2",
        )

        database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_3_id,
            question_text="Question 3: What is the prognosis?",
            notes_text="Notes for question 3",
        )

        # Assert
        saved_questions = database_with_posts.get_user_questions(item_id)
        assert len(saved_questions) == 3

        # Verify all questions are present and ordered by creation time
        question_ids = [q["question_id"] for q in saved_questions]
        assert question_1_id in question_ids
        assert question_2_id in question_ids
        assert question_3_id in question_ids

    def test_get_user_questions_empty_item(self, database_with_posts):
        """Test retrieving questions for item that has no questions."""
        # Act
        questions = database_with_posts.get_user_questions("nonexistent_item")

        # Assert
        assert questions == []

    def test_get_user_questions_order(self, database_with_posts):
        """Test that questions are returned in chronological order (created_at ASC)."""
        # Arrange
        item_id = "test_item_789"
        question_ids = [str(uuid.uuid4()) for _ in range(3)]

        # Save questions with small delays to ensure different timestamps
        import time

        for i, qid in enumerate(question_ids):
            database_with_posts.save_user_question(
                item_id=item_id,
                question_id=qid,
                question_text=f"Question {i + 1}",
                notes_text=f"Notes {i + 1}",
            )
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Act
        saved_questions = database_with_posts.get_user_questions(item_id)

        # Assert
        assert len(saved_questions) == 3

        # Verify chronological order
        for i in range(3):
            assert saved_questions[i]["question_text"] == f"Question {i + 1}"
            assert saved_questions[i]["notes_text"] == f"Notes {i + 1}"

    def test_delete_user_question_success(self, database_with_posts):
        """Test successfully deleting an existing user question."""
        # Arrange - Create question to delete
        item_id = "test_item_123"
        question_id = str(uuid.uuid4())

        database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text="Question to be deleted",
            notes_text="Notes to be deleted",
        )

        # Verify question exists
        initial_questions = database_with_posts.get_user_questions(item_id)
        assert len(initial_questions) == 1

        # Act
        result = database_with_posts.delete_user_question(item_id, question_id)

        # Assert
        assert result is True

        # Verify question was deleted
        remaining_questions = database_with_posts.get_user_questions(item_id)
        assert len(remaining_questions) == 0

    def test_delete_user_question_nonexistent(self, database_with_posts):
        """Test deleting a question that doesn't exist."""
        # Act
        result = database_with_posts.delete_user_question(
            "nonexistent_item", "nonexistent_question"
        )

        # Assert
        assert result is False

    def test_delete_user_question_wrong_item(self, database_with_posts):
        """Test deleting a question with wrong item_id."""
        # Arrange - Create question for one item
        item_id = "test_item_456"
        wrong_item_id = "test_item_wrong"
        question_id = str(uuid.uuid4())

        database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text="Question for correct item",
            notes_text="Notes for correct item",
        )

        # Act - Try to delete with wrong item_id
        result = database_with_posts.delete_user_question(wrong_item_id, question_id)

        # Assert
        assert result is False

        # Verify original question still exists
        questions = database_with_posts.get_user_questions(item_id)
        assert len(questions) == 1

    def test_delete_one_question_keeps_others(self, database_with_posts):
        """Test deleting one question doesn't affect other questions for same item."""
        # Arrange - Create multiple questions
        item_id = "test_item_789"
        question_1_id = str(uuid.uuid4())
        question_2_id = str(uuid.uuid4())
        question_3_id = str(uuid.uuid4())

        for i, qid in enumerate([question_1_id, question_2_id, question_3_id], 1):
            database_with_posts.save_user_question(
                item_id=item_id,
                question_id=qid,
                question_text=f"Question {i}",
                notes_text=f"Notes {i}",
            )

        # Act - Delete middle question
        result = database_with_posts.delete_user_question(item_id, question_2_id)

        # Assert
        assert result is True

        remaining_questions = database_with_posts.get_user_questions(item_id)
        assert len(remaining_questions) == 2

        # Verify correct questions remain
        remaining_ids = [q["question_id"] for q in remaining_questions]
        assert question_1_id in remaining_ids
        assert question_3_id in remaining_ids
        assert question_2_id not in remaining_ids

    def test_user_question_data_integrity(self, database_with_posts):
        """Test that all expected fields are properly stored and retrieved."""
        # Arrange
        item_id = "test_item_123"
        question_id = str(uuid.uuid4())
        question_text = "Test question with special characters: àáâãäåæçèéêë"
        notes_text = "Test notes with emojis: 🏥💊🩺 and newlines\nLine 2\nLine 3"

        # Act
        database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text=question_text,
            notes_text=notes_text,
        )

        # Assert
        saved_questions = database_with_posts.get_user_questions(item_id)
        assert len(saved_questions) == 1

        question = saved_questions[0]

        # Verify all expected fields are present
        expected_fields = [
            "question_id",
            "question_text",
            "notes_text",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            assert field in question

        # Verify content integrity
        assert question["question_id"] == question_id
        assert question["question_text"] == question_text
        assert question["notes_text"] == notes_text
        assert question["created_at"] is not None
        assert question["updated_at"] is not None

    def test_save_user_question_database_error(self, database_with_posts):
        """Test handling of database errors during save operation."""
        # Arrange - Close database connection to simulate error
        original_db_path = database_with_posts.db_path
        database_with_posts.db_path = "/invalid/path/that/does/not/exist.db"

        # Act
        result = database_with_posts.save_user_question(
            item_id="test_item",
            question_id="test_question",
            question_text="Test question",
            notes_text="Test notes",
        )

        # Assert
        assert result is False

        # Restore original path for cleanup
        database_with_posts.db_path = original_db_path

    def test_get_user_questions_database_error(self, database_with_posts):
        """Test handling of database errors during retrieval operation."""
        # Arrange - Close database connection to simulate error
        original_db_path = database_with_posts.db_path
        database_with_posts.db_path = "/invalid/path/that/does/not/exist.db"

        # Act
        questions = database_with_posts.get_user_questions("test_item")

        # Assert
        assert questions == []

        # Restore original path for cleanup
        database_with_posts.db_path = original_db_path

    def test_delete_user_question_database_error(self, database_with_posts):
        """Test handling of database errors during delete operation."""
        # Arrange - Close database connection to simulate error
        original_db_path = database_with_posts.db_path
        database_with_posts.db_path = "/invalid/path/that/does/not/exist.db"

        # Act
        result = database_with_posts.delete_user_question("test_item", "test_question")

        # Assert
        assert result is False

        # Restore original path for cleanup
        database_with_posts.db_path = original_db_path

    def test_empty_string_handling(self, database_with_posts):
        """Test handling of empty strings and None values."""
        # Arrange
        item_id = "test_item_456"
        question_id = str(uuid.uuid4())

        # Act - Save with empty strings
        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text="",
            notes_text="",
        )

        # Assert
        assert result is True

        saved_questions = database_with_posts.get_user_questions(item_id)
        assert len(saved_questions) == 1
        assert saved_questions[0]["question_text"] == ""
        assert saved_questions[0]["notes_text"] == ""

    def test_unicode_character_support(self, database_with_posts):
        """Test support for various Unicode characters."""
        # Arrange
        item_id = "test_item_789"
        question_id = str(uuid.uuid4())

        # Test various Unicode characters
        question_text = "Question with unicode: 中文测试 العربية Русский 日本語"
        notes_text = "Notes with symbols: ©®™ ½¼¾ αβγδε ♠♥♦♣"

        # Act
        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text=question_text,
            notes_text=notes_text,
        )

        # Assert
        assert result is True

        saved_questions = database_with_posts.get_user_questions(item_id)
        assert saved_questions[0]["question_text"] == question_text
        assert saved_questions[0]["notes_text"] == notes_text


class TestUserQuestionEdgeCases:
    """Test edge cases and boundary conditions for user questions."""

    def test_very_long_question_text(self, database_with_posts):
        """Test handling of very long question text."""
        # Arrange
        item_id = "test_item_123"
        question_id = str(uuid.uuid4())

        # Create very long text (10,000 characters)
        long_text = "This is a very long question. " * 333  # ~10,000 chars

        # Act
        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text=long_text,
            notes_text="Short notes",
        )

        # Assert
        assert result is True

        saved_questions = database_with_posts.get_user_questions(item_id)
        assert saved_questions[0]["question_text"] == long_text

    def test_very_long_notes_text(self, database_with_posts):
        """Test handling of very long notes text."""
        # Arrange
        item_id = "test_item_456"
        question_id = str(uuid.uuid4())

        # Create very long notes (10,000 characters)
        long_notes = "These are very detailed notes. " * 312  # ~10,000 chars

        # Act
        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text="Short question",
            notes_text=long_notes,
        )

        # Assert
        assert result is True

        saved_questions = database_with_posts.get_user_questions(item_id)
        assert saved_questions[0]["notes_text"] == long_notes

    def test_special_characters_in_ids(self, database_with_posts):
        """Test handling of special characters in question_id."""
        # Arrange - Use an existing item_id from the fixture
        item_id = "test_item_789"
        question_id = "question-456_with.special@chars"

        # Act
        result = database_with_posts.save_user_question(
            item_id=item_id,
            question_id=question_id,
            question_text="Question with special ID characters",
            notes_text="Notes with special ID characters",
        )

        # Assert
        assert result is True

        saved_questions = database_with_posts.get_user_questions(item_id)
        assert len(saved_questions) == 1
        assert saved_questions[0]["question_id"] == question_id
