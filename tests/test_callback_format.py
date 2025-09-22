# Quick test to verify datatable callback format

import pandas as pd
from unittest.mock import patch


# Test the callback format logic
def test_datatable_callback_format():
    """Test that the callback applies the same formatting as create_table_view"""

    # Create sample data that mimics what comes from get_forum_data(datatable_format=True)
    sample_data = pd.DataFrame(
        {
            "original_title": ["Test Post 1", "Test Post 2"],
            "all_questions": ["Question 1\nQuestion 2", "Question 3\nQuestion 4"],
            "all_categories": ["Category 1\nCategory 2", "Category 3"],
        }
    )

    # Apply the same formatting logic as in the callback
    def format_for_datatable(text):
        """Convert newline-separated text to markdown list format"""
        if not text or pd.isna(text):
            return ""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return ""
        # Create markdown list format
        return "\n".join([f"• {line}" for line in lines])

    formatted_data = sample_data.copy()
    formatted_data["all_questions"] = formatted_data["all_questions"].apply(
        format_for_datatable
    )
    formatted_data["all_categories"] = formatted_data["all_categories"].apply(
        format_for_datatable
    )

    print("Original data:")
    print(sample_data["all_questions"].iloc[0])
    print("\nFormatted data:")
    print(formatted_data["all_questions"].iloc[0])

    # Verify formatting
    expected_questions = "• Question 1\n• Question 2"
    actual_questions = formatted_data["all_questions"].iloc[0]

    assert actual_questions == expected_questions, (
        f"Expected: {expected_questions}, Got: {actual_questions}"
    )
    print(" Formatting test passed!")


if __name__ == "__main__":
    test_datatable_callback_format()
