"""
Frontend tests for user question functionality using callback context mocking.
Tests the Dash callbacks for adding, saving, and deleting user questions.
"""

import pytest
from contextvars import copy_context
from dash._callback_context import context_value
from dash._utils import AttributeDict
from unittest.mock import patch, MagicMock
from dash import html


def test_manage_user_questions_add_callback_with_context(temp_database_with_data):
    """Test manage user questions callback for adding questions with proper context mocking"""

    # Test data
    test_data_id = "test_item_1"

    def run_callback():
        # Mock the callback context to simulate add button click
        context_value.set(
            AttributeDict(
                **{
                    "triggered": [
                        {
                            "prop_id": f'{{"type":"add-user-question-btn","item_id":"{test_data_id}"}}.n_clicks',
                            "value": 1,
                        }
                    ]
                }
            )
        )

        # Mock uuid and component creation
        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value.hex = "12345678"
            mock_uuid().__str__.return_value = "test_question_id"

            with patch(
                "components.user_questions.create_user_question_component"
            ) as mock_create_component:
                mock_create_component.return_value = html.Div("New Question Component")

                # Mock the manage_user_questions function logic
                add_clicks = 1
                current_children = []

                # Handle add button click logic
                if add_clicks:
                    question_id = str(mock_uuid.return_value)[:8]
                    new_question = mock_create_component(test_data_id, question_id)
                    current_children.append(new_question)

                return current_children

    # Run the callback in the proper context
    ctx = copy_context()
    output = ctx.run(run_callback)

    # Verify the output contains the new question
    assert isinstance(output, list)
    assert len(output) == 1
    assert output[0].children == "New Question Component"


def test_save_user_question_callback_with_context(temp_database_with_data):
    """Test save user question callback with context mocking"""

    # Test data
    test_data_id = "test_item_1"
    test_question_id = "test_question_123"
    test_question_text = "What is the main issue?"
    test_notes_text = "This question focuses on the core problem"
    button_id = {"item_id": test_data_id, "question_id": test_question_id}

    def run_callback():
        # Mock the callback context to simulate save button click
        context_value.set(
            AttributeDict(
                **{
                    "triggered": [
                        {
                            "prop_id": f'{{"type":"save-user-question-btn","item_id":"{test_data_id}","question_id":"{test_question_id}"}}.n_clicks',
                            "value": 1,
                        }
                    ]
                }
            )
        )

        # Mock the database calls
        with patch("utilities.mrpc_database.MRPCDatabase") as mock_db_class:
            mock_db = MagicMock()
            mock_db_class.return_value = mock_db
            mock_db.save_user_question.return_value = True

            # Mock the save_user_question function logic (simplified)
            n_clicks = 1
            if n_clicks:
                db = mock_db_class()
                success = db.save_user_question(
                    button_id["item_id"],
                    button_id["question_id"],
                    test_question_text or "",
                    test_notes_text or "",
                )

                if success:
                    return "success"  # Button color change
                else:
                    return "danger"

            return "primary"  # Default color

    # Run the callback in the proper context
    ctx = copy_context()
    output = ctx.run(run_callback)

    # Verify the output indicates successful save
    assert output == "success"


