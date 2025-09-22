from dash import (
    callback_context,
    MATCH,
    ALL,
    Output,
    Input,
    State,
    html,
    callback,
    no_update,
)
import pandas as pd
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from utilities.backend import get_forum_data
from components.ai_categories_section_card import load_existing_ai_categories
from components.ai_questions_section_card import load_existing_ai_questions
from components.combined_card import create_review_content_card
from services.table_view import create_table_view
from components.basic_metadata_content import create_basic_metadata_content
from components.unified_user_card import create_unified_user_card
from utilities.backend import load_existing_feedback, save_feedback_to_db
import uuid
import json


def create_unified_user_content(data_id):
    """Create unified user content combining questions and topics using unified cards"""
    from utilities.mrpc_database import MRPCDatabase

    print(f"🔍 DEBUG: Creating unified content for data_id: {data_id}")

    try:
        db = MRPCDatabase()

        # Load existing user questions from database
        existing_questions = db.get_user_questions(data_id)
        # Load existing user topics from database
        existing_topics = db.get_category_notes(data_id)

        print(
            f"🔍 DEBUG: Found {len(existing_questions)} questions and {len(existing_topics)} topics"
        )

        unified_cards = []

        # Convert user questions to unified cards
        for index, question_data in enumerate(existing_questions):
            question_id = question_data["question_id"]
            print(f"🔍 DEBUG: Creating question card for question_id: {question_id}")
            unified_cards.append(
                create_unified_user_card(
                    data_id=data_id,
                    item_id=question_id,
                    card_type="question",
                    content_text=question_data.get("question_text", ""),
                    notes_text=question_data.get("notes_text", ""),
                    card_number=index + 1,
                    mode="display",
                )
            )

        # Convert user topics to unified cards
        for index, topic_data in enumerate(existing_topics):
            topic_id = topic_data["note_id"]
            print(f"🔍 DEBUG: Creating topic card for topic_id: {topic_id}")
            unified_cards.append(
                create_unified_user_card(
                    data_id=data_id,
                    item_id=topic_id,
                    card_type="topic",
                    content_text=topic_data.get("notes_text", ""),
                    notes_text="",
                    card_number=len(existing_questions) + index + 1,
                    mode="display",
                )
            )

        # Add "Add New Question" button card
        add_question_card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        dbc.Button(
                            [
                                html.I(className="fas fa-plus me-2"),
                                "Add New Question",
                            ],
                            id={
                                "type": "add-user-question-btn",
                                "item_id": data_id,
                            },
                            color="primary",
                            outline=True,
                            size="sm",
                            className="w-100",
                        ),
                    ],
                    className="p-3 text-center",
                ),
            ],
            className="mb-3 shadow-sm border-dashed",
            style={"border-style": "dashed"},
        )

        # Add "Add New Topic" button card
        add_topic_card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        dbc.Button(
                            [
                                html.I(className="fas fa-plus me-2"),
                                "Add New Topic",
                            ],
                            id={
                                "type": "add-user-topic-btn",
                                "item_id": data_id,
                            },
                            color="success",
                            outline=True,
                            size="sm",
                            className="w-100",
                        ),
                    ],
                    className="p-3 text-center",
                ),
            ],
            className="mb-0 shadow-sm border-dashed",
        )

        # Return all cards: existing unified cards + add buttons
        return unified_cards + [add_question_card, add_topic_card]

    except Exception as e:
        print(f"❌ Error creating unified user content: {e}")
        return []


