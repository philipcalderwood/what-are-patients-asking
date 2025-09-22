import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State
import os
import uuid
import json
from config import (
    TEXTAREA_COMPONENT_STYLE,
    TEXTAREA_WRAPPER_STYLE,
    MAIN_CONTENT_VIEW_STYLE,
)
from utilities.backend import get_forum_data
from services.table_view import create_table_view

# Import direct database access
from utilities.mrpc_database import MRPCDatabase
from components.basic_metadata_content import create_basic_metadata_content

# Cache for UMAP figures (data cache now handled by database)
_figure_cache = {}


# def get_data_path(filename):
#     """Get the correct path for data files, checking both data/ directory and root"""
#     data_dir_path = os.path.join("data", filename)
#     root_path = filename

#     # Check if file exists in data directory first
#     if os.path.exists(data_dir_path):
#         return data_dir_path
#     elif os.path.exists(root_path):
#         return root_path
#     else:
#         # Default to data directory for new files
#         return data_dir_path


# def get_cluster_summary(forum):
#     """
#     Get a summary of clusters from forum data.

#     Args:
#         forum (str): Forum to analyze ("all", "cervical", etc.)

#     Returns:
#         pd.DataFrame: Summary with cluster counts and labels
#     """
#     df = get_forum_data(forum)

#     cluster_summary = (
#         df.groupby("cluster")
#         .agg({"LLM_inferred_question": "count", "cluster_label": "first"})
#         .rename(columns={"LLM_inferred_question": "count"})
#     )

#     return cluster_summary


# Example usage for different dashboard frameworks:


# def create_text_area_component(original_post):
#     """Create a reusable textarea component for displaying post content"""
#     from dash import html

#     # Clean the text data - remove leading/trailing whitespace and normalize line breaks
#     cleaned_post = (
#         str(original_post).strip() if original_post else "No content available"
#     )

#     return html.Div(
#         [
#             html.Textarea(
#                 children=cleaned_post,  # Use cleaned text to eliminate leading whitespace/newlines
#                 key=f"textarea-{len(cleaned_post)}-{hash(cleaned_post) % 10000}",
#                 style=TEXTAREA_COMPONENT_STYLE,
#                 readOnly="readOnly",  # Use string value as expected by Dash
#             )
#         ],
#         style=TEXTAREA_WRAPPER_STYLE,
#     )


# def create_category_feedback_with_notes(data_id, feedback_key, display_label, value):
#     """Create category feedback component with integrated persistent notes within the same card"""
#     from dash import html
#     import dash_bootstrap_components as dbc
#     import uuid

#     # Check for existing feedback
#     existing_feedback = load_existing_feedback(data_id, feedback_key)

#     # Generate unique response ID - use existing one if available
#     if existing_feedback and existing_feedback.get("response_id"):
#         response_id = existing_feedback["response_id"]
#     else:
#         response_id = str(uuid.uuid4())

#     # Determine initial state based on existing feedback
#     if existing_feedback:
#         # Existing feedback found - start in locked state
#         rating = existing_feedback.get("rating", "")
#         feedback_text = existing_feedback.get("feedback_text", "")

#         # Handle potential NaN values from pandas - convert to string
#         if not isinstance(feedback_text, str):
#             feedback_text = (
#                 str(feedback_text)
#                 if feedback_text and str(feedback_text) != "nan"
#                 else ""
#             )

#         formatted_time = existing_feedback.get("formatted_time", "")