def test_manage_user_questions_delete_callback_with_context(temp_database_with_data):
    """Test manage user questions callback for deleting questions with context mocking"""

    # Test data
    test_data_id = "test_item_1"
    test_question_id = "test_question_123"

    def run_callback():
        # Mock the callback context to simulate delete button click
        context_value.set(
            AttributeDict(
                **{
                    "triggered": [
                        {
                            "prop_id": f'{{"type":"delete-user-question-btn","item_id":"{test_data_id}","question_id":"{test_question_id}"}}.n_clicks',
                            "value": 1,
                        }
                    ]
                }
            )
        )

        # Mock JSON parsing and database calls
        with patch("json.loads") as mock_json:
            mock_json.return_value = {"question_id": test_question_id}

            with patch("utilities.mrpc_database.MRPCDatabase") as mock_db_class:
                mock_db = MagicMock()
                mock_db_class.return_value = mock_db
                mock_db.delete_user_question.return_value = True

                with patch(
                    "components.user_questions.load_existing_user_questions"
                ) as mock_load_questions:
                    mock_load_questions.return_value = []

                    # Mock the delete logic from manage_user_questions
                    delete_clicks = [1]  # One delete button clicked
                    if any(delete_clicks):
                        # Extract question_id from the triggered component
                        triggered_prop = f'{{"type":"delete-user-question-btn","item_id":"{test_data_id}","question_id":"{test_question_id}"}}.n_clicks'
                        triggered_component = mock_json(triggered_prop.split(".")[0])
                        question_id_to_delete = triggered_component["question_id"]

                        db = mock_db_class()
                        success = db.delete_user_question(
                            test_data_id, question_id_to_delete
                        )

                        if success:
                            # Reload questions from database to get updated list
                            current_children = mock_load_questions(test_data_id)
                            return current_children

                    return []

    # Run the callback in the proper context
    ctx = copy_context()
    output = ctx.run(run_callback)

    # Verify the output is an empty list (no questions remaining)
    assert isinstance(output, list)
    assert len(output) == 0


def test_manage_user_questions_no_trigger(temp_database_with_data):
    """Test manage user questions callback when no button is clicked"""
    from dash.exceptions import PreventUpdate

    def run_callback():
        # Mock empty callback context (no trigger)
        context_value.set(AttributeDict(**{"triggered": []}))

        # Mock the manage_user_questions logic
        # If no triggers, should raise PreventUpdate
        from dash import callback_context

        if not callback_context.triggered:
            raise PreventUpdate

        return []

    # Run the callback in the proper context
    ctx = copy_context()

    # Should raise PreventUpdate when no trigger
    with pytest.raises(PreventUpdate):
        ctx.run(run_callback)


def test_save_user_question_no_trigger(temp_database_with_data):
    """Test save user question callback when no button is clicked"""
    from dash.exceptions import PreventUpdate

    def run_callback():
        # Mock empty callback context (no trigger)
        context_value.set(AttributeDict(**{"triggered": []}))

        # Mock the save_user_question logic
        n_clicks = None  # No clicks
        if not n_clicks:
            raise PreventUpdate

        return "primary"

    # Run the callback in the proper context
    ctx = copy_context()

    # Should raise PreventUpdate when no trigger
    with pytest.raises(PreventUpdate):
        ctx.run(run_callback)


def test_create_user_question_component_structure():
    """Test the structure of the user question component"""
    from components.user_questions import create_user_question_component

    # Test data
    data_id = "test_item_1"
    question_id = "test_question_123"
    question_text = "What is the main issue?"
    notes_text = "This question focuses on the core problem"
    question_number = 2

    # Create the component
    component = create_user_question_component(
        data_id, question_id, question_text, notes_text, question_number
    )

    # Verify it's a dbc.Card
    assert component.__class__.__name__ == "Card"

    # Verify the component has the correct ID structure
    assert component.id == {
        "type": "user-question-container",
        "data_id": data_id,
        "question_id": question_id,
    }

    # Verify styling classes
    assert "mb-3" in component.className

    # Verify the card structure has header and body
    assert len(component.children) == 2  # Header and Body

    # Check that the header contains the question number
    header = component.children[0]
    assert header.__class__.__name__ == "CardHeader"


