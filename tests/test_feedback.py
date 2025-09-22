"""
Unit tests for the feedback system to verify functionality
"""

import pytest
import uuid
import tempfile
import os
from unittest.mock import patch, MagicMock

# Import the functions we want to test
from umap_viz_module import (
    create_review_content_card,
    save_feedback_to_db,
    load_existing_feedback,
    _create_ai_feedback_card,
)


class TestFeedbackSystem:
    """Test suite for the feedback system"""

    def test_create_review_content_card_basic(self):
        """Test that create_review_content_card creates a card without errors"""
        # Mock the database functions to avoid database dependency
        with patch("umap_viz_module.load_existing_feedback", return_value=None):
            card = create_review_content_card(
                data_id="test_123",
                content_type="LLM_inferred_question",
                display_label="AI Inferred Question",
                value="Is this treatment effective for stage 2 cervical cancer?",
                card_type="ai_feedback",
            )

        # Verify card was created
        assert card is not None
        assert hasattr(card, "children")
        assert card.className == "ai-content-card h-100"
        assert card.color == "light"  # No existing feedback = light color
        assert card.outline == True

    def test_create_review_content_card_with_existing_positive_feedback(self):
        """Test card creation with existing positive feedback"""
        mock_feedback = {
            "rating": "positive",
            "feedback_text": "This looks good!",
            "response_id": "test-response-id",
            "user_display_name": "John Doe",
            "formatted_time": "January 15, 2024 at 14:30",
        }

        with patch(
            "umap_viz_module.load_existing_feedback", return_value=mock_feedback
        ):
            card = create_review_content_card(
                data_id="test_123",
                content_type="LLM_inferred_question",
                display_label="AI Inferred Question",
                value="Is this treatment effective?",
                card_type="ai_feedback",
            )

        # Card should be green for positive feedback
        assert card.color == "success"

        # Should have feedback display in the card
        card_body = card.children[0]  # CardBody
        body_content = card_body.children

        # Find feedback display (should be one of the children)
        feedback_display = None
        for child in body_content:
            if hasattr(child, "className") and "user-feedback-display" in str(
                child.className
            ):
                feedback_display = child
                break

        assert feedback_display is not None, (
            "Feedback display should be present for existing feedback"
        )

    def test_create_review_content_card_with_existing_negative_feedback(self):
        """Test card creation with existing negative feedback"""
        mock_feedback = {
            "rating": "negative",
            "feedback_text": "This needs improvement",
            "response_id": "test-response-id-2",
            "user_display_name": "Jane Smith",
            "formatted_time": "January 16, 2024 at 09:15",
        }

        with patch(
            "umap_viz_module.load_existing_feedback", return_value=mock_feedback
        ):
            card = create_review_content_card(
                data_id="test_456",
                content_type="llm_cluster_name",
                display_label="AI Inferred Category",
                value="Treatment Options",
                card_type="ai_feedback",
            )

        # Card should be red for negative feedback
        assert card.color == "danger"

    def test_create_review_content_card_different_types(self):
        """Test creating different card types"""
        # Test basic card type
        basic_card = create_review_content_card(
            data_id="test_basic",
            content_type="test",
            display_label="Basic Card",
            value="Basic content",
            card_type="basic",
        )
        assert basic_card.color == "light"
        assert "ai-content-feedback-buttons" not in str(basic_card.children)

        # Test metadata card type
        metadata_card = create_review_content_card(
            data_id="test_metadata",
            content_type="test",
            display_label="Metadata Card",
            value="Metadata content",
            card_type="metadata",
        )
        assert metadata_card.color == "light"

    def test_card_components_structure(self):
        """Test that AI feedback cards have the expected component structure"""
        with patch("umap_viz_module.load_existing_feedback", return_value=None):
            card = create_review_content_card(
                data_id="test_structure",
                content_type="LLM_inferred_question",
                display_label="AI Inferred Question",
                value="Test question?",
                card_type="ai_feedback",
            )

        # Verify structure
        assert len(card.children) == 1  # Should have CardBody

        card_body = card.children[0]
        body_content = card_body.children

        # Should have main text, buttons, edit button, and collapsible feedback area
        assert len(body_content) >= 4

        # Find the main text div
        main_text = body_content[0]
        assert hasattr(main_text, "className")
        assert main_text.className == "ai-content-main-text"
        assert "Test question?" in str(main_text.children)

        # Find the feedback buttons
        button_group = body_content[1]
        assert hasattr(button_group, "className")
        assert "ai-content-feedback-buttons" in button_group.className

        # Should have thumbs up and thumbs down buttons
        buttons = button_group.children
        assert len(buttons) == 2

        # Check thumbs up button
        thumbs_up = buttons[0]
        assert thumbs_up.color == "outline-success"
        assert any("fa-thumbs-up" in str(child) for child in thumbs_up.children)
        assert any("Good" in str(child) for child in thumbs_up.children)

        # Check thumbs down button
        thumbs_down = buttons[1]
        assert thumbs_down.color == "outline-danger"
        assert any("fa-thumbs-down" in str(child) for child in thumbs_down.children)
        assert any("Poor" in str(child) for child in thumbs_down.children)

    def test_card_with_header(self):
        """Test card creation with header enabled"""
        with patch("umap_viz_module.load_existing_feedback", return_value=None):
            card = create_review_content_card(
                data_id="test_header",
                content_type="test",
                display_label="Test Header",
                value="Content with header",
                card_type="ai_feedback",
                show_header=True,
            )

        # Should have both CardHeader and CardBody
        assert len(card.children) == 2

        # First child should be CardHeader
        card_header = card.children[0]
        assert hasattr(card_header, "children")

        # Second child should be CardBody
        card_body = card.children[1]
        assert hasattr(card_body, "children")

    def test_invalid_card_type_raises_error(self):
        """Test that invalid card type raises ValueError"""
        with pytest.raises(ValueError, match="Unknown card_type: invalid_type"):
            create_review_content_card(
                data_id="test_error",
                content_type="test",
                display_label="Error Test",
                value="This should fail",
                card_type="invalid_type",
            )

    @patch("umap_viz_module.save_feedback_to_db")
    @patch("umap_viz_module.load_existing_feedback")
    def test_save_and_load_feedback_integration(
        self, mock_load_feedback, mock_save_feedback
    ):
        """Test the integration between saving and loading feedback"""
        # Mock the feedback functions directly
        mock_save_feedback.return_value = True

        test_feedback = {
            "rating": "positive",
            "feedback_text": "Integration test feedback",
            "response_id": "integration-test-id",
            "user_display_name": "Test User",
            "formatted_time": "January 17, 2024 at 12:00",
        }
        mock_load_feedback.return_value = test_feedback

        # Test saving feedback
        success = save_feedback_to_db(
            data_id="integration_test",
            inference_type="LLM_inferred_question",
            rating="positive",
            feedback_text="Integration test feedback",
            response_id="integration-test-id",
        )
        assert success == True

        # Verify save was called with correct parameters
        mock_save_feedback.assert_called_once_with(
            data_id="integration_test",
            inference_type="LLM_inferred_question",
            rating="positive",
            feedback_text="Integration test feedback",
            response_id="integration-test-id",
        )

        # Test loading feedback
        loaded_feedback = load_existing_feedback(
            "integration_test", "LLM_inferred_question"
        )
        assert loaded_feedback == test_feedback

        # Verify get was called with correct parameters
        mock_load_feedback.assert_called_once_with(
            "integration_test", "LLM_inferred_question"
        )

    def test_card_button_ids_are_unique(self):
        """Test that card buttons have unique, properly formatted IDs"""
        with patch("umap_viz_module.load_existing_feedback", return_value=None):
            card = create_review_content_card(
                data_id="unique_test_123",
                content_type="LLM_inferred_question",
                display_label="AI Inferred Question",
                value="Unique test question?",
                card_type="ai_feedback",
            )

        # Extract button IDs from the card structure
        card_body = card.children[0]
        button_group = card_body.children[1]  # Feedback buttons

        thumbs_up_button = button_group.children[0]
        thumbs_down_button = button_group.children[1]

        # Check thumbs up button ID structure
        thumbs_up_id = thumbs_up_button.id
        assert thumbs_up_id["type"] == "ai-content-thumbs-up"
        assert thumbs_up_id["data_id"] == "unique_test_123"
        assert thumbs_up_id["content_type"] == "LLM_inferred_question"
        assert "response_id" in thumbs_up_id

        # Check thumbs down button ID structure
        thumbs_down_id = thumbs_down_button.id
        assert thumbs_down_id["type"] == "ai-content-thumbs-down"
        assert thumbs_down_id["data_id"] == "unique_test_123"
        assert thumbs_down_id["content_type"] == "LLM_inferred_question"
        assert "response_id" in thumbs_down_id

        # Response IDs should be the same for both buttons (same card)
        assert thumbs_up_id["response_id"] == thumbs_down_id["response_id"]

    def test_feedback_display_formatting(self):
        """Test that existing feedback is properly formatted in the display"""
        mock_feedback = {
            "rating": "positive",
            "feedback_text": "This is excellent work! Very accurate inference.",
            "response_id": "display-test-id",
            "user_display_name": "Dr. Jane Smith",
            "formatted_time": "January 18, 2024 at 15:45",
        }

        with patch(
            "umap_viz_module.load_existing_feedback", return_value=mock_feedback
        ):
            card = create_review_content_card(
                data_id="display_test",
                content_type="LLM_inferred_question",
                display_label="AI Inferred Question",
                value="Display test question?",
                card_type="ai_feedback",
            )

        # Convert card to string to search for formatted content
        card_str = str(card)

        # Should contain user name
        assert "Dr. Jane Smith" in card_str
        # Should contain feedback text in quotes
        assert '"This is excellent work! Very accurate inference."' in card_str
        # Should contain formatted time
        assert "January 18, 2024 at 15:45" in card_str
        # Should have positive feedback styling class
        assert "positive" in card_str


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