#         if rating == "positive":
#             container_style = {
#                 "padding": "0.75rem",
#                 "border": "2px solid #28a745",
#                 "border-radius": "0.375rem",
#                 "background-color": "#d4edda",
#                 "margin-bottom": "0.75rem",
#                 "transition": "all 0.3s ease",
#                 "position": "relative",  # Add position relative for absolute positioning of buttons
#             }
#             status_color = "#155724"
#             status_icon = "fa-thumbs-up"
#             status_text = f"Positive feedback submitted on {formatted_time}"
#         elif rating == "negative":
#             container_style = {
#                 "padding": "0.75rem",
#                 "border": "2px solid #dc3545",
#                 "border-radius": "0.375rem",
#                 "background-color": "#f8d7da",
#                 "margin-bottom": "0.75rem",
#                 "transition": "all 0.3s ease",
#                 "position": "relative",  # Add position relative for absolute positioning of buttons
#             }
#             status_color = "#721c24"
#             status_icon = "fa-thumbs-down"
#             status_text = f"Negative feedback submitted on {formatted_time}"
#         else:
#             # Text-only feedback
#             container_style = {
#                 "padding": "0.75rem",
#                 "border": "2px solid #17a2b8",
#                 "border-radius": "0.375rem",
#                 "background-color": "#d1ecf1",
#                 "margin-bottom": "0.75rem",
#                 "transition": "all 0.3s ease",
#                 "position": "relative",  # Add position relative for absolute positioning of buttons
#             }
#             status_color = "#0c5460"
#             status_icon = "fa-comment"
#             status_text = f"Text feedback submitted on {formatted_time}"

#         # Create locked state status message
#         status_message = html.Div(
#             [
#                 html.I(
#                     className=f"fas {status_icon}",
#                     style={"color": status_color, "margin-right": "0.25rem"},
#                 ),
#                 status_text,
#             ],
#             style={
#                 "color": status_color,
#                 "font-size": "0.75rem",
#                 "margin-bottom": "0.5rem",
#             },
#         )

#         # Show existing feedback text if available
#         if feedback_text.strip():
#             status_message = html.Div(
#                 [
#                     status_message,
#                     html.Div(
#                         f'"{feedback_text}"',
#                         style={
#                             "font-style": "italic",
#                             "color": status_color,
#                             "font-size": "0.7rem",
#                             "margin-top": "0.25rem",
#                             "padding": "0.25rem",
#                             "background-color": "rgba(255,255,255,0.3)",
#                             "border-radius": "0.25rem",
#                         },
#                     ),
#                 ]
#             )

#         # Create update button for locked state
#         buttons_container = dbc.Button(
#             [
#                 html.I(className="fas fa-edit", style={"margin-right": "0.25rem"}),
#                 "Update",
#             ],
#             id={
#                 "type": "feedback-update-btn",
#                 "data_id": data_id,
#                 "inference_type": feedback_key,
#                 "response_id": response_id,
#             },
#             size="sm",
#             color="secondary",
#             outline=True,
#             style={
#                 "font-size": "0.7rem",
#                 "padding": "0.2rem 0.5rem",
#                 "position": "absolute",
#                 "top": "0.75rem",
#                 "right": "0.75rem",
#             },
#         )

#         # Text area starts hidden for locked state
#         textarea_is_open = False

#     else:
#         # No existing feedback - start in unlocked state
#         container_style = {
#             "padding": "0.75rem",
#             "border": "1px solid #dee2e6",
#             "border-radius": "0.375rem",
#             "background-color": "#ffffff",
#             "margin-bottom": "0.75rem",
#             "transition": "all 0.3s ease",
#             "position": "relative",  # Add position relative for absolute positioning of buttons
#         }

#         status_message = html.Div(
#             "",  # Remove the instructional text
#             style={"display": "none"},  # Hide the status message when no feedback
#         )

#         # Create initial feedback buttons
#         buttons_container = html.Div(
#             [
#                 dbc.Button(
#                     html.I(className="fas fa-thumbs-up"),
#                     id={
#                         "type": "feedback-btn",
#                         "data_id": data_id,
#                         "inference_type": feedback_key,
#                         "rating": "positive",
#                         "response_id": response_id,
#                     },
#                     size="sm",
#                     color="success",
#                     outline=True,
#                     style={
#                         "padding": "0.3rem 0.6rem",
#                         "margin-right": "0.25rem",
#                         "font-size": "0.8rem",
#                     },
#                 ),
#                 dbc.Button(
#                     html.I(className="fas fa-thumbs-down"),
#                     id={
#                         "type": "feedback-btn",
#                         "data_id": data_id,
#                         "inference_type": feedback_key,
#                         "rating": "negative",
#                         "response_id": response_id,
#                     },
#                     size="sm",
#                     color="danger",
#                     outline=True,
#                     style={"padding": "0.3rem 0.6rem", "font-size": "0.8rem"},
#                 ),
#             ],
#             style={
#                 "display": "flex",
#                 "gap": "0.25rem",
#                 "position": "absolute",
#                 "top": "0.75rem",
#                 "right": "0.75rem",
#             },
#         )

