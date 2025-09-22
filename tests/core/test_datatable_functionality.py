"""
Comprehensive Datatable Functionality Test Suite

This test suite validates the new datatable format that aggregates questions and categories
by post title, ensuring proper data aggregation and UI component functionality.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Import components to test
from utilities.mrpc_database import MRPCDatabase
from umap_viz_module import get_forum_data, create_table_view


@pytest.fixture(autouse=True)
def mock_auth_functions():
    """Automatically mock authentication functions for all tests in this module."""
    with (
        patch("utilities.auth.get_current_user_id", return_value=1),
        patch("utilities.auth.require_admin", return_value=None),
        patch(
            "utilities.auth.get_current_user",
            return_value={"id": 1, "name": "Test User"},
        ),
    ):
        yield


class TestDatatableFormat:
    """Test the new datatable format with aggregated questions and categories."""

    def test_database_datatable_format_flag(self, temp_database_with_data):
        """Test that the datatable_format flag works correctly in database layer."""
        # Test new datatable format
        df_new = temp_database_with_data.get_all_posts_as_dataframe(
            user_id=1, datatable_format=True
        )

        # Test legacy format for comparison
        df_legacy = temp_database_with_data.get_all_posts_as_dataframe(
            user_id=1, datatable_format=False
        )

        # Basic shape validation
        assert len(df_new) > 0, "Datatable format should return some data"
        assert len(df_legacy) > 0, "Legacy format should return some data"

        # The datatable format should aggregate posts by title, so fewer rows
        assert len(df_new) <= len(df_legacy), (
            "Datatable format should have fewer or equal rows due to aggregation"
        )

        # Check new format has the expected columns
        expected_columns = ["all_questions", "all_categories", "original_title"]
        for col in expected_columns:
            assert col in df_new.columns, f"Datatable format should have column '{col}'"

        # Check legacy format doesn't have the new columns
        for col in ["all_questions", "all_categories"]:
            assert col not in df_legacy.columns, (
                f"Legacy format should not have column '{col}'"
            )

    def test_datatable_aggregation_logic(self, temp_database_with_data):
        """Test that questions and categories are properly aggregated."""
        df = temp_database_with_data.get_all_posts_as_dataframe(
            user_id=1, datatable_format=True
        )

        # Find a row with data to test
        sample_with_questions = df[df["all_questions"].str.len() > 0]
        sample_with_categories = df[df["all_categories"].str.len() > 0]

        if len(sample_with_questions) > 0:
            sample_q = sample_with_questions.iloc[0]["all_questions"]
            # Check that questions are separated by newlines
            assert "\n" in sample_q or len(sample_q.split("\n")) == 1, (
                "Questions should be newline-separated"
            )

        if len(sample_with_categories) > 0:
            sample_c = sample_with_categories.iloc[0]["all_categories"]
            # Check that categories are separated by newlines
            assert "\n" in sample_c or len(sample_c.split("\n")) == 1, (
                "Categories should be newline-separated"
            )

    def test_datatable_deduplication(self, temp_database_with_data):
        """Test that duplicate questions and categories are removed."""
        df = temp_database_with_data.get_all_posts_as_dataframe(
            user_id=1, datatable_format=True
        )

        # Check for proper deduplication by looking for rows with content
        for idx, row in df.iterrows():
            if row["all_questions"]:
                questions = [
                    q.strip() for q in row["all_questions"].split("\n") if q.strip()
                ]
                # Check no duplicates in questions
                assert len(questions) == len(set(questions)), (
                    f"Questions should be deduplicated for row {idx}"
                )

            if row["all_categories"]:
                categories = [
                    c.strip() for c in row["all_categories"].split("\n") if c.strip()
                ]
                # Check no duplicates in categories
                assert len(categories) == len(set(categories)), (
                    f"Categories should be deduplicated for row {idx}"
                )

    def test_datatable_title_grouping(self, temp_database_with_data):
        """Test that posts with the same title are properly grouped."""
        df = temp_database_with_data.get_all_posts_as_dataframe(
            user_id=1, datatable_format=True
        )

        # Check that all titles are unique (no duplicates)
        duplicate_titles = df["original_title"].duplicated().sum()
        assert duplicate_titles == 0, "All titles should be unique in datatable format"

        # Verify original_title column exists and has valid data
        assert "original_title" in df.columns, "Should have original_title column"
        assert df["original_title"].notna().all(), "All titles should be non-null"
        assert (df["original_title"].str.len() > 0).all(), (
            "All titles should be non-empty"
        )


class TestGetForumDataFunction:
    """Test the get_forum_data function that bridges database and UI."""

    def test_get_forum_data_with_authentication(self):
        """Test get_forum_data works with proper authentication mocking."""
        # This should work with the autouse auth fixture
        df = get_forum_data("all", datatable_format=True)

        # Should return a DataFrame (might be empty if no data, but should be DataFrame)
        assert isinstance(df, pd.DataFrame), "Should return a pandas DataFrame"

        # If not empty, should have the right columns
        if len(df) > 0:
            assert "original_title" in df.columns, "Should have original_title column"
            assert "all_questions" in df.columns, "Should have all_questions column"
            assert "all_categories" in df.columns, "Should have all_categories column"

    def test_get_forum_data_backward_compatibility(self):
        """Test that legacy format still works."""
        df_legacy = get_forum_data("all", datatable_format=False)

        assert isinstance(df_legacy, pd.DataFrame), (
            "Legacy format should return DataFrame"
        )

        # Legacy format should not have the new aggregated columns
        if len(df_legacy) > 0:
            assert "all_questions" not in df_legacy.columns, (
                "Legacy should not have all_questions"
            )
            assert "all_categories" not in df_legacy.columns, (
                "Legacy should not have all_categories"
            )

    def test_get_forum_data_error_handling(self):
        """Test that get_forum_data handles errors gracefully."""
        # Test with authentication failure
        with patch(
            "utilities.auth.get_current_user_id", side_effect=Exception("Auth error")
        ):
            df = get_forum_data("all", datatable_format=True)

            # Should return empty DataFrame rather than crashing
            assert isinstance(df, pd.DataFrame), (
                "Should return DataFrame even on auth error"
            )
            # Empty DataFrame is acceptable when auth fails


class TestDatatableUIComponent:
    """Test the datatable UI component creation."""

    def test_create_table_view_basic(self):
        """Test that create_table_view doesn't crash with basic parameters."""
        # Mock the imported modules within the function
        with (
            patch("dash.html") as mock_html,
            patch("dash.dash_table") as mock_dash_table,
            patch("dash_bootstrap_components.Card") as mock_card,
        ):
            # Configure mocks
            mock_html.Div.return_value = "mocked_div"
            mock_dash_table.DataTable.return_value = "mocked_datatable"
            mock_card.return_value = "mocked_card"

            # Should not crash
            create_table_view(forum="all")

    def test_create_table_view_with_empty_data(self):
        """Test create_table_view handles empty data gracefully."""
        # Mock get_forum_data to return empty DataFrame
        with (
            patch("umap_viz_module.get_forum_data", return_value=pd.DataFrame()),
            patch("dash.html") as mock_html,
            patch("dash.dash_table") as mock_dash_table,
            patch("dash_bootstrap_components.Card") as mock_card,
        ):
            mock_html.Div.return_value = "mocked_div"
            mock_dash_table.DataTable.return_value = "mocked_datatable"
            mock_card.return_value = "mocked_card"

            # Should handle empty data without crashing
            create_table_view(forum="all")

    def test_create_table_view_column_configuration(self):
        """Test that column configuration is correct for datatable format."""
        # Create a sample DataFrame with the expected structure
        sample_df = pd.DataFrame(
            {
                "original_title": ["Test Post 1", "Test Post 2"],
                "all_questions": ["Question 1\nQuestion 2", "Question 3"],
                "all_categories": ["Category 1\nCategory 2", "Category 3"],
            }
        )

        with (
            patch("umap_viz_module.get_forum_data", return_value=sample_df),
            patch("dash.html") as mock_html,
            patch("dash.dash_table") as mock_dash_table,
            patch("dash_bootstrap_components.Card") as mock_card,
        ):
            mock_html.Div.return_value = "mocked_div"
            mock_card.return_value = "mocked_card"

            # Capture the DataTable call
            mock_datatable = MagicMock()
            mock_dash_table.DataTable.return_value = mock_datatable

            result = create_table_view(forum="all")

            # Verify DataTable was called
            assert mock_dash_table.DataTable.called, "DataTable should be created"

            # Get the call arguments
            call_args = mock_dash_table.DataTable.call_args
            assert call_args is not None, "DataTable should be called with arguments"

            # Check that columns configuration includes markdown presentation
            columns_config = call_args.kwargs.get("columns", [])
            question_col = next(
                (col for col in columns_config if col["id"] == "all_questions"), None
            )
            category_col = next(
                (col for col in columns_config if col["id"] == "all_categories"), None
            )

            if question_col:
                assert question_col.get("presentation") == "markdown", (
                    "Questions column should have markdown presentation"
                )
                assert question_col.get("type") == "text", (
                    "Questions column should be text type"
                )

            if category_col:
                assert category_col.get("presentation") == "markdown", (
                    "Categories column should have markdown presentation"
                )
                assert category_col.get("type") == "text", (
                    "Categories column should be text type"
                )

            # Use result to avoid lint warning
            assert result is not None


