"""
Test suite for AI card functionality in the metadata sidebar.
Tests the new individual card structure for AI questions and categories.
"""

from unittest.mock import patch, MagicMock
from umap_viz_module import (
    create_ai_question_component,
    create_ai_category_component,
    load_existing_ai_questions,
    load_existing_ai_categories,
)


class TestAICardFunctionality:
    """Test AI card generation and loading functionality"""

    def test_create_ai_question_component(self):
        """Test AI question component creation"""
        data_id = "test_id_123"
        ai_question_data = {
            "id": 1,
            "question_text": "What is the main topic of this post?",
            "confidence_score": 0.85,
            "model_version": "gpt-4",
            "created_at": "2025-08-28 10:00:00",
            "updated_at": "2025-08-28 10:00:00",
        }

        component = create_ai_question_component(
            data_id, ai_question_data, question_number=1
        )

        # Check that component is created
        assert component is not None
        assert hasattr(component, "children")

        # Check card structure
        card_header = component.children[0]
        card_body = component.children[1]

        # Verify header contains question number and confidence badge
        assert "AI Question 1" in str(card_header)
        assert "Confidence: 0.85" in str(card_header)

        # Verify body contains question text
        assert "What is the main topic of this post?" in str(card_body)

        # Verify CSS classes are applied
        assert "ai-question-card" in str(component)
        assert "ai-card-header-title" in str(component)
        assert "ai-card-content-text" in str(component)

    def test_create_ai_category_component(self):
        """Test AI category component creation"""
        data_id = "test_id_456"
        ai_category_data = {
            "id": 2,
            "category_type": "topic_classification",
            "category_value": "Technology > Software Development",
            "confidence_score": 0.92,
            "model_version": "gpt-4",
            "created_at": "2025-08-28 10:05:00",
            "updated_at": "2025-08-28 10:05:00",
        }

        component = create_ai_category_component(
            data_id, ai_category_data, category_number=2
        )

        # Check that component is created
        assert component is not None
        assert hasattr(component, "children")

        # Check card structure
        card_header = component.children[0]
        card_body = component.children[1]

        # Verify header contains category number and confidence badge
        assert "AI Category 2" in str(card_header)
        assert "Topic Classification" in str(card_header)
        assert "Confidence: 0.92" in str(card_header)

        # Verify body contains category value
        assert "Technology > Software Development" in str(card_body)

        # Verify CSS classes are applied
        assert "ai-category-card" in str(component)
        assert "ai-card-header-title" in str(component)
        assert "ai-card-content-text" in str(component)

    @patch("utilities.mrpc_database.MRPCDatabase")
    def test_load_ai_questions_with_data(self, mock_db_class):
        """Test loading AI questions when data exists"""
        # Mock database instance and method
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_ai_questions.return_value = [
            {
                "id": 1,
                "question_text": "What technology is discussed?",
                "confidence_score": 0.88,
                "model_version": "gpt-4",
                "created_at": "2025-08-28 09:00:00",
                "updated_at": "2025-08-28 09:00:00",
            },
            {
                "id": 2,
                "question_text": "What are the main benefits mentioned?",
                "confidence_score": 0.76,
                "model_version": "gpt-4",
                "created_at": "2025-08-28 09:30:00",
                "updated_at": "2025-08-28 09:30:00",
            },
        ]

        data_id = "test_123"
        components = load_existing_ai_questions(data_id)

        # Verify database method was called
        mock_db.get_ai_questions.assert_called_once_with(data_id)

        # Verify two components were created
        assert len(components) == 2

        # Verify components are properly structured
        assert "AI Question 1" in str(components[0])
        assert "AI Question 2" in str(components[1])
        assert "What technology is discussed?" in str(components[0])
        assert "What are the main benefits mentioned?" in str(components[1])

    @patch("utilities.mrpc_database.MRPCDatabase")
    def test_load_ai_questions_no_data(self, mock_db_class):
        """Test loading AI questions when no data exists"""
        # Mock database instance and method
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_ai_questions.return_value = []

        data_id = "test_456"
        components = load_existing_ai_questions(data_id)

        # Verify database method was called
        mock_db.get_ai_questions.assert_called_once_with(data_id)

        # Verify empty list returned
        assert components == []

    @patch("utilities.mrpc_database.MRPCDatabase")
    def test_load_ai_categories_with_data(self, mock_db_class):
        """Test loading AI categories when data exists"""
        # Mock database instance and method
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_ai_categories.return_value = [
            {
                "id": 1,
                "category_type": "topic",
                "category_value": "Software Engineering",
                "confidence_score": 0.95,
                "model_version": "gpt-4",
                "created_at": "2025-08-28 10:00:00",
                "updated_at": "2025-08-28 10:00:00",
            },
            {
                "id": 2,
                "category_type": "sentiment",
                "category_value": "Positive",
                "confidence_score": 0.82,
                "model_version": "gpt-4",
                "created_at": "2025-08-28 10:15:00",
                "updated_at": "2025-08-28 10:15:00",
            },
        ]

        data_id = "test_789"
        components = load_existing_ai_categories(data_id)

        # Verify database method was called
        mock_db.get_ai_categories.assert_called_once_with(data_id)

        # Verify two components were created
        assert len(components) == 2

        # Verify components are properly structured
        assert "AI Category 1" in str(components[0])
        assert "AI Category 2" in str(components[1])
        assert "Software Engineering" in str(components[0])
        assert "Positive" in str(components[1])

    @patch("utilities.mrpc_database.MRPCDatabase")
    def test_load_ai_categories_no_data(self, mock_db_class):
        """Test loading AI categories when no data exists"""
        # Mock database instance and method
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_ai_categories.return_value = []

        data_id = "test_999"
        components = load_existing_ai_categories(data_id)

        # Verify database method was called
        mock_db.get_ai_categories.assert_called_once_with(data_id)

        # Verify empty list returned
        assert components == []

    def test_ai_question_component_handles_missing_data(self):
        """Test AI question component handles missing or None data gracefully"""
        data_id = "test_empty"
        ai_question_data = {
            "id": 1,
            "question_text": None,
            "confidence_score": None,
            "model_version": "",
            "created_at": "",
            "updated_at": "",
        }

        component = create_ai_question_component(data_id, ai_question_data)

        # Verify component is still created
        assert component is not None

        # Verify fallback text is used
        assert "No question available" in str(component)
        assert "N/A" in str(component)  # For confidence score

    def test_ai_category_component_handles_missing_data(self):
        """Test AI category component handles missing or None data gracefully"""
        data_id = "test_empty"
        ai_category_data = {
            "id": 1,
            "category_type": None,
            "category_value": None,
            "confidence_score": None,
            "model_version": "",
            "created_at": "",
            "updated_at": "",
        }

        component = create_ai_category_component(data_id, ai_category_data)

        # Verify component is still created
        assert component is not None

        # Verify fallback text is used
        assert "No category available" in str(component)
        assert "N/A" in str(component)  # For confidence score

    @patch("utilities.mrpc_database.MRPCDatabase")
    def test_database_error_handling(self, mock_db_class):
        """Test that database errors are handled gracefully"""
        # Mock database to raise an exception
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_ai_questions.side_effect = Exception("Database connection failed")

        data_id = "test_error"
        components = load_existing_ai_questions(data_id)

        # Verify empty list returned on error
        assert components == []
