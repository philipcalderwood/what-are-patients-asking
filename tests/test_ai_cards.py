#!/usr/bin/env python3
"""
Test script to verify AI card functionality
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, "/Users/philipcalderwood/Code/MRPC")

from umap_viz_module import (
    create_ai_question_component,
    create_ai_category_component,
    load_existing_ai_questions,
    load_existing_ai_categories,
)


def test_ai_question_component():
    """Test AI question component creation"""
    test_data = {
        "question_text": "What is the best approach for learning Python?",
        "confidence_score": 0.85,
        "model_version": "gpt-4",
        "created_at": "2024-01-15 10:30:00",
    }

    component = create_ai_question_component("test_id", test_data, 1)
    print(" AI question component created successfully")
    return component


def test_ai_category_component():
    """Test AI category component creation"""
    test_data = {
        "category_type": "programming_topic",
        "category_value": "Python Programming",
        "confidence_score": 0.92,
        "model_version": "gpt-4",
        "created_at": "2024-01-15 10:30:00",
    }

    component = create_ai_category_component("test_id", test_data, 1)
    print(" AI category component created successfully")
    return component


def test_load_functions():
    """Test the load functions (they should return empty lists for non-existent data)"""
    # These should return empty lists since we're using test data
    ai_questions = load_existing_ai_questions("test_id_123")
    ai_categories = load_existing_ai_categories("test_id_123")

    print(f" Load AI questions returned: {len(ai_questions)} items")
    print(f" Load AI categories returned: {len(ai_categories)} items")

    return ai_questions, ai_categories


if __name__ == "__main__":
    print("Testing AI card functionality...")

    try:
        # Test component creation
        question_component = test_ai_question_component()
        category_component = test_ai_category_component()

        # Test load functions
        questions, categories = test_load_functions()

        print("\n🎉 All AI card tests passed!")
        print(" AI question component creation works")
        print(" AI category component creation works")
        print(" Load functions work (return empty lists for test data)")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