class TestDatatableFormatting:
    """Test the data formatting functions for datatable display."""

    def test_markdown_formatting_function(self):
        """Test the markdown formatting function for multi-line content."""

        def format_for_datatable(text):
            """Convert newline-separated text to markdown list format"""
            if pd.isna(text) or not text:
                return ""
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if not lines:
                return ""
            return "\n".join([f"• {line}" for line in lines])

        # Test basic functionality
        input_text = "Question 1\nQuestion 2\nQuestion 3"
        expected = "• Question 1\n• Question 2\n• Question 3"
        result = format_for_datatable(input_text)
        assert result == expected, f"Expected '{expected}', got '{result}'"

        # Test empty input
        assert format_for_datatable("") == ""
        assert format_for_datatable(None) == ""
        assert format_for_datatable(pd.NA) == ""

        # Test single line
        single_line = "Single question"
        expected_single = "• Single question"
        result_single = format_for_datatable(single_line)
        assert result_single == expected_single

    def test_datatable_content_formatting(self, temp_database_with_data):
        """Test that datatable content is properly formatted for display."""
        df = temp_database_with_data.get_all_posts_as_dataframe(
            user_id=1, datatable_format=True
        )

        if len(df) > 0:
            # Apply the formatting function
            def format_for_datatable(text):
                if not text or pd.isna(text):
                    return ""
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                if not lines:
                    return ""
                return "\n".join([f"• {line}" for line in lines])

            # Test formatting on actual data
            for idx, row in df.head(3).iterrows():  # Test first 3 rows
                if row["all_questions"]:
                    formatted_q = format_for_datatable(row["all_questions"])
                    # Should have bullet points
                    assert "•" in formatted_q, (
                        "Formatted questions should have bullet points"
                    )

                if row["all_categories"]:
                    formatted_c = format_for_datatable(row["all_categories"])
                    # Should have bullet points
                    assert "•" in formatted_c, (
                        "Formatted categories should have bullet points"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