#         # Text area starts hidden for new feedback
#         textarea_is_open = False

#     return html.Div(
#         [
#             # Inference content and feedback in integrated card
#             html.Div(
#                 [
#                     # Main inference display
#                     html.Div(
#                         [
#                             html.Strong(
#                                 f"{display_label}:",
#                                 style={
#                                     "font-size": "0.85rem",
#                                     "color": "#495057",
#                                     "margin-bottom": "0.25rem",
#                                     "display": "block",
#                                 },
#                             ),
#                             html.Div(
#                                 str(value) if value else "N/A",
#                                 style={
#                                     "font-size": "0.8rem",
#                                     "color": "#6c757d",
#                                     "margin-bottom": "0.5rem",
#                                     "line-height": "1.4",
#                                 },
#                             ),
#                         ]
#                     ),
#                     # Integrated persistent notes section within the card
#                     html.Div(
#                         [
#                             html.Strong(
#                                 "Notes:",
#                                 style={
#                                     "font-size": "0.8rem",
#                                     "color": "#495057",
#                                     "margin-bottom": "0.5rem",
#                                     "display": "block",
#                                 },
#                             ),
#                             # Always visible textarea for notes
#                             dbc.Textarea(
#                                 id={
#                                     "type": "category-note-persistent",
#                                     "item_id": data_id,
#                                 },
#                                 placeholder="Add your notes about this category...",
#                                 value=load_existing_category_note_persistent(data_id),
#                                 size="sm",
#                                 style={
#                                     "font-size": "0.75rem",
#                                     "min-height": "2.5rem",
#                                     "resize": "vertical",
#                                     "margin-bottom": "0.5rem",
#                                 },
#                             ),
#                             # Save button and status for notes
#                             html.Div(
#                                 [
#                                     dbc.Button(
#                                         "Save Note",
#                                         id={
#                                             "type": "save-category-note-persistent",
#                                             "item_id": data_id,
#                                         },
#                                         color="primary",
#                                         size="sm",
#                                         style={
#                                             "font-size": "0.75rem",
#                                             "padding": "0.25rem 0.5rem",
#                                             "margin-right": "0.5rem",
#                                         },
#                                     ),
#                                     html.Span(
#                                         id={
#                                             "type": "category-note-save-status",
#                                             "item_id": data_id,
#                                         },
#                                         style={
#                                             "font-size": "0.75rem",
#                                             "color": "#6c757d",
#                                         },
#                                     ),
#                                 ],
#                                 style={"display": "flex", "align-items": "center"},
#                             ),
#                         ],
#                         style={
#                             "padding": "0.5rem",
#                             "background-color": "#f8f9fa",
#                             "border": "1px solid #dee2e6",
#                             "border-radius": "0.375rem",
#                             "margin-bottom": "0.5rem",
#                         },
#                     ),
#                     # Feedback controls
#                     html.Div(
#                         [
#                             # Status message
#                             html.Div(
#                                 status_message,
#                                 id={
#                                     "type": "feedback-status",
#                                     "data_id": data_id,
#                                     "inference_type": feedback_key,
#                                     "response_id": response_id,
#                                 },
#                             ),
#                             # Feedback buttons or update button
#                             html.Div(
#                                 buttons_container,
#                                 id={
#                                     "type": "feedback-buttons-container",
#                                     "data_id": data_id,
#                                     "inference_type": feedback_key,
#                                     "response_id": response_id,
#                                 },
#                             ),
#                             # Optional feedback text area
#                             dbc.Collapse(
#                                 [
#                                     dbc.Textarea(
#                                         id={
#                                             "type": "feedback-text",
#                                             "data_id": data_id,
#                                             "inference_type": feedback_key,
#                                             "response_id": response_id,
#                                         },
#                                         placeholder="Optional: Add your feedback comments here...",
#                                         size="sm",
#                                         value=existing_feedback.get("feedback_text", "")
#                                         if existing_feedback
#                                         else "",
#                                         style={
#                                             "font-size": "0.7rem",
#                                             "min-height": "2.5rem",
#                                             "resize": "vertical",
#                                             "margin-bottom": "0.5rem",
#                                         },
#                                     ),
#                                     dbc.Button(
#                                         "Submit Text",
#                                         id={
#                                             "type": "feedback-text-submit",
#                                             "data_id": data_id,
#                                             "inference_type": feedback_key,
#                                             "response_id": response_id,
#                                         },
#                                         size="sm",
#                                         color="primary",
#                                         outline=True,
#                                         style={
#                                             "font-size": "0.65rem",
#                                             "padding": "0.2rem 0.5rem",
#                                         },
#                                     ),
#                                 ],
#                                 id={
#                                     "type": "feedback-collapse",
#                                     "data_id": data_id,
#                                     "inference_type": feedback_key,
#                                     "response_id": response_id,
#                                 },
#                                 is_open=textarea_is_open,
#                             ),
#                         ],
#                         style={
#                             "padding-top": "0.5rem",
#                             "border-top": "1px solid #e9ecef",
#                         },
#                     ),
#                 ],
#                 # Dynamic container styling
#                 id={
#                     "type": "feedback-container",
#                     "data_id": data_id,
#                     "inference_type": feedback_key,
#                     "response_id": response_id,
#                 },
#                 style=container_style,
#             )
#         ]
#     )


