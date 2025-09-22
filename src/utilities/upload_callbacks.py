"""
Upload Page Callbacks
Handles all interactive functionality for the upload page
"""

from dash import Input, Output, State, no_update, ALL, ctx
import dash_bootstrap_components as dbc
from dash import html
from utilities.upload_service import upload_service


def create_upload_type_badge(upload_type):
    """Create a badge for upload type display"""
    if upload_type == "forum_data":
        return dbc.Badge("Forum Data", color="info", className="me-1")
    elif upload_type == "transcription_data":
        return dbc.Badge("Transcription Data", color="warning", className="me-1")
    else:
        return dbc.Badge("❓ Unknown", color="secondary", className="me-1")


def create_type_specific_info(upload):
    """Create type-specific information display"""
    upload_type = upload.get("upload_type", "forum_data")

    if upload_type == "transcription_data":
        return html.Div(
            [
                html.Hr(),
                html.H6("Transcription Data Details", className="text-warning"),
                html.P(
                    "Experimental session data with 15 structured fields",
                    className="small text-muted",
                ),
                html.P(
                    [
                        html.Strong("Data Categories: "),
                        "Digital Access, Emotional Response, Information Quality, Behavioral Outcomes, Support Systems",
                    ],
                    className="small",
                ),
            ]
        )
    elif upload_type == "forum_data":
        return html.Div(
            [
                html.Hr(),
                html.H6("📋 Forum Data Details", className="text-info"),
                html.P(
                    "Forum discussion posts with UMAP clustering",
                    className="small text-muted",
                ),
                html.P(
                    [
                        html.Strong("Includes: "),
                        "Posts, titles, cluster assignments, AI-inferred questions",
                    ],
                    className="small",
                ),
            ]
        )
    else:
        return html.Div()


def create_upload_statistics_cards(stats):
    """Create statistics cards for upload overview with type breakdown"""
    if not stats:
        return html.P("No upload statistics available")

    # Get type-specific stats if available
    forum_stats = stats.get("forum_data", {})
    transcription_stats = stats.get("transcription_data", {})

    total_uploads = stats.get("total_uploads", 0)
    total_records = stats.get("total_records", 0)

    forum_uploads = forum_stats.get("upload_count", 0)
    forum_records = forum_stats.get("total_records", 0)

    transcription_uploads = transcription_stats.get("upload_count", 0)
    transcription_records = transcription_stats.get("total_records", 0)

    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(
                                        total_uploads,
                                        className="text-primary",
                                    ),
                                    html.P("Total Uploads", className="mb-1"),
                                    html.Small(
                                        f"Forum: {forum_uploads} | Transcription: {transcription_uploads}",
                                        className="text-muted",
                                    ),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(
                                        total_records,
                                        className="text-success",
                                    ),
                                    html.P("Total Records", className="mb-1"),
                                    html.Small(
                                        f"Forum: {forum_records} | Transcription: {transcription_records}",
                                        className="text-muted",
                                    ),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(
                                        stats.get("recent_uploads", 0),
                                        className="text-info",
                                    ),
                                    html.P("Recent (7 days)", className="mb-1"),
                                    html.Small("Forum | Lorem Ipsum"),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(
                                        len(stats.get("by_status", {})),
                                        className="text-warning",
                                    ),
                                    html.P("Status Types", className="mb-0"),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            ),
        ]
    )


