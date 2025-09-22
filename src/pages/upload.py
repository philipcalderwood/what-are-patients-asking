"""
Upload Page for MRPC Forum Data
Provides file upload interface and upload history management
"""

from dash import register_page, html, dcc
import dash_bootstrap_components as dbc

register_page(__name__, path="/upload", name="Upload")


def layout():
    """Create the upload page layout"""

    return html.Div(
        [
            # Main container
            dbc.Container(
                [
                    dcc.Markdown(
                        """

                                 `This page is a bit more WIP`
                                 """,
                        className="text-center",
                    ),
                    # Page title
                    html.H1("Data Upload Management", className="mb-4 text-center"),
                    # Upload section
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [html.H4("Upload New Dataset", className="mb-0")]
                            ),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    # File upload component
                                                    dcc.Upload(
                                                        id="upload-data",
                                                        children=[
                                                            "Drag and Drop CSV file or ",
                                                            html.A(
                                                                "Select a File",
                                                                style={
                                                                    "textDecoration": "underline",
                                                                    "cursor": "pointer",
                                                                },
                                                            ),
                                                        ],
                                                        style={
                                                            "width": "100%",
                                                            "height": "80px",
                                                            "lineHeight": "80px",
                                                            "borderWidth": "2px",
                                                            "borderStyle": "dashed",
                                                            "borderRadius": "8px",
                                                            "textAlign": "center",
                                                            "margin": "10px 0",
                                                            "backgroundColor": "#f8f9fa",
                                                            "cursor": "pointer",
                                                            "color": "#666",
                                                        },
                                                        style_active={
                                                            "borderStyle": "solid",
                                                            "borderColor": "#007bff",
                                                            "backgroundColor": "#e7f3ff",
                                                        },
                                                        style_reject={
                                                            "borderStyle": "solid",
                                                            "borderColor": "#dc3545",
                                                            "backgroundColor": "#f8d7da",
                                                        },
                                                        accept=".csv",
                                                        multiple=False,
                                                    ),
                                                    # File format info
                                                    html.Small(
                                                        "Supported format: CSV files only",
                                                        className="text-muted d-block mt-2",
                                                    ),
                                                    # Upload type selector
                                                    html.Div(
                                                        id="upload-type-container",
                                                        style={"display": "none"},
                                                        className="mt-3",
                                                        children=[
                                                            dbc.Label(
                                                                "Data Type Selection",
                                                                className="fw-bold mb-2",
                                                            ),
                                                            dbc.RadioItems(
                                                                id="upload-type-selector",
                                                                options=[
                                                                    {
                                                                        "label": "Forum Data (Questions, Posts, UMAP coordinates)",
                                                                        "value": "forum_data",
                                                                    },
                                                                    {
                                                                        "label": "Transcription Data (Experimental session data)",
                                                                        "value": "transcription_data",
                                                                    },
                                                                ],
                                                                value="forum_data",
                                                                inline=False,
                                                                className="mb-2",
                                                            ),
                                                            # Upload type info card
                                                            html.Div(
                                                                id="upload-type-info"
                                                            ),
                                                        ],
                                                    ),
                                                    # Upload form
                                                    html.Div(
                                                        id="upload-form-container",
                                                        style={"display": "none"},
                                                        children=[
                                                            html.Hr(),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Dataset Name *",
                                                                                html_for="upload-name",
                                                                            ),
                                                                            dbc.Input(
                                                                                id="upload-name",
                                                                                type="text",
                                                                                placeholder="Give this upload a descriptive name...",
                                                                                required=True,
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Upload Comment",
                                                                                html_for="upload-comment",
                                                                            ),
                                                                            dbc.Textarea(
                                                                                id="upload-comment",
                                                                                placeholder="Add a comment about this upload...",
                                                                                rows=3,
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ]
                                                            ),
                                                            html.Div(
                                                                className="mt-3",
                                                                children=[
                                                                    dbc.Button(
                                                                        "Upload & Process",
                                                                        id="upload-submit-btn",
                                                                        color="primary",
                                                                        size="lg",
                                                                        className="me-2",
                                                                    ),
                                                                    dbc.Button(
                                                                        "Cancel",
                                                                        id="upload-cancel-btn",
                                                                        color="secondary",
                                                                        size="lg",
                                                                        outline=True,
                                                                    ),
                                                                ],
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                                width=12,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Upload status alerts
                    html.Div(id="upload-alerts"),
                    # Upload history section
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.H4(
                                                        "Upload History",
                                                        className="mb-0",
                                                    )
                                                ],
                                                width=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Small(
                                                        "Filter by Status:",
                                                        className="text-muted d-block mb-1",
                                                    ),
                                                    dbc.ButtonGroup(
                                                        [
                                                            dbc.Button(
                                                                "All",
                                                                id="filter-all-btn",
                                                                color="primary",
                                                                size="sm",
                                                                outline=False,
                                                            ),
                                                            dbc.Button(
                                                                "Active",
                                                                id="filter-active-btn",
                                                                color="success",
                                                                size="sm",
                                                                outline=True,
                                                            ),
                                                            dbc.Button(
                                                                "Archived",
                                                                id="filter-archived-btn",
                                                                color="warning",
                                                                size="sm",
                                                                outline=True,
                                                            ),
                                                            dbc.Button(
                                                                "Deleted",
                                                                id="filter-deleted-btn",
                                                                color="danger",
                                                                size="sm",
                                                                outline=True,
                                                            ),
                                                        ],
                                                        className="me-2",
                                                    ),
                                                ],
                                                width=4,
                                                className="text-center",
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Small(
                                                        "Filter by Type:",
                                                        className="text-muted d-block mb-1",
                                                    ),
                                                    dbc.ButtonGroup(
                                                        [
                                                            dbc.Button(
                                                                "All Types",
                                                                id="filter-all-types-btn",
                                                                color="info",
                                                                size="sm",
                                                                outline=False,
                                                            ),
                                                            dbc.Button(
                                                                "Forum",
                                                                id="filter-forum-btn",
                                                                color="info",
                                                                size="sm",
                                                                outline=True,
                                                            ),
                                                            dbc.Button(
                                                                "Transcription",
                                                                id="filter-transcription-btn",
                                                                color="warning",
                                                                size="sm",
                                                                outline=True,
                                                            ),
                                                        ],
                                                        className="me-2",
                                                    ),
                                                ],
                                                width=3,
                                                className="text-center",
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Small(
                                                        "Actions:",
                                                        className="text-muted d-block mb-1",
                                                    ),
                                                    dbc.Button(
                                                        "Refresh",
                                                        id="refresh-uploads-btn",
                                                        color="outline-primary",
                                                        size="sm",
                                                    ),
                                                ],
                                                width=2,
                                                className="text-end",
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            dbc.CardBody(
                                [
                                    # Upload statistics
                                    html.Div(id="upload-stats", className="mb-3"),
                                    # Upload history table
                                    html.Div(id="upload-history-table"),
                                ]
                            ),
                        ]
                    ),
                ],
                className="py-4",
            ),
            # Upload details modal
            create_upload_details_modal(),
            # Action confirmation modal (Archive/Delete)
            create_delete_confirmation_modal(),
            # Restore confirmation modal
            create_restore_confirmation_modal(),
            # Store for current filter
            dcc.Store(id="current-status-filter", data="all"),
            # Store for current type filter
            dcc.Store(id="current-type-filter", data="all"),
            # Store for pending action
            dcc.Store(id="pending-action-data", data={}),
        ],
        className="h-100",
    )