# def load_existing_category_note_persistent(data_id: str) -> str:
#     """Load existing persistent category note from database for a given item"""
#     try:
#         from utilities.mrpc_database import MRPCDatabase

#         db = MRPCDatabase()
#         existing_notes = db.get_category_notes(data_id)

#         # Look specifically for the persistent note
#         for note in existing_notes:
#             if note.get("note_id") == "persistent_note":
#                 return note.get("notes_text", "")

#         return ""

#     except Exception as e:
#         print(f"❌ Error loading existing category note: {e}")
#         return ""


# def create_category_note_component(data_id, note_id, notes_text=""):
#     """Create a component for a single category note"""
#     from dash import html

#     return html.Div(
#         [
#             # Header
#             html.H6(
#                 "Category Note",
#                 style={
#                     "margin-bottom": "0.5rem",
#                     "color": "#495057",
#                     "font-weight": "600",
#                     "font-size": "0.9rem",
#                 },
#             ),
#             # Notes input area
#             html.Div(
#                 [
#                     dbc.Textarea(
#                         id={
#                             "type": "category-note-input",
#                             "item_id": data_id,
#                             "note_id": note_id,
#                         },
#                         placeholder="Add notes about this category...",
#                         value=notes_text,
#                         size="sm",
#                         style={
#                             "font-size": "0.75rem",
#                             "min-height": "2.5rem",
#                             "resize": "vertical",
#                             "background-color": "#f8f9fa",
#                             "border": "1px solid #e9ecef",
#                             "margin-bottom": "0.5rem",
#                         },
#                     ),
#                     # Action buttons
#                     html.Div(
#                         [
#                             dbc.Button(
#                                 "Save Note",
#                                 id={
#                                     "type": "save-category-note-btn",
#                                     "item_id": data_id,
#                                     "note_id": note_id,
#                                 },
#                                 color="primary",
#                                 size="sm",
#                                 style={
#                                     "font-size": "0.75rem",
#                                     "padding": "0.25rem 0.5rem",
#                                     "margin-right": "0.5rem",
#                                 },
#                             ),
#                             dbc.Button(
#                                 "Delete",
#                                 id={
#                                     "type": "delete-category-note-btn",
#                                     "item_id": data_id,
#                                     "note_id": note_id,
#                                 },
#                                 color="danger",
#                                 outline=True,
#                                 size="sm",
#                                 style={
#                                     "font-size": "0.75rem",
#                                     "padding": "0.25rem 0.5rem",
#                                 },
#                             ),
#                         ],
#                         style={"text-align": "left"},
#                     ),
#                 ],
#             ),
#         ],
#         style={
#             "margin-bottom": "0.75rem",
#             "padding": "0.75rem",
#             "border": "1px solid #dee2e6",
#             "border-radius": "0.375rem",
#             "background-color": "#fff8f0",  # Slightly different background
#         },
#         id={
#             "type": "category-note-container",
#             "data_id": data_id,
#             "note_id": note_id,
#         },
#     )


