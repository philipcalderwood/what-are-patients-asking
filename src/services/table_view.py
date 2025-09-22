import pandas as pd
from utilities.backend import get_forum_data
from config import TABLE_COLUMN_ORDER, DATATABLE_CELL_STYLE
import dash_bootstrap_components as dbc
from dash import html, dcc
import dash.dash_table as dash_table


def create_table_view(**kwargs) -> html.Div:
    """Create a data table view component with integrated reading pane

    Returns: html.Div(dbc.Card(DataTable))"""

    # Get data directly from database using new datatable format
    table_df = get_forum_data(
        datatable_format=True
    ).copy()  # Make a proper copy to avoid SettingWithCopyWarning
    print(table_df.columns)
    # Check if we got valid data
    if table_df.empty or len(table_df) == 0:
        print("⚠️ Warning: get_forum_data returned empty DataFrame")
        # Return a simple error message component
        return html.Div(
            [
                html.H5(
                    "No data available",
                    id="table-view-no-data-heading",
                    className="text-center text-muted p-4",
                ),
                html.P(
                    "This might be due to authentication issues or missing data.",
                    id="table-view-no-data-message",
                    className="text-center text-muted",
                ),
            ],
            id="table-view-no-data-container",
        )

    # Get unique forum values for the dropdown
    unique_forums = (
        sorted(table_df["forum"].unique()) if "forum" in table_df.columns else []
    )
    unique_topics = (
        sorted(table_df["llm_cluster_name"].unique())
        if "llm_cluster_name" in table_df.columns
        else []
    )
    forum_options = [{"label": "All Forums", "value": "all"}]
    forum_options.extend([{"label": forum, "value": forum} for forum in unique_forums])
    topic_options = [{"label": "All Topics", "value": "all"}]
    topic_options.extend([{"label": topic, "value": topic} for topic in unique_topics])

    # Convert newline-separated content to markdown for better display
    if "all_questions" in table_df.columns and "all_categories" in table_df.columns:

        def format_for_datatable(text):
            """Convert newline-separated text to markdown list format"""
            if not text or pd.isna(text):
                return ""
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if not lines:
                return ""
            # Create markdown list format
            return "\n".join([f"- {line}" for line in lines])

        table_df["all_questions"] = table_df["all_questions"].apply(
            format_for_datatable
        )
        table_df["all_categories"] = table_df["all_categories"].apply(
            format_for_datatable
        )

    # Format date_posted column for better display
    if "date_posted" in table_df.columns:
        # Convert to datetime and format nicely, handling errors gracefully
        try:
            # Convert to datetime first
            table_df["date_posted"] = pd.to_datetime(
                table_df["date_posted"], errors="coerce"
            )

            # Custom formatting function for ordinal dates
            def format_date_with_ordinal(dt):
                if pd.isna(dt):
                    return "N/A"

                # Get the day and add ordinal suffix
                day = dt.day
                if 4 <= day <= 20 or 24 <= day <= 30:
                    suffix = "th"
                else:
                    suffix = ["st", "nd", "rd"][day % 10 - 1]

                # Format: "29th Jan, 2025 21:36"
                return dt.strftime(f"{day}{suffix} %b, %Y %H:%M")

            # Apply the custom formatting
            table_df["date_posted"] = table_df["date_posted"].apply(
                format_date_with_ordinal
            )

        except Exception as e:
            print(f"Warning: Date formatting failed: {e}")
            # Keep original values if formatting fails
            pass

    # Create user-friendly column names mapping for the new 3-column datatable format
    column_mapping = {
        "original_title": "Title",
        "all_questions": "Questions",
        "all_categories": "Topics",
        # Keep legacy mappings for backward compatibility
        "id": "ID",
        "forum": "Forum",
        "post_type": "Post Type",
        "username": "Username",
        "post_url": "Post URL",
        "LLM_inferred_question": "Inferred Question",
        "cluster": "Cluster ID",
        "cluster_label": "Cluster Theme",
        "date_posted": "Date Posted",
        "llm_cluster_name": "Inferred Category",
    }

    # For datatable format, use the new 3-column layout
    if "all_questions" in table_df.columns and "all_categories" in table_df.columns:
        # New 3-column format: Title, Questions, Categories
        display_columns = ["original_title", "all_questions", "all_categories"]
    else:
        # Legacy format - use original column logic
        column_order = TABLE_COLUMN_ORDER
        umap_columns = [
            "umap_x",
            "umap_y",
            "umap_z",
            "umap_1",
            "umap_2",
            "umap_3",
            "original_post",
        ]
        display_columns = [
            col
            for col in column_order[:3]  # Only take the first 3 columns
            if col in table_df.columns and col not in umap_columns
        ]

    # Create columns configuration for DataTable with special formatting
    COLUMNS_CONFIG = []
    for col in display_columns:
        # Special configuration for multi-line content columns
        if col in ["all_questions", "all_categories"]:
            config = {
                "id": col,
                "name": column_mapping.get(col, col.replace("_", " ").title()),
                "deletable": False,  # Don't allow deleting columns
                "renamable": False,  # Don't allow renaming columns
                "presentation": "markdown",  # Enable markdown rendering for newlines
            }
        elif col == "date_posted":
            config = {
                "id": col,
                "name": "Date Posted",
                "deletable": False,  # Don't allow deleting columns
                "renamable": False,  # Don't allow renaming columns
                "type": "text",  # Keep as text since we've pre-formatted it
            }
        else:
            config = {
                "id": col,
                "name": column_mapping.get(col, col.replace("_", " ").title()),
                "deletable": False,  # Don't allow deleting columns
                "renamable": False,  # Don't allow renaming columns
            }

        COLUMNS_CONFIG.append(config)

    return html.Div(
        [
            # DataTable Card
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.I(
                                                className="fas fa-table me-2",
                                                id="table-view-header-icon",
                                            ),
                                            html.Span(
                                                "Data Table",
                                                className="fw-bold",
                                                id="table-view-header-text",
                                            ),
                                        ],
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                [
                                                    html.I(className="fas fa-cog me-1"),
                                                    "Table Controls",
                                                ],
                                                id="table-controls-modal-btn",
                                                color="light",
                                                outline=True,
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        width="auto",
                                        className="ms-auto",
                                    ),
                                ],
                                className="align-items-center",
                            ),
                        ],
                        className="py-3 px-4 bg-primary text-white",
                        id="table-view-card-header",
                    ),
                    dbc.CardBody(
                        [
                            dash_table.DataTable(
                                id="forum-data-table",
                                data=table_df.to_dict("records"),
                                columns=[
                                    {"name": "Title", "id": "original_title"},
                                    {
                                        "name": "All Questions",
                                        "id": "all_questions",
                                        "presentation": "markdown",
                                    },
                                    {
                                        "name": "All Categories",
                                        "id": "all_categories",
                                        "presentation": "markdown",
                                    },
                                ],
                                hidden_columns=[],
                                column_selectable=False,
                                page_action="none",  # Disable pagination to show all rows
                                sort_action="custom",
                                filter_action="custom",
                                row_selectable=False,
                                row_deletable=False,
                                markdown_options={
                                    "html": True,
                                    "link_target": "_blank",  # Open links in new tab
                                },
                                # fixed_rows={"headers": True}, # experiment to see if fixed headers fixes it
                                # virtualization=True,
                                style_cell_conditional=[
                                    {
                                        "if": {"column_id": "original_title"},
                                        "width": "30%",
                                        "overflow": "ellipsis",
                                        "whiteSpace": "normal",
                                        "font-size": "1.3rem",
                                        "vertical-align": "top",
                                        "fontWeight": "normal",
                                        "text-align": "left",
                                    },
                                    {
                                        "if": {"column_id": "all_questions"},
                                        "width": "40%",
                                        "text-align": "left",
                                        "vertical-align": "top",
                                        "font-size": "1rem",
                                        "color": "#666",
                                        "whiteSpace": "normal",  # Allow line breaks for markdown
                                        "height": "auto",  # Auto height for content
                                    },
                                    {
                                        "if": {"column_id": "all_categories"},
                                        "width": "30%",
                                        "whiteSpace": "normal",
                                        "text-align": "left",
                                        "vertical-align": "top",
                                        "font-size": "1.1rem",
                                        "height": "auto",  # Auto height for content
                                    },
                                ],
                                tooltip_duration=None,
                                css=[
                                    {"selector": ".show-hide", "rule": "display: none"},
                                    {
                                        "selector": ".previous-next-container",
                                        "rule": "display: none",
                                    },
                                    {  # this is absolutely vital code - dash table with frozen headers has fixed height of 500px which must be overriden inline
                                        "selector": ".dash-spreadsheet.dash-freeze-top, .dash-spreadsheet .dash-virtualized .dash-freeze-top",
                                        "rule": "max-height: 100%; overflow-y: scroll; scrollbar-width: none;",
                                    },
                                    {
                                        "selector": "table",
                                        "rule": "table-layout: auto",  # Allow dynamic sizing for markdown content
                                    },
                                    {
                                        "selector": ".dash-cell div",
                                        "rule": "height: auto !important; max-height: none !important;",  # Allow cells to expand
                                    },
                                ],
                            ),
                        ],
                        id="table-view-card-body",
                        className="p-0 d-flex flex-column flex-fill",  # Bootstrap flex body
                        style={
                            "overflow-y": "scroll",
                            "scrollbarWidth": "none",  # Prevent overflow
                        },
                    ),
                ],
                className="d-flex flex-column border shadow-sm rounded h-75",
                id="table-view-card",  # Bootstrap flex card
            ),
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.I(className="fas fa-book-open me-2"),
                            html.Span("Reading Pane", className="fw-bold"),
                        ],
                        className="py-3 px-4 border border-success  text-success",
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
                                    "font-size": "2.2rem",
                                },
                            )
                        ],
                        id="sidebar-reading-pane",
                        className="dbc p-2 overflow-auto mt-0 h-100 font-size-2-2rem",
                    ),
                ],
                style={
                    "border": "1px solid #dee2e6",
                    "border-radius": "0.375rem",
                    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "flex": "1 1 auto",  # Take all remaining space
                    "min-height": "0",
                    "margin-top": "1rem ",  # Allow flex shrinking
                },
                id="reading-pane-card",  # Standalone card appearance that grows
            ),
            # Table Controls Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        [
                            html.I(className="fas fa-cog me-2"),
                            "Table Controls",
                        ]
                    ),
                    dbc.ModalBody(
                        [
                            html.Label("Forum Filter:", className="fw-bold mb-2"),
                            dbc.Select(
                                id="table-forum-selector",
                                options=forum_options,
                                value="all",
                                className="mb-3",
                            ),
                            html.Label("Topics:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="table-topic-selector",
                                options=topic_options,
                                value="all",
                                className="dbc",
                                multi=True,
                            ),
                            html.Hr(),
                            html.P(
                                "Use the forum filter to narrow down the data shown in the table.",
                                className="text-muted small",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Close",
                                id="table-controls-modal-close",
                                color="secondary",
                                outline=True,
                            ),
                        ]
                    ),
                ],
                id="table-controls-modal",
                is_open=False,
                size="md",
            ),
        ],
        className="d-flex flex-column h-100",  # Bootstrap flex container
        id="table-view-container",
    )