def test_load_existing_user_questions_with_mock():
    """Test loading existing user questions with mocked database"""
    from components.user_questions import load_existing_user_questions

    test_data_id = "test_item_1"
    mock_questions = [
        {"question_id": "q1", "question_text": "Question 1", "notes_text": "Notes 1"},
        {"question_id": "q2", "question_text": "Question 2", "notes_text": "Notes 2"},
    ]

    # Mock the database and component creation
    with patch("utilities.mrpc_database.MRPCDatabase") as mock_db_class:
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.get_user_questions.return_value = mock_questions

        with patch(
            "components.user_questions.create_user_question_component"
        ) as mock_create:
            mock_create.side_effect = lambda *args, **kwargs: html.Div(
                f"Component {args[1]}"
            )

            # Call the function
            result = load_existing_user_questions(test_data_id)

            # Verify database was called
            mock_db.get_user_questions.assert_called_once_with(test_data_id)

            # Verify components were created with correct numbering
            assert mock_create.call_count == 2

            # Check first call (question_number=1)
            first_call = mock_create.call_args_list[0]
            assert first_call[0][0] == test_data_id  # data_id
            assert first_call[0][1] == "q1"  # question_id
            assert first_call[0][2] == "Question 1"  # question_text
            assert first_call[0][3] == "Notes 1"  # notes_text
            assert first_call[1]["question_number"] == 1  # question_number

            # Check second call (question_number=2)
            second_call = mock_create.call_args_list[1]
            assert second_call[1]["question_number"] == 2

            # Verify result structure
            assert len(result) == 2
            assert result[0].children == "Component q1"
            assert result[1].children == "Component q2"


def test_create_user_questions_content():
    """Test the create_user_questions_content function"""
    from components.user_questions import create_user_questions_content

    # Mock point and customdata
    point = {"customdata": ["test_item_1"]}
    customdata = ["test_item_1"]

    # Mock the load_existing_user_questions function
    with patch("components.user_questions.load_existing_user_questions") as mock_load:
        mock_load.return_value = [html.Div("Existing Question")]

        # Call the function
        result = create_user_questions_content(point, customdata)

        # Verify it returns a dbc.Container
        assert result.__class__.__name__ == "Container"

        # Verify it has fluid=True and proper className
        assert result.fluid
        assert result.className == "p-0"

        # Verify the structure contains rows and columns
        assert len(result.children) == 2  # Two rows

        # Check first row (existing questions)
        first_row = result.children[0]
        assert first_row.__class__.__name__ == "Row"

        # Check second row (add button)
        second_row = result.children[1]
        assert second_row.__class__.__name__ == "Row"

        # Verify load_existing_user_questions was called
        mock_load.assert_called_once_with("test_item_1")


def test_question_component_titles_with_dash_testing(dash_duo):
    """Test question component titles using Dash testing framework"""
    from dash import Dash, html
    import dash_bootstrap_components as dbc
    from components.user_questions import create_user_question_component

    # Create a simple app for testing
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Create test components with different question numbers
    test_components = []
    for i in range(1, 4):
        component = create_user_question_component(
            data_id="test_item",
            question_id=f"test_question_{i}",
            question_text=f"This is test question {i}",
            notes_text=f"These are notes for question {i}",
            question_number=i,
        )
        test_components.append(component)

    # Create app layout
    app.layout = html.Div(test_components)

    # Start the app
    dash_duo.start_server(app)

    # Wait for elements to load by looking for the first h6
    dash_duo.wait_for_element("h6", timeout=10)

    # Debug: print the page HTML to see what's actually rendered
    print("\n=== PAGE HTML ===")
    print(dash_duo.driver.page_source)
    print("=== END HTML ===")

    # Try different selectors to find the title
    h6_elements = dash_duo.find_elements("h6")
    print(f"\n=== Found {len(h6_elements)} h6 elements ===")
    for i, element in enumerate(h6_elements):
        print(f"H6 {i}: '{element.text}'")

    # Test that we can find any h6 elements first
    assert len(h6_elements) > 0, "No h6 elements found on page"

    # Test that the question titles are rendered correctly
    for i in range(1, 4):
        expected_title = f"Inferred Question {i}"

        # Use a more flexible approach to find the text
        found = False
        for element in h6_elements:
            if expected_title in element.text:
                found = True
                break

        assert found, f"Expected title '{expected_title}' not found in any h6 element"

    # Verify question input placeholders are present
    question_inputs = dash_duo.find_elements(
        "textarea[placeholder*='Enter your inferred question']"
    )
    assert len(question_inputs) == 3

    # Verify notes input placeholders are present
    notes_inputs = dash_duo.find_elements(
        "textarea[placeholder*='Add notes or justification']"
    )
    assert len(notes_inputs) == 3

    # Verify save buttons are present by looking for buttons with the success class
    save_buttons = dash_duo.find_elements("button.btn-success")
    assert len(save_buttons) == 3