# def load_existing_category_notes(data_id: str):
#     """Load existing category notes from database for a given item"""
#     try:
#         from utilities.mrpc_database import MRPCDatabase

#         db = MRPCDatabase()
#         existing_notes = db.get_category_notes(data_id)

#         note_components = []
#         for note_data in existing_notes:
#             note_component = create_category_note_component(
#                 data_id, note_data["note_id"], note_data["notes_text"] or ""
#             )
#             note_components.append(note_component)

#         return note_components

#     except Exception as e:
#         print(f"❌ Error loading existing category notes: {e}")
#         return []


# def create_metadata_sidebar_content(point, customdata):
#     """Create reusable metadata sidebar content"""
#     from dash import html

#     # Define the actual order of data in customdata array based on plot creation
#     # ["id", "forum", "post_type", "username", "original_title", "post_url",
#     #  "LLM_inferred_question", "cluster", "cluster_label", "date_posted",
#     #  "llm_cluster_name", "original_post", "tag_group", "tag_subgroup",
#     #  "tag_name", "tag_source", "tag_confidence", "tag_hierarchy_path", "enhanced_tags"]

#     # Extract specific fields by their actual indices
#     data_id = customdata[0] if len(customdata) > 0 else "unknown"
#     inferred_question = customdata[6] if len(customdata) > 6 else "N/A"

#     # Legacy category (for backward compatibility)
#     legacy_category = customdata[10] if len(customdata) > 10 else "N/A"

#     # Enhanced tags JSON (new index 18)
#     # Inferred Metadata section with integrated feedback cards
#     inferred_items = []

#     # Create feedback card for inferred question with notes
#     feedback_card_question = create_review_content_card(
#         data_id=data_id,
#         content_type="LLM_inferred_question",
#         display_label="AI Inferred Question",
#         value=inferred_question,
#         card_type="ai_feedback",
#     )
#     inferred_items.append(feedback_card_question)

#     # Create feedback card for category
#     display_category = legacy_category
#     feedback_key = "llm_cluster_name"

#     feedback_card_category = create_review_content_card(
#         data_id=data_id,
#         content_type=feedback_key,
#         display_label="AI Inferred Category",
#         value=display_category,
#         card_type="ai_feedback",
#     )
#     inferred_items.append(feedback_card_category)

#     # Remove the old separate category notes section since it's now integrated

#     # Add User Inferred Questions section right after category notes
#     user_questions_section = html.Div(
#         [
#             html.Strong(
#                 "User Inferred Questions",
#                 style={"margin-bottom": "0.5rem", "color": "#007bff"},
#             ),
#             # Container for user questions (will be populated with existing questions)
#             html.Div(
#                 id={"type": "user-questions-container", "item_id": data_id},
#                 children=load_existing_user_questions(data_id),
#                 style={"margin-bottom": "0.5rem"},
#             ),
#             # Add new question button
#             dbc.Button(
#                 [
#                     html.I(className="fas fa-plus", style={"margin-right": "0.25rem"}),
#                     "Add User Question",
#                 ],
#                 id={"type": "add-user-question-btn", "item_id": data_id},
#                 color="success",
#                 outline=True,
#                 size="sm",
#                 style={
#                     "font-size": "0.75rem",
#                     "padding": "0.25rem 0.5rem",
#                 },
#             ),
#         ],
#         style={"margin-bottom": "1rem"},
#     )
#     inferred_items.append(user_questions_section)

#     return html.Div(
#         [
#             html.Div(
#                 [
#                     html.Strong(
#                         "Inferred Metadata",
#                         style={"margin-bottom": "0.5rem", "color": "#007bff"},
#                     ),
#                     html.Div(inferred_items),
#                 ],
#                 style={"margin-bottom": "1rem"},
#             )
#         ]
#     )