def create_upload_history_table_component(uploads):
    """Create the upload history table with status-based actions"""
    if not uploads:
        return dbc.Alert(
            "No uploads found. Upload your first dataset above!",
            color="info",
            className="text-center",
        )

    # Create table rows
    table_rows = []
    for upload in uploads:
        status = upload.get("status", "unknown")
        status_style = upload.get("status_style", {"color": "secondary", "icon": "❓"})

        # Create status-based action buttons
        action_buttons = []

        # View button (always available)
        action_buttons.append(
            dbc.Button(
                "View",
                id={
                    "type": "view-upload-btn",
                    "index": upload["id"],
                },
                color="info",
                size="sm",
                className="me-1",
            )
        )

        # Status-specific actions
        if status == "active":
            action_buttons.append(
                dbc.Button(
                    " Archive",
                    id={
                        "type": "archive-upload-btn",
                        "index": upload["id"],
                    },
                    color="warning",
                    size="sm",
                    outline=True,
                )
            )
        elif status == "archived":
            action_buttons.extend(
                [
                    dbc.Button(
                        "🔄 Restore",
                        id={
                            "type": "restore-upload-btn",
                            "index": upload["id"],
                        },
                        color="success",
                        size="sm",
                        outline=True,
                        className="me-1",
                    ),
                    dbc.Button(
                        "🗑️ Delete",
                        id={
                            "type": "delete-upload-btn",
                            "index": upload["id"],
                        },
                        color="danger",
                        size="sm",
                        outline=True,
                    ),
                ]
            )
        elif status == "deleted":
            action_buttons.append(
                dbc.Button(
                    "🔥 Permanent Delete",
                    id={
                        "type": "permanent-delete-upload-btn",
                        "index": upload["id"],
                    },
                    color="danger",
                    size="sm",
                    title="Admin only - permanently remove all data",
                )
            )

        table_rows.append(
            html.Tr(
                [
                    html.Td(upload.get("user_readable_name", "Unknown")),
                    html.Td(upload.get("filename", "Unknown")),
                    html.Td(upload.get("uploader_name", "Unknown")),
                    html.Td(
                        upload.get("upload_date", "Unknown")[:19]
                        if upload.get("upload_date")
                        else "Unknown"
                    ),
                    html.Td(upload.get("records_count", 0)),
                    html.Td(
                        dbc.Badge(
                            "📊" if upload.get("upload_type") == "forum_data" else "🧪",
                            color="info"
                            if upload.get("upload_type") == "forum_data"
                            else "warning",
                            title=upload.get("upload_type", "forum_data")
                            .replace("_", " ")
                            .title(),
                            className="me-1",
                        )
                    ),
                    html.Td(
                        dbc.Badge(
                            f"{status_style['icon']} {status.title()}",
                            color=status_style["color"],
                            className="fs-6",
                        )
                    ),
                    html.Td(dbc.ButtonGroup(action_buttons, className="btn-group-sm")),
                ]
            )
        )

    return dbc.Table(
        [
            html.Thead(
                [
                    html.Tr(
                        [
                            html.Th("Dataset Name"),
                            html.Th("Filename"),
                            html.Th("Uploaded By"),
                            html.Th("Upload Date"),
                            html.Th("Records"),
                            html.Th("Type"),
                            html.Th("Status"),
                            html.Th("Actions"),
                        ]
                    )
                ]
            ),
            html.Tbody(table_rows),
        ],
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
    )