def register_umap_callback(app):
    # Table Controls Modal Callbacks
    @app.callback(
        Output("table-controls-modal", "is_open"),
        [
            Input("table-controls-modal-btn", "n_clicks"),
            Input("table-controls-modal-close", "n_clicks"),
        ],
        [State("table-controls-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_table_controls_modal(open_clicks, close_clicks, is_open):
        """Toggle table controls modal open/closed"""
        ctx = callback_context
        if not ctx.triggered:
            return is_open

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id in ["table-controls-modal-btn", "table-controls-modal-close"]:
            return not is_open

        return is_open

    @app.callback(
        [
            Output("main-view-content", "children"),
            Output("click-info", "children"),
            Output("click-info", "style"),
            Output("table-controls-section", "style"),  # Add table controls visibility
        ],
        [
            Input("table-forum-selector", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_main_view(selected_forum):
        """Handle forum changes - always show table view"""
        from dash.exceptions import PreventUpdate

        # Check if we're on the correct page by seeing if the inputs have values
        # If inputs are None, we're probably not on the Forum Explorer page
        if selected_forum is None:
            raise PreventUpdate

        # Default placeholder content for metadata
        placeholder_style = {
            "margin-top": "0.6rem",
            "padding": "0.6rem",
            "border": "1px solid #ddd",
            "border-radius": "0.3rem",
            "background-color": "#f9f9f9",
            "height": "10.5rem",  # Increased from 8rem by one third
            "overflow-y": "auto",
            "display": "block",
            "box-sizing": "border-box",
        }

        # Always show table view since view selector is removed
        main_content = create_table_view()
        # Hide the separate click-info div for table view by setting display: none
        hidden_style = {**placeholder_style, "display": "none"}
        # Show table controls for table view
        table_controls_style = {"display": "block"}

        return (
            main_content,
            [],  # Empty children for hidden click-info
            hidden_style,
            table_controls_style,
        )

    @app.callback(
        [
            Output("sidebar-reading-pane", "children"),
            Output("basic-metadata-content", "children"),
            Output("ai-question-content", "children"),
            Output("ai-categories-content", "children"),
            Output("user-questions-content", "children"),
            Output("user-topics-content", "children"),
        ],
        [Input("forum-data-table", "active_cell")],
        [State("forum-data-table", "data")],
        prevent_initial_call=True,
    )
    def handle_table_selection(active_cell, table_data):
        """Handle table cell click to update reading pane and all metadata cards"""

        if not active_cell or not table_data:
            # Return default placeholders for all components

            placeholder_sidebar_reading = [
                html.P(
                    "Select a row to read the original post",
                    className="text-muted text-center font-italic",
                    style={"margin": "2rem 0", "font-size": "0.8rem"},
                )
            ]

            placeholder_basic = [
                html.P(
                    "Click on a row to see basic metadata",
                    className="text-muted text-center font-italic",
                    style={"margin": "1rem 0", "font-size": "0.8rem"},
                )
            ]

            placeholder_inferred = [
                html.P(
                    "Click on a row to see AI inferred data",
                    className="text-muted text-center font-italic",
                    style={"margin": "1rem 0", "font-size": "0.8rem"},
                )
            ]

            placeholder_questions = [
                html.P(
                    "Click on a row to manage user questions",
                    className="text-muted text-center font-italic",
                    style={"margin": "1rem 0", "font-size": "0.8rem"},
                )
            ]

            placeholder_topics = [
                html.P(
                    "Click on a row to manage user topics",
                    className="text-muted text-center font-italic",
                    style={"margin": "1rem 0", "font-size": "0.8rem"},
                )
            ]

            return (
                placeholder_sidebar_reading,
                placeholder_basic,
                placeholder_inferred,
                placeholder_inferred,
                placeholder_questions,
                placeholder_topics,
            )

        # Get selected row data from active cell
        selected_row_index = active_cell["row"]
        if selected_row_index >= len(table_data):
            # Invalid row index, return placeholders
            placeholder_reading_pane = []
            placeholder_sidebar_reading = [
                html.P(
                    "Invalid row selection",
                    className="text-muted text-center font-italic",
                    style={"margin": "2rem 0", "font-size": "0.8rem"},
                )
            ]
            placeholder_basic = [
                html.P(
                    "Invalid row selection",
                    className="text-muted text-center font-italic",
                    style={"margin": "1rem 0", "font-size": "0.8rem"},
                )
            ]
            placeholder_inferred = [
                html.P(
                    "Invalid row selection",
                    className="text-muted text-center font-italic",
                    style={"margin": "1rem 0", "font-size": "0.8rem"},
                )
            ]
            placeholder_questions = [
                html.P(
                    "Invalid row selection",
                    className="text-muted text-center font-italic",
                    style={"margin": "1rem 0", "font-size": "0.8rem"},
                )
            ]
            placeholder_topics = [
                html.P(
                    "Invalid row selection",
                    className="text-muted text-center font-italic",
                    style={"margin": "1rem 0", "font-size": "0.8rem"},
                )
            ]
            return (
                placeholder_reading_pane,
                placeholder_sidebar_reading,
                placeholder_basic,
                placeholder_inferred,
                placeholder_inferred,
                placeholder_questions,
                placeholder_topics,
            )

        row_data = table_data[selected_row_index]

        # Create reading pane content with original post
        original_post = row_data.get("original_post", "No original post available")

        # Convert row_data to customdata format expected by metadata functions
        customdata = [
            row_data.get("id", "N/A"),  # index 0
            row_data.get("forum", "N/A"),  # index 1
            row_data.get("post_type", "N/A"),  # index 2
            row_data.get("username", "N/A"),  # index 3
            row_data.get("original_title", "N/A"),  # index 4
            row_data.get("post_url", "N/A"),  # index 5
            row_data.get("LLM_inferred_question", "N/A"),  # index 6
            row_data.get("cluster", "N/A"),  # index 7
            row_data.get("cluster_label", "N/A"),  # index 8
            row_data.get("date_posted", "N/A"),  # index 9
            row_data.get("llm_cluster_name", "N/A"),  # index 10
            row_data.get("original_post", "N/A"),  # index 11
            row_data.get("tag_group", "N/A"),  # index 12
            row_data.get("tag_subgroup", "N/A"),  # index 13
            row_data.get("tag_name", "N/A"),  # index 14
            row_data.get("tag_source", "N/A"),  # index 15
            row_data.get("tag_confidence", "N/A"),  # index 16
            row_data.get("tag_hierarchy_path", "N/A"),  # index 17
            row_data.get("enhanced_tags", "N/A"),  # index 18
        ]

        # Create a mock point object for compatibility
        mock_point = {
            "x": 0,
            "y": 0,
            "z": 0,
            "fullData": {"name": f"Cluster {row_data.get('cluster', 'Unknown')}"},
        }

        # Create content for each metadata card separately
        basic_metadata = create_basic_metadata_content(mock_point, customdata)

        # Extract data for separate AI components
        data_id = customdata[0] if len(customdata) > 0 else "unknown"

        # Load AI questions from database as individual cards
        ai_question_cards = load_existing_ai_questions(data_id)

        # If no AI questions in database, fallback to legacy inferred question
        if not ai_question_cards:
            inferred_question = customdata[6] if len(customdata) > 6 else "N/A"
            if inferred_question and inferred_question != "N/A":
                fallback_ai_question = create_review_content_card(
                    data_id=data_id,
                    content_type="LLM_inferred_question",
                    display_label="AI Inferred Question",
                    value=inferred_question,
                    card_type="ai_feedback",
                )
                ai_question_cards = [fallback_ai_question]
            else:
                ai_question_cards = [
                    html.P(
                        "No AI questions available",
                        className="text-muted text-center font-italic",
                        style={"margin": "1rem 0", "font-size": "0.8rem"},
                    )
                ]

        # Load AI categories from database as individual cards
        ai_category_cards = load_existing_ai_categories(data_id)

        # If no AI categories in database, fallback to legacy category
        if not ai_category_cards:
            legacy_category = customdata[10] if len(customdata) > 10 else "N/A"
            tag_hierarchy_path = customdata[17] if len(customdata) > 17 else "N/A"

            if (
                tag_hierarchy_path
                and tag_hierarchy_path != "N/A"
                and str(tag_hierarchy_path).strip()
            ):
                display_category = tag_hierarchy_path
                feedback_key = "tag_hierarchy_path"
            else:
                display_category = legacy_category
                feedback_key = "llm_cluster_name"

            if display_category and display_category != "N/A":
                fallback_ai_category = create_review_content_card(
                    data_id=data_id,
                    content_type=feedback_key,
                    display_label="AI Inferred Category",
                    value=display_category,
                    card_type="ai_feedback",
                )
                ai_category_cards = [fallback_ai_category]
            else:
                ai_category_cards = [
                    html.P(
                        "No AI categories available",
                        className="text-muted text-center font-italic",
                        style={"margin": "1rem 0", "font-size": "0.8rem"},
                    )
                ]

        # Create unified user content (questions + topics)
        unified_user_content = create_unified_user_content(data_id)

        # Create sidebar reading pane content
        post_id = row_data.get("id", "unknown")
        original_post = row_data.get("original_post", "No original post available")
        sidebar_reading_content = [
            html.Div(
                [
                    html.Pre(
                        original_post,
                        id=f"sidebar-content-{post_id}",
                        style={
                            "border": "none",
                            "white-space": "normal",
                            "word-wrap": "wrap",
                            "overflow-y": "auto",
                            "font-family": "inherit",
                            "font-size": "1.2rem",
                            "line-height": "1.5",
                        },
                    )
                ]
            )
        ]

        return (
            sidebar_reading_content,
            basic_metadata,
            ai_question_cards,
            ai_category_cards,
            unified_user_content,  # This replaces user_questions
            [],  # Empty list for user_topics since we're now unified
        )

    # @app.callback(
    #     Output("forum-data-table", "style_data_conditional"),
    #     [Input("forum-data-table", "active_cell")],
    #     prevent_initial_call=False,
    # )
    # def highlight_active_row(active_cell):
    #     """Highlight the active row when a cell is clicked"""

    #     # We're always in table view now since view selector is removed

    #     # Base conditional styling - simple column styling
    #     base_styling = [
    #         {
    #             "if": {"column_id": "cluster_label"},
    #             "maxWidth": "15.625rem",
    #             "overflow": "hidden",
    #             "textOverflow": "ellipsis",
    #         },
    #         {
    #             "if": {"column_id": "LLM_inferred_question"},
    #             "maxWidth": "18.75rem",
    #             "overflow": "hidden",
    #             "textOverflow": "ellipsis",
    #         },
    #         {
    #             "if": {"column_id": "llm_cluster_name"},
    #             "maxWidth": "12rem",
    #             "overflow": "hidden",
    #             "textOverflow": "ellipsis",
    #         },
    #     ]

    #     # Add row highlighting if a cell is active
    #     if active_cell:
    #         active_row = active_cell["row"]
    #         base_styling.append(
    #             {
    #                 "if": {"row_index": active_row},
    #                 "backgroundColor": "#e3f2fd",
    #                 "border": "2px solid #2196f3",
    #             }
    #         )

    #     return base_styling

    @callback(
        [
            Output("forum-data-table", "data"),
            Output("forum-data-table", "page_count"),
        ],
        [
            Input("forum-data-table", "filter_query"),
            Input("forum-data-table", "sort_by"),
            Input("forum-data-table", "page_current"),
            Input("table-forum-selector", "value"),
            Input("table-topic-selector", "value"),
        ],
        allow_duplicate=True,
    )
    def update_table_data(
        filter_query, sort_by, page_current, selected_forum, selected_topic
    ):
        """Handle custom filtering, sorting, and pagination for the data table"""
        # Get the full dataset with datatable format for aggregated questions/categories
        df = get_forum_data(selected_forum, datatable_format=True)

        # Start with full dataframe
        filtered_df = df.copy()

        # Apply topic filtering if topics are selected
        if selected_topic and selected_topic != "all":
            filtered_df = filtered_df[
                filtered_df["llm_cluster_name"].isin(selected_topic)
            ]

        # Apply filtering if filter_query exists
        if filter_query:
            print(f"DEBUG: Filter query received: '{filter_query}'")  # Debug output
            try:
                # Parse the filter query - Dash uses a specific format
                # Support for various filter operations
                filtering_expressions = filter_query.split(" && ")
                for expr in filtering_expressions:
                    expr = expr.strip()
                    print(
                        f"DEBUG: Processing filter expression: '{expr}'"
                    )  # Debug output

                    if " scontains " in expr:
                        col, value = expr.split(" scontains ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            print(
                                f"DEBUG: Applying scontains filter - Column: {col}, Value: {value}"
                            )
                            filtered_df = filtered_df[
                                filtered_df[col]
                                .astype(str)
                                .str.contains(value, case=False, na=False, regex=False)
                            ]
                    elif " contains " in expr:
                        col, value = expr.split(" contains ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            print(
                                f"DEBUG: Applying contains filter - Column: {col}, Value: {value}"
                            )
                            filtered_df = filtered_df[
                                filtered_df[col]
                                .astype(str)
                                .str.contains(value, case=False, na=False, regex=False)
                            ]
                    elif " icontains " in expr:
                        col, value = expr.split(" icontains ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            print(
                                f"DEBUG: Applying icontains filter - Column: {col}, Value: {value}"
                            )
                            filtered_df = filtered_df[
                                filtered_df[col]
                                .astype(str)
                                .str.contains(value, case=False, na=False, regex=False)
                            ]
                    elif " eq " in expr:
                        col, value = expr.split(" eq ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            print(
                                f"DEBUG: Applying eq filter - Column: {col}, Value: {value}"
                            )
                            filtered_df = filtered_df[
                                filtered_df[col].astype(str).str.lower()
                                == value.lower()
                            ]
                    elif " ne " in expr:
                        col, value = expr.split(" ne ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            print(
                                f"DEBUG: Applying ne filter - Column: {col}, Value: {value}"
                            )
                            filtered_df = filtered_df[
                                filtered_df[col].astype(str).str.lower()
                                != value.lower()
                            ]
                    elif " gt " in expr:
                        col, value = expr.split(" gt ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            try:
                                # Try numeric comparison first
                                numeric_value = float(value)
                                print(
                                    f"DEBUG: Applying numeric gt filter - Column: {col}, Value: {numeric_value}"
                                )
                                filtered_df = filtered_df[
                                    pd.to_numeric(filtered_df[col], errors="coerce")
                                    > numeric_value
                                ]
                            except ValueError:
                                # Fall back to string comparison
                                print(
                                    f"DEBUG: Applying string gt filter - Column: {col}, Value: {value}"
                                )
                                filtered_df = filtered_df[
                                    filtered_df[col].astype(str) > value
                                ]
                    elif " lt " in expr:
                        col, value = expr.split(" lt ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            try:
                                # Try numeric comparison first
                                numeric_value = float(value)
                                print(
                                    f"DEBUG: Applying numeric lt filter - Column: {col}, Value: {numeric_value}"
                                )
                                filtered_df = filtered_df[
                                    pd.to_numeric(filtered_df[col], errors="coerce")
                                    < numeric_value
                                ]
                            except ValueError:
                                # Fall back to string comparison
                                print(
                                    f"DEBUG: Applying string lt filter - Column: {col}, Value: {value}"
                                )
                                filtered_df = filtered_df[
                                    filtered_df[col].astype(str) < value
                                ]
                    elif " ge " in expr:
                        col, value = expr.split(" ge ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            try:
                                # Try numeric comparison first
                                numeric_value = float(value)
                                print(
                                    f"DEBUG: Applying numeric ge filter - Column: {col}, Value: {numeric_value}"
                                )
                                filtered_df = filtered_df[
                                    pd.to_numeric(filtered_df[col], errors="coerce")
                                    >= numeric_value
                                ]
                            except ValueError:
                                # Fall back to string comparison
                                print(
                                    f"DEBUG: Applying string ge filter - Column: {col}, Value: {value}"
                                )
                                filtered_df = filtered_df[
                                    filtered_df[col].astype(str) >= value
                                ]
                    elif " le " in expr:
                        col, value = expr.split(" le ", 1)
                        col = col.strip("{}")
                        value = value.strip("\"'")
                        if col in filtered_df.columns:
                            try:
                                # Try numeric comparison first
                                numeric_value = float(value)
                                print(
                                    f"DEBUG: Applying numeric le filter - Column: {col}, Value: {numeric_value}"
                                )
                                filtered_df = filtered_df[
                                    pd.to_numeric(filtered_df[col], errors="coerce")
                                    <= numeric_value
                                ]
                            except ValueError:
                                # Fall back to string comparison
                                print(
                                    f"DEBUG: Applying string le filter - Column: {col}, Value: {value}"
                                )
                                filtered_df = filtered_df[
                                    filtered_df[col].astype(str) <= value
                                ]
                print(f"DEBUG: After filtering, {len(filtered_df)} rows remain")
            except Exception as e:
                # If filtering fails, return original data
                print(f"Filter error: {e}")  # For debugging
                pass

        # Apply sorting if sort_by exists - supports multiple column sorting
        if sort_by:
            # Build list of columns and directions for multi-column sorting
            sort_columns = []
            sort_directions = []

            for sort_item in sort_by:
                col = sort_item["column_id"]
                direction = sort_item["direction"] == "asc"

                if col in filtered_df.columns:
                    sort_columns.append(col)
                    sort_directions.append(direction)

            if sort_columns:
                # Apply multi-column sorting
                filtered_df = filtered_df.sort_values(
                    by=sort_columns,
                    ascending=sort_directions,
                    na_position="last",  # Put NaN values at the end
                )

        # No pagination - show all filtered results
        page_count = 1  # Only one page since we show everything
        paginated_df = filtered_df.copy()  # Use all filtered data

        # Apply markdown formatting for datatable display (same as in create_table_view)
        if (
            "all_questions" in paginated_df.columns
            and "all_categories" in paginated_df.columns
        ):

            def format_for_datatable(text):
                """Convert newline-separated text to markdown list format"""
                if not text or pd.isna(text):
                    return ""
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                if not lines:
                    return ""
                # Create markdown list format
                return "\n".join([f"• {line}" for line in lines])

            paginated_df["all_questions"] = paginated_df["all_questions"].apply(
                format_for_datatable
            )
            paginated_df["all_categories"] = paginated_df["all_categories"].apply(
                format_for_datatable
            )

        return (
            paginated_df.to_dict("records"),
            page_count,
        )

    @app.callback(
        [
            Output("forum-data-table", "page_current"),
            Output("page-info", "children"),
        ],
        [
            Input("page-first-btn", "n_clicks"),
            Input("page-prev-btn", "n_clicks"),
            Input("page-next-btn", "n_clicks"),
            Input("page-last-btn", "n_clicks"),
        ],
        [
            State("forum-data-table", "page_current"),
            State("forum-data-table", "page_size"),
            State("forum-data-table", "page_count"),
        ],
        prevent_initial_call=True,
    )
    def update_pagination(
        first_clicks,
        prev_clicks,
        next_clicks,
        last_clicks,
        current_page,
        page_size,
        page_count,
    ):
        """Handle pagination button clicks"""

        # We're always in table view now since view selector is removed

        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Handle None values safely
        page_count = page_count or 1
        current_page = current_page or 0

        # Use the page_count directly from DataTable
        total_pages = max(1, page_count)

        # Determine which button was clicked
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        new_page = current_page
        if button_id == "page-first-btn":
            new_page = 0
        elif button_id == "page-prev-btn":
            new_page = max(0, current_page - 1)
        elif button_id == "page-next-btn":
            new_page = min(total_pages - 1, current_page + 1)
        elif button_id == "page-last-btn":
            new_page = total_pages - 1

        # Update page info display
        page_info = f"Page {new_page + 1} of {total_pages}"

        return new_page, page_info

    @app.callback(
        Output("page-info", "children", allow_duplicate=True),
        [Input("forum-data-table", "page_count")],  # Use page_count instead
        [
            State("forum-data-table", "page_current"),
        ],
        prevent_initial_call=True,
    )
    def update_page_info_on_data_change(page_count, current_page):
        """Update page info when table data changes"""

        # We're always in table view now since view selector is removed

        # Handle None values safely
        page_count = page_count or 1
        current_page = current_page or 0

        total_pages = max(1, page_count)
        return f"Page {current_page + 1} of {total_pages}"

    @app.callback(
        Output("export-csv-btn", "n_clicks"),
        [Input("export-csv-btn", "n_clicks")],
        [State("table-forum-selector", "value")],
        prevent_initial_call=True,
    )
    def export_full_csv(n_clicks, selected_forum):
        """Export the full dataset as CSV"""
        if n_clicks and n_clicks > 0:
            df = get_forum_data(selected_forum)

            # Remove UMAP coordinates and original_post for cleaner export
            umap_columns = [
                "umap_x",
                "umap_y",
                "umap_z",
                "umap_1",
                "umap_2",
                "umap_3",
                "original_post",
            ]
            export_df = df.drop(
                columns=[col for col in umap_columns if col in df.columns],
                errors="ignore",
            )

            # Generate filename
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"forum_data_export_{timestamp}.csv"

            # This would typically trigger a download in a real app
            # For now, we'll just save to the data directory
            export_path = f"data/{filename}"
            export_df.to_csv(export_path, index=False)

            print(f"Full dataset exported to: {export_path}")

        return 0  # Reset button clicks

    @app.callback(
        Output("export-filtered-btn", "n_clicks"),
        [Input("export-filtered-btn", "n_clicks")],
        [
            State("forum-data-table", "derived_virtual_data"),
            State("table-forum-selector", "value"),
        ],
        prevent_initial_call=True,
    )
    def export_filtered_csv(n_clicks, table_data, selected_forum):
        """Export the currently filtered/displayed data as CSV"""
        if n_clicks and n_clicks > 0 and table_data:
            import pandas as pd
            import datetime

            # Convert table data back to DataFrame
            filtered_df = pd.DataFrame(table_data)

            # Generate filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"forum_data_filtered_export_{timestamp}.csv"

            # Save to data directory
            export_path = f"data/{filename}"
            filtered_df.to_csv(export_path, index=False)

            print(
                f"Filtered dataset exported to: {export_path} ({len(filtered_df)} rows)"
            )

        return 0  # Reset button clicks

    @app.callback(
        [
            Output(
                {
                    "type": "feedback-collapse",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "is_open",
            ),
            Output(
                {
                    "type": "feedback-container",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "style",
            ),
            Output(
                {
                    "type": "feedback-status",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "children",
            ),
            Output(
                {
                    "type": "feedback-buttons-container",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "children",
            ),
            Output(
                {
                    "type": "feedback-display-container",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "children",
            ),
            Output(
                {
                    "type": "feedback-submit-spinner",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "spinner_style",
            ),
            Output(
                {
                    "type": "feedback-submit-icon",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "style",
            ),
            Output(
                {
                    "type": "feedback-submit-text",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "children",
            ),
            Output(
                {
                    "type": "feedback-text-submit",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "disabled",
            ),
        ],
        [
            Input(
                {
                    "type": "feedback-btn",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "rating": "positive",
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "feedback-btn",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "rating": "negative",
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "feedback-text-only-btn",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "feedback-text-submit",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
        ],
        [
            State(
                {
                    "type": "feedback-btn",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "rating": "positive",
                    "response_id": MATCH,
                },
                "id",
            ),
            State(
                {
                    "type": "feedback-text",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "value",
            ),
        ],
        prevent_initial_call=True,
    )
    def handle_feedback_rating(
        positive_clicks,
        negative_clicks,
        comment_clicks,
        submit_clicks,
        button_id,
        feedback_text,
    ):
        """Handle feedback rating button clicks and comment submissions"""
        from dash import html, no_update
        import dash_bootstrap_components as dbc

        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Get the triggered button information from context
        button_id_clicked = ctx.triggered[0]["prop_id"]

        # Parse the button ID from the triggered component
        if not button_id_clicked or button_id_clicked == ".":
            raise PreventUpdate

        # The button_id parameter will be from the triggered component
        if button_id is None:
            raise PreventUpdate

        # Get button information
        data_id = button_id["data_id"]
        inference_type = button_id["inference_type"]
        response_id = button_id["response_id"]

        # Handle comment submission (different logic than rating buttons)
        if "feedback-text-submit" in button_id_clicked and submit_clicks:
            if not feedback_text or not feedback_text.strip():
                raise PreventUpdate

            # For comment submissions, always use "text_update" to ensure the text gets saved
            # The save_inference_feedback method will preserve any existing rating automatically
            rating_to_use = "text_update"

            print(
                f"🔧 Comment submission debug: data_id={data_id}, rating_to_use={rating_to_use}, feedback_text='{feedback_text.strip()}'"
            )

            # Save to database with text_update (preserves existing rating if any)
            success = save_feedback_to_db(
                data_id,
                inference_type,
                rating_to_use,
                feedback_text.strip(),
                response_id,
            )

            if success:
                # Get updated feedback to show in display
                updated_feedback = load_existing_feedback(data_id, inference_type)

                # Create feedback display
                feedback_display = []
                if updated_feedback and updated_feedback.get("feedback_text"):
                    feedback_display = [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            [
                                                html.P(
                                                    "Your Comment:",
                                                    className="small text-muted fw-bold",
                                                )
                                            ],
                                            className="mb-2",
                                        ),
                                        html.P(
                                            updated_feedback["feedback_text"],
                                            className="mb-0",
                                            style={
                                                "fontSize": "0.875rem",
                                                "lineHeight": "1.4",
                                                "fontStyle": "italic",
                                            },
                                        ),
                                    ],
                                    className="py-2 px-3",
                                )
                            ],
                            color="info",
                            outline=True,
                            className="mb-3",
                            id={
                                "type": "existing-feedback-card",
                                "data_id": data_id,
                                "inference_type": inference_type,
                                "response_id": response_id,
                            },
                        )
                    ]

                # Return: close textarea, keep other outputs unchanged, update feedback display, and update submit button state
                return (
                    False,
                    no_update,
                    no_update,
                    no_update,
                    feedback_display,
                    {"display": "none"},
                    {"display": "inline"},
                    "Comment Submitted",
                    True,
                )
            else:
                # Error saving
                raise PreventUpdate

        # Determine rating and create updated button group
        if "positive" in button_id_clicked and positive_clicks:
            rating = "positive"

            # Create updated button group with solid positive button
            updated_buttons = dbc.ButtonGroup(
                [
                    dbc.Button(
                        [html.I(className="fas fa-thumbs-up me-1"), "Good"],
                        id={
                            "type": "feedback-btn",
                            "data_id": data_id,
                            "inference_type": inference_type,
                            "rating": "positive",
                            "response_id": response_id,
                        },
                        size="sm",
                        color="success",
                        outline=False,  # Solid button to show it's selected
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-thumbs-down me-1"), "Poor"],
                        id={
                            "type": "feedback-btn",
                            "data_id": data_id,
                            "inference_type": inference_type,
                            "rating": "negative",
                            "response_id": response_id,
                        },
                        size="sm",
                        color="danger",
                        outline=True,  # Keep outline for unselected
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-comment me-1"), "Comment"],
                        id={
                            "type": "feedback-text-only-btn",
                            "data_id": data_id,
                            "inference_type": inference_type,
                            "response_id": response_id,
                        },
                        size="sm",
                        color="info",
                        outline=True,
                    ),
                ],
                className="w-100",
            )

        elif "negative" in button_id_clicked and negative_clicks:
            rating = "negative"

            # Create updated button group with solid negative button
            updated_buttons = dbc.ButtonGroup(
                [
                    dbc.Button(
                        [html.I(className="fas fa-thumbs-up me-1"), "Good"],
                        id={
                            "type": "feedback-btn",
                            "data_id": data_id,
                            "inference_type": inference_type,
                            "rating": "positive",
                            "response_id": response_id,
                        },
                        size="sm",
                        color="success",
                        outline=True,  # Keep outline for unselected
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-thumbs-down me-1"), "Poor"],
                        id={
                            "type": "feedback-btn",
                            "data_id": data_id,
                            "inference_type": inference_type,
                            "rating": "negative",
                            "response_id": response_id,
                        },
                        size="sm",
                        color="danger",
                        outline=False,  # Solid button to show it's selected
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-comment me-1"), "Comment"],
                        id={
                            "type": "feedback-text-only-btn",
                            "data_id": data_id,
                            "inference_type": inference_type,
                            "response_id": response_id,
                        },
                        size="sm",
                        color="info",
                        outline=True,
                    ),
                ],
                className="w-100",
            )

        elif "feedback-text-only-btn" in button_id_clicked and comment_clicks:
            # Comment-only button clicked - just open the textarea without setting rating
            # Get existing feedback to show current comment
            existing_feedback = load_existing_feedback(data_id, inference_type)

            # Create feedback display if comment exists
            feedback_display = []
            if existing_feedback and existing_feedback.get("feedback_text"):
                feedback_display = [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                "Your Comment:",
                                                className="small text-muted fw-bold",
                                            )
                                        ],
                                        className="mb-2",
                                    ),
                                    html.P(
                                        existing_feedback["feedback_text"],
                                        className="mb-0",
                                        style={
                                            "fontSize": "0.875rem",
                                            "lineHeight": "1.4",
                                            "fontStyle": "italic",
                                        },
                                    ),
                                ],
                                className="py-2 px-3",
                            )
                        ],
                        color="info",
                        outline=True,
                        className="mb-3",
                        id={
                            "type": "existing-feedback-card",
                            "data_id": data_id,
                            "inference_type": inference_type,
                            "response_id": response_id,
                        },
                    )
                ]

            # Return: is_open=True, style=no_update, status=no_update, buttons=no_update, feedback_display=feedback_display, submit button states=no_update
            return (
                True,
                no_update,
                no_update,
                no_update,
                feedback_display,
                no_update,
                no_update,
                no_update,
                no_update,
            )
        else:
            raise PreventUpdate

        # Save feedback to database
        save_feedback_to_db(data_id, inference_type, rating, "", response_id)

        # Get existing feedback to show current comment (after saving the rating)
        existing_feedback = load_existing_feedback(data_id, inference_type)

        # Create feedback display if comment exists
        feedback_display = []
        if existing_feedback and existing_feedback.get("feedback_text"):
            feedback_display = [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.P(
                                            "Your Comment:",
                                            className="small text-muted fw-bold",
                                        )
                                    ],
                                    className="mb-2",
                                ),
                                html.P(
                                    existing_feedback["feedback_text"],
                                    className="mb-0",
                                    style={
                                        "fontSize": "0.875rem",
                                        "lineHeight": "1.4",
                                        "fontStyle": "italic",
                                    },
                                ),
                            ],
                            className="py-2 px-3",
                        )
                    ],
                    color="info",
                    outline=True,
                    className="mb-3",
                    id={
                        "type": "existing-feedback-card",
                        "data_id": data_id,
                        "inference_type": inference_type,
                        "response_id": response_id,
                    },
                )
            ]

        # Return: is_open=False (keep textarea closed), style=no_update, status=no_update, buttons=updated_buttons, feedback_display=feedback_display, submit button states=no_update
        return (
            False,
            no_update,
            no_update,
            updated_buttons,
            feedback_display,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    @app.callback(
        [
            Output(
                {
                    "type": "feedback-container",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "style",
                allow_duplicate=True,
            ),
            Output(
                {
                    "type": "feedback-status",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "children",
                allow_duplicate=True,
            ),
            Output(
                {
                    "type": "feedback-buttons-container",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "children",
                allow_duplicate=True,
            ),
        ],
        [
            Input(
                {
                    "type": "feedback-update-btn",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "n_clicks",
            )
        ],
        [
            State(
                {
                    "type": "feedback-update-btn",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "id",
            )
        ],
        prevent_initial_call=True,
    )
    def handle_feedback_update(n_clicks, button_id):
        """Handle update button clicks to unlock feedback for editing"""
        if not n_clicks:
            raise PreventUpdate

        # Get button information
        data_id = button_id["data_id"]
        inference_type = button_id["inference_type"]
        response_id = button_id["response_id"]

        # Reset to unlocked state with original buttons
        container_style = {
            "padding": "0.75rem",
            "border": "1px solid #dee2e6",
            "border-radius": "0.375rem",
            "background-color": "#ffffff",
            "margin-bottom": "0.75rem",
            "transition": "all 0.3s ease",
        }

        status_message = html.Div(
            [
                html.I(
                    className="fas fa-edit",
                    style={"color": "#6c757d", "margin-right": "0.25rem"},
                ),
                "Click thumbs up or down to provide feedback",
            ],
            style={"color": "#6c757d", "font-size": "0.8rem"},
        )

        # Create original feedback buttons
        feedback_buttons = dbc.ButtonGroup(
            [
                dbc.Button(
                    [html.I(className="fas fa-thumbs-up")],
                    id={
                        "type": "feedback-btn",
                        "data_id": data_id,
                        "inference_type": inference_type,
                        "rating": "positive",
                        "response_id": response_id,
                    },
                    color="success",
                    outline=True,
                    size="sm",
                    style={"font-size": "0.8rem", "padding": "0.3rem 0.6rem"},
                ),
                dbc.Button(
                    [html.I(className="fas fa-thumbs-down")],
                    id={
                        "type": "feedback-btn",
                        "data_id": data_id,
                        "inference_type": inference_type,
                        "rating": "negative",
                        "response_id": response_id,
                    },
                    color="danger",
                    outline=True,
                    size="sm",
                    style={"font-size": "0.8rem", "padding": "0.3rem 0.6rem"},
                ),
            ],
            size="sm",
        )

        return container_style, status_message, feedback_buttons

    # Simple debug callback to test if edit button is being clicked

    # Unified Cards Callback - FIXED to work like feedback system
    @app.callback(
        [
            Output(
                {
                    "type": "unified-display-content",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "style",
            ),
            Output(
                {
                    "type": "unified-edit-content",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "style",
            ),
            Output(
                {
                    "type": "edit-user-content-btn",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "style",
            ),
            Output(
                {
                    "type": "save-user-content-btn",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "style",
            ),
            Output(
                {
                    "type": "cancel-user-content-btn",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "style",
            ),
            Output(
                {
                    "type": "unified-card-display-content",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "children",
            ),
        ],
        [
            Input(
                {
                    "type": "edit-user-content-btn",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "save-user-content-btn",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "cancel-user-content-btn",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "n_clicks",
            ),
        ],
        [
            State(
                {
                    "type": "edit-user-content-btn",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "id",
            ),
            State(
                {
                    "type": "user-content-input",
                    "item_id": MATCH,
                    "card_type": MATCH,
                    "data_id": MATCH,
                },
                "value",
            ),
        ],
        prevent_initial_call=True,
    )
    def handle_unified_cards_like_feedback(
        edit_clicks,
        save_clicks,
        cancel_clicks,
        button_id,
        text_value,
    ):
        """Handle unified card interactions like feedback system - ALL COMPONENTS EXIST"""
        from utilities.mrpc_database import MRPCDatabase

        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Get the triggered button information from context
        button_id_clicked = ctx.triggered[0]["prop_id"]

        # Parse the button ID from the triggered component
        if not button_id_clicked or button_id_clicked == ".":
            raise PreventUpdate

        # The button_id parameter will be from the triggered component
        if button_id is None:
            raise PreventUpdate

        # Get button information
        data_id = button_id["data_id"]
        item_id = button_id["item_id"]
        card_type = button_id["card_type"]

        print(
            f"🔍 DEBUG: Unified callback (feedback-style) triggered - data_id={data_id}, item_id={item_id}, card_type={card_type}"
        )
        print(f"🔍 DEBUG: button_id_clicked={button_id_clicked}")

        # Handle edit button click - show edit content, hide display content
        if "edit-user-content-btn" in button_id_clicked and edit_clicks:
            print("🔍 DEBUG: Edit button clicked - switching to edit view")
            return (
                {"display": "none"},  # hide display content
                {"display": "block"},  # show edit content
                {"display": "none"},  # hide edit button
                {"display": "inline-block"},  # show save button
                {"display": "inline-block"},  # show cancel button
                no_update,  # no change to display content text
            )

        # Handle save button click - save data and switch to display
        elif "save-user-content-btn" in button_id_clicked and save_clicks:
            print("🔍 DEBUG: Save button clicked")

            if not text_value or not text_value.strip():
                print("❌ No text to save")
                raise PreventUpdate

            try:
                db = MRPCDatabase()
                if card_type == "question":
                    success = db.save_user_question(
                        data_id,
                        item_id,
                        text_value.strip(),
                        "",  # notes_text - could be extended later
                    )
                else:  # topic
                    success = db.save_category_note(
                        data_id, item_id, text_value.strip()
                    )

                if success:
                    print(" Save successful - switching to display view")
                    # Return to display mode with updated content
                    return (
                        {"display": "block"},  # show display content
                        {"display": "none"},  # hide edit content
                        {"display": "inline-block"},  # show edit button
                        {"display": "none"},  # hide save button
                        {"display": "none"},  # hide cancel button
                        text_value.strip(),  # update display content with saved text
                    )
                else:
                    print("❌ Save failed")
                    raise PreventUpdate
            except Exception as e:
                print(f"❌ Error saving: {e}")
                raise PreventUpdate

        # Handle cancel button click - switch back to display without saving
        elif "cancel-user-content-btn" in button_id_clicked and cancel_clicks:
            print("🔍 DEBUG: Cancel button clicked - switching to display view")
            return (
                {"display": "block"},  # show display content
                {"display": "none"},  # hide edit content
                {"display": "inline-block"},  # show edit button
                {"display": "none"},  # hide save button
                {"display": "none"},  # hide cancel button
                no_update,  # no change to display content text
            )
        else:
            raise PreventUpdate

    @app.callback(
        Output(
            {
                "type": "feedback-text",
                "data_id": MATCH,
                "inference_type": MATCH,
                "response_id": MATCH,
            },
            "value",
        ),
        [
            Input(
                {
                    "type": "feedback-text",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "value",
            )
        ],
        [
            State(
                {
                    "type": "feedback-text",
                    "data_id": MATCH,
                    "inference_type": MATCH,
                    "response_id": MATCH,
                },
                "id",
            )
        ],
        prevent_initial_call=True,
    )
    def handle_feedback_text_change(feedback_text, text_id):
        """Handle feedback text changes and update CSV"""
        if feedback_text and feedback_text.strip():
            # Update the existing feedback record with text
            # Note: In a real app, you'd want to update the specific record
            # For now, we'll just trigger on button clicks
            pass

        return feedback_text

    # All main UMAP callback registrations complete

    # User Inferred Questions/Topics Unified Callbacks
    @app.callback(
        Output("user-questions-content", "children", allow_duplicate=True),
        [
            Input({"type": "add-user-question-btn", "item_id": ALL}, "n_clicks"),
            Input({"type": "add-user-topic-btn", "item_id": ALL}, "n_clicks"),
            Input(
                {
                    "type": "delete-user-question-btn",
                    "item_id": ALL,
                    "question_id": ALL,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "delete-user-topic-btn",
                    "item_id": ALL,
                    "topic_id": ALL,
                },
                "n_clicks",
            ),
        ],
        [
            State("user-questions-content", "children"),
        ],
        prevent_initial_call=True,
    )
    def manage_unified_user_content(
        add_question_clicks,
        add_topic_clicks,
        delete_question_clicks,
        delete_topic_clicks,
        current_children,
    ):
        """Manage adding questions, topics, and deleting with unified content"""

        if not callback_context.triggered:
            raise PreventUpdate

        triggered_prop = callback_context.triggered[0]["prop_id"]

        # Extract data_id from the triggered prop_id
        triggered_id = json.loads(triggered_prop.split(".")[0])
        data_id = triggered_id["item_id"]

        # Handle add question button click
        if "add-user-question-btn" in triggered_prop:
            if add_question_clicks and any(
                click for click in add_question_clicks if click
            ):
                # Generate unique question ID
                question_id = str(uuid.uuid4())[:8]

                # Save the new question to database first
                try:
                    from utilities.mrpc_database import MRPCDatabase

                    db = MRPCDatabase()

                    # Save empty question to database
                    success = db.save_user_question(
                        data_id,
                        question_id,
                        "",
                        "",
                    )

                    if success:
                        print(f" Saved new user question {question_id} for {data_id}")
                        # Return updated unified content
                        return create_unified_user_content(data_id)
                    else:
                        print("❌ Failed to save new user question")

                except Exception as e:
                    print(f"❌ Error saving new user question: {e}")

        # Handle add topic button click
        elif "add-user-topic-btn" in triggered_prop:
            if add_topic_clicks and any(click for click in add_topic_clicks if click):
                # Generate unique topic ID
                topic_id = str(uuid.uuid4())[:8]

                # Save the new topic to database first
                try:
                    from utilities.mrpc_database import MRPCDatabase

                    db = MRPCDatabase()

                    # Save empty topic to database
                    success = db.save_category_note(
                        data_id,
                        topic_id,
                        "",
                    )

                    if success:
                        print(f" Saved new user topic {topic_id} for {data_id}")
                        # Return updated unified content
                        return create_unified_user_content(data_id)
                    else:
                        print("❌ Failed to save new user topic")

                except Exception as e:
                    print(f"❌ Error saving new user topic: {e}")

        # Handle delete question button click
        elif "delete-user-question-btn" in triggered_prop:
            if delete_question_clicks and any(
                click for click in delete_question_clicks if click
            ):
                question_id = triggered_id["question_id"]

                try:
                    from utilities.mrpc_database import MRPCDatabase

                    db = MRPCDatabase()

                    # Delete from database
                    success = db.delete_user_question(data_id, question_id)

                    if success:
                        print(f" Deleted user question {question_id} for {data_id}")
                        # Return updated unified content
                        return create_unified_user_content(data_id)
                    else:
                        print("❌ Failed to delete user question")

                except Exception as e:
                    print(f"❌ Error deleting user question: {e}")

        # Handle delete topic button click
        elif "delete-user-topic-btn" in triggered_prop:
            if delete_topic_clicks and any(
                click for click in delete_topic_clicks if click
            ):
                topic_id = triggered_id["topic_id"]

                try:
                    from utilities.mrpc_database import MRPCDatabase

                    db = MRPCDatabase()

                    # Delete from database
                    success = db.delete_category_note(data_id, topic_id)

                    if success:
                        print(f" Deleted user topic {topic_id} for {data_id}")
                        # Return updated unified content
                        return create_unified_user_content(data_id)
                    else:
                        print("❌ Failed to delete user topic")

                except Exception as e:
                    print(f"❌ Error deleting user topic: {e}")

        raise PreventUpdate

    @app.callback(
        Output(
            {"type": "save-user-question-btn", "item_id": MATCH, "question_id": MATCH},
            "color",
        ),
        [
            Input(
                {
                    "type": "save-user-question-btn",
                    "item_id": MATCH,
                    "question_id": MATCH,
                },
                "n_clicks",
            ),
        ],
        [
            State(
                {"type": "user-question-input", "item_id": MATCH, "question_id": MATCH},
                "value",
            ),
            State(
                {"type": "user-question-notes", "item_id": MATCH, "question_id": MATCH},
                "value",
            ),
            State(
                {
                    "type": "save-user-question-btn",
                    "item_id": MATCH,
                    "question_id": MATCH,
                },
                "id",
            ),
        ],
        prevent_initial_call=True,
    )
    def save_user_question(n_clicks, question_text, notes_text, button_id):
        """Save user question and notes to database"""
        if not n_clicks:
            raise PreventUpdate

        data_id = button_id["item_id"]
        question_id = button_id["question_id"]

        try:
            from utilities.mrpc_database import MRPCDatabase

            db = MRPCDatabase()
            success = db.save_user_question(
                data_id, question_id, question_text or "", notes_text or ""
            )

            if success:
                print(
                    f" Saved user question for {data_id}: '{question_text}' with notes: '{notes_text}'"
                )
                # Change button color temporarily to show save success
                return "success"
            else:
                print(f"❌ Failed to save user question for {data_id}")
                return "danger"

        except Exception as e:
            print(f"❌ Error saving user question: {e}")
            return "danger"

    # Persistent Category Note Callback
    @app.callback(
        [
            Output(
                {"type": "save-category-note-persistent", "item_id": MATCH}, "color"
            ),
            Output({"type": "category-note-save-status", "item_id": MATCH}, "children"),
        ],
        [
            Input(
                {"type": "save-category-note-persistent", "item_id": MATCH}, "n_clicks"
            ),
        ],
        [
            State({"type": "category-note-persistent", "item_id": MATCH}, "value"),
            State({"type": "save-category-note-persistent", "item_id": MATCH}, "id"),
        ],
        prevent_initial_call=True,
    )
    def save_persistent_category_note(n_clicks, notes_text, button_id):
        """Save persistent category note to database"""
        if not n_clicks:
            raise PreventUpdate

        data_id = button_id["item_id"]

        try:
            from utilities.mrpc_database import MRPCDatabase

            db = MRPCDatabase()
            # Use a fixed note_id for persistent notes (one per item)
            note_id = "persistent_note"

            success = db.save_category_note(data_id, note_id, notes_text or "")

            if success:
                print(f" Saved persistent category note for {data_id}: '{notes_text}'")
                # Change button color temporarily to show save success
                return "success", "✓ Saved"
            else:
                print(f"❌ Failed to save persistent category note for {data_id}")
                return "danger", "❌ Error"

        except Exception as e:
            print(f"❌ Error saving persistent category note: {e}")
            return "danger", "❌ Error"

    # Category Notes Callbacks - COMMENTED OUT DUE TO MISSING FUNCTIONS
    # @app.callback(
    #     Output({"type": "category-notes-container", "item_id": MATCH}, "children"),
    #     [
    #         Input({"type": "add-category-note-btn", "item_id": MATCH}, "n_clicks"),
    #         Input(
    #             {"type": "delete-category-note-btn", "item_id": MATCH, "note_id": ALL},
    #             "n_clicks",
    #         ),
    #     ],
    #     [
    #         State({"type": "category-notes-container", "item_id": MATCH}, "children"),
    #         State({"type": "add-category-note-btn", "item_id": MATCH}, "id"),
    #     ],
    #     prevent_initial_call=True,
    # )
    # def manage_category_notes(add_clicks, delete_clicks, current_children, button_id):
    #     """Manage adding and deleting category notes"""

    #     if not callback_context.triggered:
    #         raise PreventUpdate

    #     triggered_prop = callback_context.triggered[0]["prop_id"]
    #     data_id = button_id["item_id"]

    #     # Initialize current children if None
    #     if not current_children:
    #         current_children = []

    #     # Handle add button click
    #     if "add-category-note-btn" in triggered_prop:
    #         if add_clicks:
    #             # Generate unique note ID
    #             note_id = str(uuid.uuid4())[:8]

    #             # Create new note component
    #             new_note = create_category_note_component(data_id, note_id)
    #             current_children.append(new_note)

    #     # Handle delete button clicks
    #     elif "delete-category-note-btn" in triggered_prop:
    #         if any(delete_clicks):
    #             # Extract note_id from the triggered component
    #             triggered_component = json.loads(triggered_prop.split(".")[0])
    #             note_id_to_delete = triggered_component["note_id"]

    #             try:
    #                 from utilities.mrpc_database import MRPCDatabase

    #                 db = MRPCDatabase()
    #                 success = db.delete_category_note(data_id, note_id_to_delete)

    #                 if success:
    #                     # Reload notes from database to get updated list
    #                     current_children = load_existing_category_notes(data_id)
    #                 else:
    #                     print(f"❌ Failed to delete category note {note_id_to_delete}")

    #             except Exception as e:
    #                 print(f"❌ Error deleting category note: {e}")

    #     return current_children

    @app.callback(
        Output(
            {"type": "save-category-note-btn", "item_id": MATCH, "note_id": MATCH},
            "color",
        ),
        [
            Input(
                {"type": "save-category-note-btn", "item_id": MATCH, "note_id": MATCH},
                "n_clicks",
            ),
        ],
        [
            State(
                {"type": "category-note-input", "item_id": MATCH, "note_id": MATCH},
                "value",
            ),
            State(
                {"type": "save-category-note-btn", "item_id": MATCH, "note_id": MATCH},
                "id",
            ),
        ],
        prevent_initial_call=True,
    )
    def save_category_note(n_clicks, notes_text, button_id):
        """Save category note to database"""
        if not n_clicks:
            raise PreventUpdate

        data_id = button_id["item_id"]
        note_id = button_id["note_id"]

        try:
            from utilities.mrpc_database import MRPCDatabase

            db = MRPCDatabase()
            success = db.save_category_note(data_id, note_id, notes_text or "")

            if success:
                print(f" Saved category note for {data_id}: '{notes_text}'")
                # Change button color temporarily to show save success
                return "success"
            else:
                print(f"❌ Failed to save category note for {data_id}")
                return "danger"

        except Exception as e:
            print(f"❌ Error saving category note: {e}")
            return "danger"

    # AI Content Review Card callback (handles all feedback interactions)
    @app.callback(
        [
            Output(
                {
                    "type": "ai-content-thumbs-up",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "color",
            ),
            Output(
                {
                    "type": "ai-content-thumbs-down",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "color",
            ),
            Output(
                {
                    "type": "ai-justification-collapse",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "is_open",
            ),
        ],
        [
            Input(
                {
                    "type": "ai-content-thumbs-up",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "ai-content-thumbs-down",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "edit-ai-feedback",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
            Input(
                {
                    "type": "cancel-ai-justification",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
        ],
        [
            State(
                {
                    "type": "ai-content-thumbs-up",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "id",
            ),
        ],
        prevent_initial_call=True,
    )
    def handle_ai_content_feedback(
        thumbs_up_clicks, thumbs_down_clicks, edit_clicks, cancel_clicks, button_id
    ):
        """Handle all AI content feedback interactions"""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:
            data_id = button_id["data_id"]
            content_type = button_id["content_type"]

            # Load existing feedback to determine current state
            existing_feedback = load_existing_feedback(data_id, content_type)
            current_rating = (
                existing_feedback.get("rating", "") if existing_feedback else ""
            )

            # Default button colors based on current state
            thumbs_up_color = (
                "success" if current_rating == "positive" else "outline-success"
            )
            thumbs_down_color = (
                "danger" if current_rating == "negative" else "outline-danger"
            )

            # Determine which button was clicked
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            triggered_type = eval(triggered_id)["type"]

            if triggered_type == "ai-content-thumbs-up":
                # Thumbs up clicked - make mutually exclusive and open justification
                return "success", "outline-danger", True

            elif triggered_type == "ai-content-thumbs-down":
                # Thumbs down clicked - make mutually exclusive and open justification
                return "outline-success", "danger", True

            elif triggered_type == "edit-ai-feedback":
                # Edit button clicked - open justification with current state
                return thumbs_up_color, thumbs_down_color, True

            elif triggered_type == "cancel-ai-justification":
                # Cancel button clicked - close justification with current state
                return thumbs_up_color, thumbs_down_color, False

            else:
                raise PreventUpdate

        except Exception as e:
            print(f"❌ Error in AI content feedback handler: {e}")
            return "outline-success", "outline-danger", False

    # Callback for saving justification and closing textarea
    @app.callback(
        [
            Output(
                {
                    "type": "ai-justification-collapse",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "is_open",
                allow_duplicate=True,
            ),
            Output(
                {
                    "type": "ai-feedback-status",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "children",
            ),
        ],
        [
            Input(
                {
                    "type": "save-ai-justification",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "n_clicks",
            ),
        ],
        [
            State(
                {
                    "type": "ai-content-justification",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "value",
            ),
            State(
                {
                    "type": "ai-content-thumbs-up",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "color",
            ),
            State(
                {
                    "type": "ai-content-thumbs-down",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "color",
            ),
            State(
                {
                    "type": "save-ai-justification",
                    "data_id": MATCH,
                    "content_type": MATCH,
                    "response_id": MATCH,
                },
                "id",
            ),
        ],
        prevent_initial_call=True,
    )
    def save_ai_content_justification(
        n_clicks, justification_text, thumbs_up_color, thumbs_down_color, button_id
    ):
        """Save justification and close textarea"""
        if not n_clicks:
            raise PreventUpdate

        try:
            data_id = button_id["data_id"]
            content_type = button_id["content_type"]
            response_id = button_id["response_id"]

            # Determine rating based on button colors
            if thumbs_up_color == "success":
                rating = "positive"
            elif thumbs_down_color == "danger":
                rating = "negative"
            else:
                rating = ""  # No rating selected

            # Save feedback with justification
            success = save_feedback_to_db(
                data_id, content_type, rating, justification_text or "", response_id
            )

            if success:
                return False, " Feedback saved"  # Close textarea and show success
            else:
                return True, "❌ Failed to save feedback"  # Keep textarea open

        except Exception as e:
            print(f"❌ Error saving justification: {e}")
            return True, f"❌ Save error: {str(e)}"

    # All callback registrations complete

    # Add callback for tag summary forum selector
    @app.callback(
        [
            Output("tag-summary-heading", "children"),
            Output("tag-summary-content", "children"),
            Output("category-timeline-chart", "figure"),
            Output("category-distribution-chart", "figure"),
        ],
        [Input("tag-summary-forum-selector", "value")],
    )
    def update_tag_summary_content(selected_forum):
        """Update tag summary content, timeline chart, and distribution chart based on selected forum"""
        try:
            from utilities.mrpc_database import MRPCDatabase
            from services.interactive_charts import (
                create_posts_per_category_timeline,
                create_category_distribution_chart,
            )

            db = MRPCDatabase()

            # Get data based on forum selection
            if selected_forum == "all":
                df = db.get_all_posts_as_dataframe()
                forum_text = "All Forums"
            else:
                df = db.get_posts_by_forum(selected_forum)
                forum_text = f"{selected_forum.title()} Cancer Forum"

            if df.empty:
                heading = f"Tag Summary - {forum_text}"
                empty_content = html.P(f"No data available for {forum_text}.")
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title=f"No data available for {forum_text}",
                    xaxis_title="Date",
                    yaxis_title="Number of Posts",
                    height=400,
                )
                empty_pie_fig = go.Figure()
                empty_pie_fig.update_layout(
                    title=f"No data available for {forum_text}",
                    height=400,
                )
                return heading, empty_content, empty_fig, empty_pie_fig

            # Create timeline chart
            timeline_fig = create_posts_per_category_timeline(df)

            # Create category distribution pie chart
            distribution_fig = create_category_distribution_chart(df)

            # Create basic tag summary statistics
            total_posts = len(df)

            # Get tag statistics if available
            tag_stats = []
            if "llm_cluster_name" in df.columns:
                category_counts = df["llm_cluster_name"].value_counts()
                tag_stats.append(html.H4("Top Categories:"))
                for category, count in category_counts.head(10).items():
                    if category and str(category) != "nan":
                        tag_stats.append(html.P(f"• {category}: {count} posts"))
            elif "cluster_label" in df.columns:
                category_counts = df["cluster_label"].value_counts()
                tag_stats.append(html.H4("Top Categories (by keywords):"))
                for category, count in category_counts.head(10).items():
                    if category and str(category) != "nan":
                        # Truncate long cluster labels
                        display_category = (
                            category[:60] + "..."
                            if len(str(category)) > 60
                            else category
                        )
                        tag_stats.append(html.P(f"• {display_category}: {count} posts"))

            # Add forum statistics
            if "forum" in df.columns and selected_forum == "all":
                tag_stats.append(html.H4("Posts by Forum:"))
                forum_counts = df["forum"].value_counts()
                for forum, count in forum_counts.items():
                    if forum and str(forum) != "nan":
                        tag_stats.append(html.P(f"• {forum.title()}: {count} posts"))

            # Add date range information
            if "date_posted" in df.columns:
                df_copy = df.copy()
                try:
                    df_copy["date_posted"] = pd.to_datetime(
                        df_copy["date_posted"], errors="coerce"
                    )
                    # Remove invalid dates
                    df_copy = df_copy.dropna(subset=["date_posted"])

                    if not df_copy.empty:
                        min_date = df_copy["date_posted"].min().strftime("%B %d, %Y")
                        max_date = df_copy["date_posted"].max().strftime("%B %d, %Y")
                        tag_stats.append(html.H4("Date Range:"))
                        tag_stats.append(html.P(f"• From {min_date} to {max_date}"))
                    else:
                        tag_stats.append(html.H4("Date Range:"))
                        tag_stats.append(html.P("• No valid dates found in data"))
                except Exception as e:
                    print(f"⚠️ Warning: Could not parse date range: {str(e)}")
                    tag_stats.append(html.H4("Date Range:"))
                    tag_stats.append(html.P("• Date parsing error"))

            content = [
                html.H3(f"Summary Statistics for {forum_text}"),
                html.P(f"Total Posts: {total_posts:,}"),
                html.Hr(),
            ] + tag_stats

            heading = f"Tag Summary - {forum_text}"
            return heading, content, timeline_fig, distribution_fig

        except Exception as e:
            print(f"Error in update_tag_summary_content: {str(e)}")
            error_heading = "Tag Summary - Error"
            error_content = html.P(f"Error loading tag summary: {str(e)}")
            error_fig = go.Figure()
            error_fig.update_layout(
                title="Error loading chart",
                xaxis_title="Date",
                yaxis_title="Number of Posts",
                height=400,
            )
            error_pie_fig = go.Figure()
            error_pie_fig.update_layout(
                title="Error loading chart",
                height=400,
            )
            return error_heading, error_content, error_fig, error_pie_fig

    # Callback to populate user info in main navbar
    @app.callback(
        Output("navbar-user-info", "children"),
        Input("url", "pathname"),  # Trigger on page load
        prevent_initial_call=False,
    )
    def update_navbar_user_info(pathname):
        """Update the user information displayed in the main navbar"""
        try:
            from utilities.auth import get_current_user, is_admin

            current_user = get_current_user()

            if current_user:
                user_display = (
                    f"{current_user['first_name']} {current_user['last_name']}"
                )
                user_role = "Admin" if is_admin() else "User"
                user_display = f"{user_display} ({user_role})"
                return [
                    html.I(
                        className="fas fa-user",
                        style={
                            "color": "#6c757d",
                            "margin-right": "0.5rem",
                            "font-size": "0.9rem",
                        },
                    ),
                    html.Span(user_display),
                ]
            else:
                return [
                    html.I(
                        className="fas fa-user-slash",
                        style={
                            "color": "#dc3545",
                            "margin-right": "0.5rem",
                            "font-size": "0.9rem",
                        },
                    ),
                    html.Span("Not logged in"),
                ]
        except Exception:
            return [
                html.I(
                    className="fas fa-exclamation-triangle",
                    style={
                        "color": "#ffc107",
                        "margin-right": "0.5rem",
                        "font-size": "0.9rem",
                    },
                ),
                html.Span("Authentication error"),
            ]

    # Sign-out callback using clientside JavaScript for reliability
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks > 0) {
                console.log('🚪 Sign-out button clicked, redirecting to /sign-out');
                window.location.href = '/sign-out';
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("sign-out-button", "style"),  # Dummy output
        Input("sign-out-button", "n_clicks"),
        prevent_initial_call=True,
    )

    # NOTE: All tag editing callbacks are now handled by the unified tagging system
    # See utility/unified_tagging_system.py and setup_unified_tagging_callbacks()