def table_controls_col():
    """Create the table controls sidebar component with dbc cards and integrated reading pane"""
    from dash import html

    return dbc.Stack(
        [
            # Table Controls Card (fixed at top, standalone appearance)
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.I(className="fas fa-cogs me-2"),
                            html.Span("Table Controls", className="fw-bold"),
                        ],
                        className="py-3 px-4 bg-primary text-white",
                    ),
                    dbc.CardBody(
                        [
                            # Pagination controls at the top
                            html.Div(
                                [
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "‹‹",
                                                id="page-first-btn",
                                                size="sm",
                                                outline=True,
                                                color="primary",
                                                style={"font-size": "0.7rem"},
                                            ),
                                            dbc.Button(
                                                "‹",
                                                id="page-prev-btn",
                                                size="sm",
                                                outline=True,
                                                color="primary",
                                                style={"font-size": "0.7rem"},
                                            ),
                                            html.Span(
                                                id="page-info",
                                                children="Page 1 of 1",
                                                style={
                                                    "font-size": "0.7rem",
                                                    "line-height": "2rem",
                                                    "margin": "0 0.5rem",
                                                    "white-space": "nowrap",
                                                    "color": "#6c757d",
                                                },
                                            ),
                                            dbc.Button(
                                                "›",
                                                id="page-next-btn",
                                                size="sm",
                                                outline=True,
                                                color="primary",
                                                style={"font-size": "0.7rem"},
                                            ),
                                            dbc.Button(
                                                "››",
                                                id="page-last-btn",
                                                size="sm",
                                                outline=True,
                                                color="primary",
                                                style={"font-size": "0.7rem"},
                                            ),
                                        ],
                                        size="sm",
                                        className="d-flex align-items-center justify-content-center mb-3",
                                    ),
                                ],
                            ),
                            # Forum selector
                            html.Div(
                                [
                                    html.Label(
                                        "Forum:",
                                        className="form-label mb-2",
                                        style={
                                            "font-size": "0.8rem",
                                            "font-weight": "bold",
                                        },
                                    ),
                                    dcc.Dropdown(
                                        id="table-forum-selector",
                                        options=[
                                            {"label": "All Forums", "value": "all"},
                                            {
                                                "label": "Cervical Cancer Forum",
                                                "value": "cervical",
                                            },
                                            {
                                                "label": "Ovarian Cancer Forum",
                                                "value": "ovarian",
                                            },
                                            {
                                                "label": "Vaginal Cancer Forum",
                                                "value": "vaginal",
                                            },
                                            {
                                                "label": "Vulval Cancer Forum",
                                                "value": "vulval",
                                            },
                                            {
                                                "label": "Womb Cancer Forum",
                                                "value": "womb",
                                            },
                                        ],
                                        value="all",
                                        style={
                                            "font-size": "0.8rem",
                                            "margin-bottom": "1rem",
                                        },
                                    ),
                                ],
                            ),
                            # Export controls
                            html.Div(
                                [
                                    html.Label(
                                        "Export Data:",
                                        className="form-label mb-2",
                                        style={"font-size": "0.8rem"},
                                    ),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "Export CSV",
                                                id="export-csv-btn",
                                                size="sm",
                                                color="secondary",
                                                outline=True,
                                                style={"font-size": "0.7rem"},
                                            ),
                                            dbc.Button(
                                                "Export Filtered",
                                                id="export-filtered-btn",
                                                size="sm",
                                                color="secondary",
                                                outline=True,
                                                style={"font-size": "0.7rem"},
                                            ),
                                        ],
                                        size="sm",
                                    ),
                                ],
                            ),
                        ],
                        className="p-2",
                    ),
                ],
                id="table-controls-section",
                style={
                    "display": "block",
                    "border": "1px solid #dee2e6",
                    "border-radius": "0.375rem",
                    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "background-color": "#ffffff",
                    "margin-bottom": "0.75rem",
                    "flex-shrink": "0",  # Don't allow shrinking
                },  # Fixed standalone card at top
            ),
            # Basic Metadata Card (positioned between table controls and reading pane)
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.I(className="fas fa-info-circle me-2"),
                                            html.Span(
                                                "Basic Metadata", className="fw-bold"
                                            ),
                                        ],
                                        width=12,
                                    )
                                ],
                                className="align-items-center",
                            )
                        ],
                        className="py-3 px-4 text-white bg-secondary",
                    ),
                    dbc.CardBody(
                        [
                            html.Div(
                                id="basic-metadata-content",
                                children=[
                                    dbc.Alert(
                                        [
                                            html.I(className="fas fa-info-circle me-2"),
                                            "Click on a row to see basic metadata",
                                        ],
                                        color="light",
                                        className="text-center mb-0",
                                    )
                                ],
                                className="metadata-content",
                            )
                        ],
                        className="p-3",
                    ),
                ],
                className="mb-3",
                outline=True,
                style={
                    "flex-shrink": "0",  # Don't allow shrinking
                },
            ),
            # Reading Pane Card (standalone appearance, takes remaining space)
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.I(className="fas fa-book-open me-2"),
                            html.Span("Reading Pane", className="fw-bold"),
                        ],
                        className="py-3 px-4 bg-success text-white",
                    ),
                    dbc.CardBody(
                        [
                            html.Div(
                                # id="sidebar-reading-pane",
                                children=[
                                    html.P(
                                        "Select a row to read the original post",
                                        className="text-muted text-center font-italic",
                                        style={
                                            "margin": "2rem 0",
                                            "font-size": "0.8rem",
                                        },
                                    )
                                ],
                                style={
                                    # "height": "calc(100vh - 25rem)",  # Fixed height for scrolling
                                    "overflow-y": "auto",
                                    "overflow-x": "hidden",
                                    "padding": "0.5rem",
                                    "word-wrap": "break-word",
                                    "white-space": "pre-wrap",
                                },
                            )
                        ],
                        id="sidebar-reading-pane",
                        className="p-2 overflow-auto mt-0",
                    ),
                ],
                style={
                    "border": "1px solid #dee2e6",
                    "border-radius": "0.375rem",
                    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "flex": "1",  # Take all remaining space
                    "min-height": "0",  # Allow flex shrinking
                },  # Standalone card appearance that grows
            ),
        ],
        # style={
        #     "flex": "1 1 320px",
        #     # "padding": "0.75rem",
        #     "box-sizing": "border-box",
        #     # "height": "calc(100vh - 3.5rem)",  # Removed - use natural height
        #     "display": "flex",
        #     "flex-direction": "column",
        # },
    )