def create_upload_details_modal():
    """Create modal for viewing upload details"""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Upload Details")),
            dbc.ModalBody([html.Div(id="upload-details-content")]),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Close",
                        id="close-upload-details",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ]
            ),
        ],
        id="upload-details-modal",
        is_open=False,
        size="lg",
    )


def create_delete_confirmation_modal():
    """Create modal for archive/delete/restore confirmation"""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(id="action-modal-title")),
            dbc.ModalBody(
                [
                    html.Div(id="action-confirmation-message"),
                    html.Div(id="action-upload-info", className="mt-2"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="cancel-action",
                        color="secondary",
                        className="me-2",
                        n_clicks=0,
                    ),
                    dbc.Button("Confirm", id="confirm-action", n_clicks=0),
                ]
            ),
        ],
        id="action-confirmation-modal",
        is_open=False,
    )


def create_restore_confirmation_modal():
    """Create modal for restore confirmation"""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Restore Upload")),
            dbc.ModalBody(
                [
                    html.P(
                        "Are you sure you want to restore this upload to active status?"
                    ),
                    html.P(
                        "This will make the data available for analysis again.",
                        className="text-info",
                    ),
                    html.Div(id="restore-upload-info"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="cancel-restore",
                        color="secondary",
                        className="me-2",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        "Restore", id="confirm-restore", color="success", n_clicks=0
                    ),
                ]
            ),
        ],
        id="restore-confirmation-modal",
        is_open=False,
    )


# Upload callbacks will be registered separately to avoid circular imports