def create_upload_preview_card(filename, validation_result, detected_type=None):
    """Create preview card for uploaded file with type detection"""
    if not validation_result["success"]:
        return dbc.Alert(
            [html.H6("❌ Validation Failed"), html.P(validation_result["message"])],
            color="danger",
        )

    preview_data = validation_result.get("preview_data", [])
    total_rows = validation_result.get("total_rows", 0)
    columns = validation_result.get("columns", [])

    # Create type detection badge
    type_badge = ""
    if detected_type:
        if detected_type == "forum_data":
            type_badge = dbc.Badge(
                "Forum Data Detected", color="info", className="mb-2"
            )
        elif detected_type == "transcription_data":
            type_badge = dbc.Badge(
                "Transcription Data Detected", color="warning", className="mb-2"
            )
        else:
            type_badge = dbc.Badge(
                "❓ Unknown Data Type", color="secondary", className="mb-2"
            )

    return dbc.Card(
        [
            dbc.CardHeader([html.H6(f"📋 Preview: {filename}")]),
            dbc.CardBody(
                [
                    type_badge,
                    html.P(f"Total rows: {total_rows}"),
                    html.P(f"Columns: {len(columns)}"),
                    html.Details(
                        [
                            html.Summary(
                                "📋 Column List",
                                style={"cursor": "pointer", "fontWeight": "bold"},
                            ),
                            html.Div(
                                [
                                    html.P(
                                        ", ".join(columns[:10])
                                        + ("..." if len(columns) > 10 else ""),
                                        className="small text-muted mt-2",
                                    )
                                ]
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.H6("First 3 rows:"),
                    html.Div(
                        [html.Pre(str(preview_data[:3]), style={"fontSize": "12px"})]
                    )
                    if preview_data
                    else html.P("No preview data available"),
                ]
            ),
        ],
        className="mt-3",
    )


def register_upload_callbacks(app):
    """Register all upload page callbacks"""

    @app.callback(
        [
            Output("upload-form-container", "style"),
            Output("upload-type-container", "style"),
        ],
        [Input("upload-data", "contents")],
        [State("upload-data", "filename")],
    )
    def handle_file_upload(contents, filename):
        """Handle file upload and show preview with type detection"""
        if contents is None:
            return {"display": "none"}, {"display": "none"}

        try:
            # Preview the uploaded file
            preview_result = upload_service.preview_csv(contents, rows=3)

            if preview_result["success"]:
                # Auto-detect upload type
                df = upload_service._parse_csv_contents(contents)
                detected_type = upload_service.detect_upload_type(df)

                # Create enhanced preview card with type detection
                preview_card = create_upload_preview_card(
                    filename, preview_result, detected_type
                )

                # Show upload type selector and form
                type_container_style = {"display": "block"}
                form_style = {"display": "block"}
            else:
                # Show error
                preview_card = create_upload_preview_card(filename, preview_result)
                type_container_style = {"display": "none"}
                form_style = {"display": "none"}

            return form_style, type_container_style

        except Exception as e:
            error_card = dbc.Alert(
                [html.H6("❌ Error Processing File"), html.P(f"Error: {str(e)}")],
                color="danger",
            )

            return {"display": "none"}, error_card, {"display": "none"}

    @app.callback(
        Output("upload-type-info", "children"),
        [Input("upload-type-selector", "value")],
    )
    def update_upload_type_info(selected_type):
        """Update upload type information card"""
        if selected_type == "forum_data":
            return dbc.Alert(
                [
                    html.H6("Forum Data Requirements", className="alert-heading"),
                    html.P("Required columns: forum, original_title, original_post"),
                    html.P(
                        "Optional columns: cluster, llm_inferred_question, umap coordinates"
                    ),
                    html.Small(
                        "This data will be used for forum analysis and UMAP visualization."
                    ),
                ],
                color="info",
                className="mt-2",
            )
        elif selected_type == "transcription_data":
            return dbc.Alert(
                [
                    html.H6(
                        "Transcription Data Requirements", className="alert-heading"
                    ),
                    html.P("Required: ALL 15 experimental fields must be present"),
                    html.Ul(
                        [
                            html.Li("Core: session_id, participant_id"),
                            html.Li(
                                "Digital Access: zoom_ease, poll_usability, resource_access"
                            ),
                            html.Li(
                                "Emotional Response: presession_anxiety, reassurance_provided"
                            ),
                            html.Li(
                                "Information Quality: info_useful, info_missing, info_takeaway_desired"
                            ),
                            html.Li(
                                "Behavioral Outcomes: exercise_engaged, lifestyle_change, postop_adherence"
                            ),
                            html.Li("Support Systems: family_involved, support_needed"),
                        ]
                    ),
                    html.Small(
                        "Boolean fields accept: True/False, Yes/No, 1/0, Y/N formats"
                    ),
                    html.Br(),
                    html.Small(
                        "Likert fields (1-5): poll_usability, presession_anxiety, reassurance_provided, info_useful"
                    ),
                ],
                color="warning",
                className="mt-2",
            )

        return ""

    @app.callback(
        Output("upload-alerts", "children"),
        [Input("upload-submit-btn", "n_clicks")],
        [
            State("upload-data", "contents"),
            State("upload-data", "filename"),
            State("upload-name", "value"),
            State("upload-comment", "value"),
            State("upload-type-selector", "value"),
        ],
        prevent_initial_call=True,
    )
    def process_upload(
        n_clicks, contents, filename, upload_name, comment, selected_type
    ):
        """Process the actual file upload with type selection"""
        if not n_clicks or not contents or not upload_name:
            return no_update

        try:
            # Process the upload with explicit type selection
            result = upload_service.process_file_upload(
                contents=contents,
                filename=filename,
                user_readable_name=upload_name,
                comment=comment or "",
                expected_type=selected_type,  # Pass the user-selected type
            )

            if result["success"]:
                # Enhanced success message based on upload type
                if selected_type == "transcription_data":
                    success_icon = "🧪"
                    success_title = "Transcription Data Upload Successful!"
                    data_info = f"Experimental session data processed with {result.get('new_records', 0)} records"
                else:
                    success_icon = "📊"
                    success_title = "Forum Data Upload Successful!"
                    data_info = f"Forum analysis data processed with {result.get('new_records', 0)} records"

                alert = dbc.Alert(
                    [
                        html.H4(
                            f"{success_icon} {success_title}", className="alert-heading"
                        ),
                        html.P(data_info),
                        html.Hr(),
                        html.P(
                            [
                                f"Upload ID: {result.get('upload_id', 'Unknown')} | ",
                                f"Data Type: {selected_type.replace('_', ' ').title()} | ",
                                f"New Records: {result.get('new_records', 0)} | ",
                                f"Duplicates Skipped: {result.get('duplicates_skipped', 0)}",
                            ],
                            className="mb-0",
                        ),
                    ],
                    color="success",
                    dismissable=True,
                )
            else:
                # Enhanced error message based on upload type
                if selected_type == "transcription_data":
                    error_icon = "🧪❌"
                    error_title = "Transcription Data Validation Failed"
                    error_context = "Please ensure all 15 experimental fields are present and correctly formatted."
                else:
                    error_icon = "📊❌"
                    error_title = "Forum Data Validation Failed"
                    error_context = (
                        "Please check the required forum data columns and format."
                    )

                alert = dbc.Alert(
                    [
                        html.H4(
                            f"{error_icon} {error_title}", className="alert-heading"
                        ),
                        html.P(error_context),
                        html.Hr(),
                        html.P(result["message"]),
                        html.Small(
                            f"Selected Type: {selected_type.replace('_', ' ').title()}",
                            className="text-muted",
                        ),
                    ],
                    color="danger",
                    dismissable=True,
                )

            return alert

        except Exception as e:
            error_alert = dbc.Alert(
                [
                    html.H4("❌ Unexpected Error", className="alert-heading"),
                    html.P(f"An unexpected error occurred: {str(e)}"),
                    html.Small(
                        f"Selected Type: {selected_type.replace('_', ' ').title()}",
                        className="text-muted",
                    ),
                ],
                color="danger",
                dismissable=True,
            )

            return error_alert

    @app.callback(
        [
            Output("upload-form-container", "style", allow_duplicate=True),
            Output("upload-type-container", "style", allow_duplicate=True),
            Output("upload-name", "value"),
            Output("upload-comment", "value"),
            Output("upload-type-selector", "value"),
        ],
        [Input("upload-cancel-btn", "n_clicks")],
        prevent_initial_call=True,
    )
    def cancel_upload(n_clicks):
        """Cancel the upload and reset form"""
        if not n_clicks:
            return no_update

        return {"display": "none"}, {"display": "none"}, "", "", "forum_data"

    @app.callback(
        [
            Output("upload-stats", "children"),
            Output("upload-history-table", "children"),
        ],
        [
            Input("refresh-uploads-btn", "n_clicks"),
            Input("upload-alerts", "children"),
            Input("filter-all-btn", "n_clicks"),
            Input("filter-active-btn", "n_clicks"),
            Input("filter-archived-btn", "n_clicks"),
            Input("filter-deleted-btn", "n_clicks"),
            Input("filter-all-types-btn", "n_clicks"),
            Input("filter-forum-btn", "n_clicks"),
            Input("filter-transcription-btn", "n_clicks"),
        ],
        [
            State("current-status-filter", "data"),
            State("current-type-filter", "data"),
        ],
        prevent_initial_call=False,
    )
    def refresh_upload_history(
        refresh_clicks,
        upload_alerts,
        all_clicks,
        active_clicks,
        archived_clicks,
        deleted_clicks,
        all_types_clicks,
        forum_clicks,
        transcription_clicks,
        current_status_filter,
        current_type_filter,
    ):
        """Refresh upload history and statistics with status and type filtering"""
        try:
            # Determine which filter was clicked
            triggered = ctx.triggered_id if ctx.triggered else None

            # Status filter logic
            if triggered == "filter-all-btn":
                status_filter = None
            elif triggered == "filter-active-btn":
                status_filter = "active"
            elif triggered == "filter-archived-btn":
                status_filter = "archived"
            elif triggered == "filter-deleted-btn":
                status_filter = "deleted"
            else:
                # Use current status filter or default to all
                status_filter = (
                    current_status_filter if current_status_filter != "all" else None
                )

            # Type filter logic
            if triggered == "filter-all-types-btn":
                type_filter = None
            elif triggered == "filter-forum-btn":
                type_filter = "forum_data"
            elif triggered == "filter-transcription-btn":
                type_filter = "transcription_data"
            else:
                # Use current type filter or default to all
                type_filter = (
                    current_type_filter if current_type_filter != "all" else None
                )

            # Get upload statistics (always show all for stats)
            stats = upload_service.get_upload_statistics()
            stats_cards = create_upload_statistics_cards(stats)

            # Get user uploads with both filters
            uploads = upload_service.get_user_uploads(
                status=status_filter, upload_type=type_filter
            )
            upload_table = create_upload_history_table_component(uploads)

            return stats_cards, upload_table

        except Exception as e:
            error_msg = dbc.Alert(
                f"Error loading upload history: {str(e)}", color="warning"
            )
            return error_msg, error_msg

    @app.callback(
        Output("current-status-filter", "data"),
        [
            Input("filter-all-btn", "n_clicks"),
            Input("filter-active-btn", "n_clicks"),
            Input("filter-archived-btn", "n_clicks"),
            Input("filter-deleted-btn", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def update_status_filter(
        all_clicks, active_clicks, archived_clicks, deleted_clicks
    ):
        """Update the current status filter"""
        triggered = ctx.triggered_id if ctx.triggered else None

        if triggered == "filter-all-btn":
            return "all"
        elif triggered == "filter-active-btn":
            return "active"
        elif triggered == "filter-archived-btn":
            return "archived"
        elif triggered == "filter-deleted-btn":
            return "deleted"
        else:
            return "all"

    @app.callback(
        Output("current-type-filter", "data"),
        [
            Input("filter-all-types-btn", "n_clicks"),
            Input("filter-forum-btn", "n_clicks"),
            Input("filter-transcription-btn", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def update_type_filter(all_types_clicks, forum_clicks, transcription_clicks):
        """Update the current type filter"""
        triggered = ctx.triggered_id if ctx.triggered else None

        if triggered == "filter-all-types-btn":
            return "all"
        elif triggered == "filter-forum-btn":
            return "forum_data"
        elif triggered == "filter-transcription-btn":
            return "transcription_data"
        else:
            return "all"

    @app.callback(
        [
            Output("filter-all-btn", "outline"),
            Output("filter-active-btn", "outline"),
            Output("filter-archived-btn", "outline"),
            Output("filter-deleted-btn", "outline"),
        ],
        Input("current-status-filter", "data"),
        prevent_initial_call=False,
    )
    def update_filter_button_styles(current_filter):
        """Update filter button styles based on current selection"""
        return [
            current_filter != "all",  # All button
            current_filter != "active",  # Active button
            current_filter != "archived",  # Archived button
            current_filter != "deleted",  # Deleted button
        ]

    @app.callback(
        [
            Output("filter-all-types-btn", "outline"),
            Output("filter-forum-btn", "outline"),
            Output("filter-transcription-btn", "outline"),
        ],
        Input("current-type-filter", "data"),
        prevent_initial_call=False,
    )
    def update_type_filter_button_styles(current_type_filter):
        """Update type filter button styles based on current selection"""
        return [
            current_type_filter != "all",  # All types button
            current_type_filter != "forum_data",  # Forum button
            current_type_filter != "transcription_data",  # Transcription button
        ]

    @app.callback(
        [
            Output("upload-details-modal", "is_open"),
            Output("upload-details-content", "children"),
        ],
        [
            Input({"type": "view-upload-btn", "index": ALL}, "n_clicks"),
            Input("close-upload-details", "n_clicks"),
        ],
        [State("upload-details-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_upload_details_modal(view_clicks, close_clicks, is_open):
        """Show/hide upload details modal"""
        if not any(view_clicks or []) and not close_clicks:
            return no_update, no_update

        # Check which button was clicked
        if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
            if ctx.triggered_id["type"] == "view-upload-btn":
                upload_id = ctx.triggered_id["index"]

                try:
                    # Get upload details
                    from utilities.mrpc_database import MRPCDatabase

                    db = MRPCDatabase()
                    upload = db.get_upload_by_id(upload_id)

                    if upload:
                        details_content = create_upload_details_content(upload)
                        return True, details_content
                    else:
                        error_content = dbc.Alert("Upload not found", color="danger")
                        return True, error_content

                except Exception as e:
                    error_content = dbc.Alert(
                        f"Error loading upload details: {str(e)}", color="danger"
                    )
                    return True, error_content

        # Close modal
        return False, ""

    @app.callback(
        [
            Output("action-confirmation-modal", "is_open"),
            Output("action-modal-title", "children"),
            Output("action-confirmation-message", "children"),
            Output("action-upload-info", "children"),
            Output("confirm-action", "color"),
            Output("confirm-action", "children"),
            Output("pending-action-data", "data"),
        ],
        [
            Input({"type": "archive-upload-btn", "index": ALL}, "n_clicks"),
            Input({"type": "delete-upload-btn", "index": ALL}, "n_clicks"),
            Input({"type": "permanent-delete-upload-btn", "index": ALL}, "n_clicks"),
            Input("cancel-action", "n_clicks"),
        ],
        [State("action-confirmation-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_action_confirmation_modal(
        archive_clicks, delete_clicks, permanent_delete_clicks, cancel_clicks, is_open
    ):
        """Show/hide action confirmation modal for archive/delete operations"""
        if (
            not any(archive_clicks or [])
            and not any(delete_clicks or [])
            and not any(permanent_delete_clicks or [])
            and not cancel_clicks
        ):
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        # Check which button was clicked
        if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
            action_type = ctx.triggered_id["type"]
            upload_id = ctx.triggered_id["index"]

            try:
                # Get upload info for confirmation
                from utilities.mrpc_database import MRPCDatabase

                db = MRPCDatabase()
                upload = db.get_upload_by_id(upload_id)

                if upload:
                    upload_info = html.Div(
                        [
                            html.P(f"📁 Dataset: {upload['user_readable_name']}"),
                            html.P(f"📄 Filename: {upload['filename']}"),
                            html.P(f"Records: {upload['records_count']}"),
                            html.P(f"📅 Upload Date: {upload['upload_date'][:19]}"),
                        ]
                    )

                    if action_type == "archive-upload-btn":
                        return (
                            True,
                            " Archive Upload",
                            html.Div(
                                [
                                    html.P(
                                        "Are you sure you want to archive this upload?"
                                    ),
                                    html.P(
                                        "Archived uploads can be restored later but won't appear in active data analysis.",
                                        className="text-info",
                                    ),
                                ]
                            ),
                            upload_info,
                            "warning",
                            "Archive",
                            {"action": "archive", "upload_id": upload_id},
                        )

                    elif action_type == "delete-upload-btn":
                        return (
                            True,
                            "🗑️ Delete Upload",
                            html.Div(
                                [
                                    html.P(
                                        "Are you sure you want to delete this archived upload?"
                                    ),
                                    html.P(
                                        "Deleted uploads can only be permanently removed by administrators.",
                                        className="text-warning",
                                    ),
                                    html.P(
                                        "This action moves the upload to deleted status.",
                                        className="text-danger fw-bold",
                                    ),
                                ]
                            ),
                            upload_info,
                            "danger",
                            "Delete",
                            {"action": "delete", "upload_id": upload_id},
                        )

                    elif action_type == "permanent-delete-upload-btn":
                        return (
                            True,
                            "🔥 Permanent Delete",
                            html.Div(
                                [
                                    html.P(
                                        "⚠️ PERMANENT DELETION - This action cannot be undone!"
                                    ),
                                    html.P(
                                        "This will permanently remove the upload and ALL associated data from the system.",
                                        className="text-danger fw-bold",
                                    ),
                                    html.P(
                                        "This is an admin-only operation.",
                                        className="text-info",
                                    ),
                                ]
                            ),
                            upload_info,
                            "danger",
                            "🔥 Permanent Delete",
                            {"action": "permanent_delete", "upload_id": upload_id},
                        )
                else:
                    error_info = dbc.Alert("Upload not found", color="danger")
                    return True, "Error", "", error_info, "secondary", "Close", {}

            except Exception as e:
                error_info = dbc.Alert(
                    f"Error loading upload info: {str(e)}", color="danger"
                )
                return True, "Error", "", error_info, "secondary", "Close", {}

        # Close modal (cancel)
        return False, "", "", "", "secondary", "Confirm", {}

    @app.callback(
        [
            Output("restore-confirmation-modal", "is_open"),
            Output("restore-upload-info", "children"),
            Output("pending-action-data", "data", allow_duplicate=True),
        ],
        [
            Input({"type": "restore-upload-btn", "index": ALL}, "n_clicks"),
            Input("cancel-restore", "n_clicks"),
        ],
        [State("restore-confirmation-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_restore_confirmation_modal(restore_clicks, cancel_clicks, is_open):
        """Show/hide restore confirmation modal"""
        if not any(restore_clicks or []) and not cancel_clicks:
            return no_update, no_update, no_update

        # Check which button was clicked
        if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
            if ctx.triggered_id["type"] == "restore-upload-btn":
                upload_id = ctx.triggered_id["index"]

                try:
                    # Get upload info for confirmation
                    from utilities.mrpc_database import MRPCDatabase

                    db = MRPCDatabase()
                    upload = db.get_upload_by_id(upload_id)

                    if upload:
                        restore_info = html.Div(
                            [
                                html.P(f"📁 Dataset: {upload['user_readable_name']}"),
                                html.P(f"📄 Filename: {upload['filename']}"),
                                html.P(f"Records: {upload['records_count']}"),
                                html.P(f"📅 Upload Date: {upload['upload_date'][:19]}"),
                            ]
                        )
                        # Store the restore action data
                        return (
                            True,
                            restore_info,
                            {"action": "restore", "upload_id": upload_id},
                        )
                    else:
                        error_info = dbc.Alert("Upload not found", color="danger")
                        return True, error_info, {}

                except Exception as e:
                    error_info = dbc.Alert(
                        f"Error loading upload info: {str(e)}", color="danger"
                    )
                    return True, error_info, {}

        # Close modal (cancel)
        return False, "", {}

    @app.callback(
        Output("upload-alerts", "children", allow_duplicate=True),
        [
            Input("confirm-action", "n_clicks"),
            Input("confirm-restore", "n_clicks"),
        ],
        [State("pending-action-data", "data")],
        prevent_initial_call=True,
    )
    def execute_upload_action(
        confirm_action_clicks, confirm_restore_clicks, pending_action
    ):
        """Execute the confirmed upload action (archive/delete/permanent delete/restore)"""
        if not confirm_action_clicks and not confirm_restore_clicks:
            return no_update

        try:
            if confirm_action_clicks and pending_action:
                action = pending_action.get("action")
                upload_id = pending_action.get("upload_id")

                if action == "archive":
                    result = upload_service.archive_upload(upload_id)
                    action_name = "Archive"
                    success_icon = ""
                elif action == "delete":
                    result = upload_service.delete_upload(upload_id)
                    action_name = "Delete"
                    success_icon = "🗑️"
                elif action == "permanent_delete":
                    result = upload_service.delete_upload_permanent(upload_id)
                    action_name = "Permanent Delete"
                    success_icon = "🔥"
                else:
                    return dbc.Alert("Unknown action", color="danger", dismissable=True)

            elif confirm_restore_clicks and pending_action:
                action = pending_action.get("action")
                upload_id = pending_action.get("upload_id")

                if action == "restore":
                    result = upload_service.restore_upload(upload_id)
                    action_name = "Restore"
                    success_icon = "🔄"
                else:
                    return dbc.Alert(
                        "Invalid restore action", color="danger", dismissable=True
                    )
            else:
                return no_update

            # Handle the result
            if result["success"]:
                alert = dbc.Alert(
                    [
                        html.H4(
                            f"{success_icon} {action_name} Successful!",
                            className="alert-heading",
                        ),
                        html.P(result["message"]),
                    ],
                    color="success",
                    dismissable=True,
                )
            else:
                alert = dbc.Alert(
                    [
                        html.H4(f"❌ {action_name} Failed", className="alert-heading"),
                        html.P(result["message"]),
                    ],
                    color="danger",
                    dismissable=True,
                )

            return alert

        except Exception as e:
            error_alert = dbc.Alert(
                [
                    html.H4("❌ Action Error", className="alert-heading"),
                    html.P(f"Error executing action: {str(e)}"),
                ],
                color="danger",
                dismissable=True,
            )
            return error_alert

    @app.callback(
        Output("action-confirmation-modal", "is_open", allow_duplicate=True),
        [
            Input("confirm-action", "n_clicks"),
            Input("cancel-action", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def close_action_confirmation_modal(confirm_clicks, cancel_clicks):
        """Close action confirmation modal after action is confirmed or canceled"""
        if confirm_clicks or cancel_clicks:
            return False
        return no_update

    @app.callback(
        Output("restore-confirmation-modal", "is_open", allow_duplicate=True),
        [
            Input("confirm-restore", "n_clicks"),
            Input("cancel-restore", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def close_restore_confirmation_modal(confirm_clicks, cancel_clicks):
        """Close restore confirmation modal after action is confirmed or canceled"""
        if confirm_clicks or cancel_clicks:
            return False
        return no_update


def create_upload_details_content(upload):
    """Create detailed content for upload details modal"""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Upload Information"),
                            html.Hr(),
                            html.P(
                                [
                                    html.Strong("Dataset Name: "),
                                    upload.get("user_readable_name", "Unknown"),
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Filename: "),
                                    upload.get("filename", "Unknown"),
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Uploaded By: "),
                                    upload.get("uploader_name", "Unknown"),
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Upload Date: "),
                                    upload.get("upload_date", "Unknown"),
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Records Count: "),
                                    str(upload.get("records_count", 0)),
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Upload Type: "),
                                    create_upload_type_badge(
                                        upload.get("upload_type", "forum_data")
                                    ),
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Status: "),
                                    upload.get("status", "unknown").title(),
                                ]
                            ),
                            # Type-specific information
                            create_type_specific_info(upload),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.H5("Upload Details"),
                            html.Hr(),
                            html.P(
                                [
                                    html.Strong("Upload ID: "),
                                    str(upload.get("id", "Unknown")),
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Comment: "),
                                    upload.get("comment", "No comment provided"),
                                ]
                            ),
                            html.Div(
                                [
                                    html.H6("Actions", className="mt-3"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "View Data", color="info", size="sm"
                                            ),
                                            dbc.Button(
                                                "Download", color="secondary", size="sm"
                                            ),
                                            dbc.Button(
                                                "Delete", color="danger", size="sm"
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=6,
                    ),
                ]
            )
        ]
    )