# def create_inferred_metadata_content(point, customdata):
#     """Create inferred metadata content (AI inferred question and category)"""
#     from dash import html

#     # Extract inferred data
#     data_id = customdata[0] if len(customdata) > 0 else "unknown"
#     inferred_question = customdata[6] if len(customdata) > 6 else "N/A"
#     legacy_category = customdata[10] if len(customdata) > 10 else "N/A"
#     tag_hierarchy_path = customdata[17] if len(customdata) > 17 else "N/A"

#     inferred_items = []

#     # Create feedback card for inferred question
#     feedback_card_question = create_review_content_card(
#         data_id=data_id,
#         content_type="LLM_inferred_question",
#         display_label="AI Inferred Question",
#         value=inferred_question,
#         card_type="ai_feedback",
#     )
#     inferred_items.append(feedback_card_question)

#     # Create feedback card for category
#     if (
#         tag_hierarchy_path
#         and tag_hierarchy_path != "N/A"
#         and str(tag_hierarchy_path).strip()
#     ):
#         display_category = tag_hierarchy_path
#         feedback_key = "tag_hierarchy_path"
#     else:
#         display_category = legacy_category
#         feedback_key = "llm_cluster_name"

#     feedback_card_category = create_review_content_card(
#         data_id=data_id,
#         content_type=feedback_key,
#         display_label="AI Inferred Category",
#         value=display_category,
#         card_type="ai_feedback",
#     )
#     inferred_items.append(feedback_card_category)

#     return html.Div(inferred_items)


# def for_dash():
#     """Returns layout components for Plotly Dash dashboard with click popup and metadata sidebar"""
#     # Delegate to the forum explorer page dashboard function
#     from pages.forum_explorer import create_forum_explorer_dashboard

#     return create_forum_explorer_dashboard()


# def save_feedback_to_db(data_id, inference_type, rating, feedback_text, response_id):
#     """Save feedback data to SQLite database"""
#     from utilities.mrpc_database import MRPCDatabase

#     db = MRPCDatabase()
#     return db.save_inference_feedback(
#         data_id, inference_type, rating, feedback_text, response_id
#     )


if __name__ == "__main__":
    pass
