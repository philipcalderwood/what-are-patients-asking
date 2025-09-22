import dash_bootstrap_components as dbc
from dash import html


def create_unified_user_card(
    data_id,
    item_id,  # question_id or topic_id
    card_type,  # "question" or "topic"
    content_text="",
    notes_text="",
    card_number=1,
    mode="display",  # "edit" or "display"
):
    """
    Create a unified card component that can toggle between edit and display modes
    for both user questions and user topics - FIXED to work like feedback system
    """

    # Configuration based on card type
    config = {
        "question": {
            "title": f"User Question {card_number}",
            "header_color": "bg-primary",
            "content_label": "Question",
            "notes_label": "Category Notes",
            "save_text": "Save Question",
            "edit_text": "Edit Question",
        },
        "topic": {
            "title": f"User Topic {card_number}",
            "header_color": "bg-success",
            "content_label": "Topic",
            "notes_label": "Notes",
            "save_text": "Save Topic",
            "edit_text": "Edit Topic",
        },
    }

    card_config = config[card_type]

    # Create card header (same for both modes)
    card_header = dbc.CardHeader(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H6(
                                f"{card_config['title']}",
                                className="mb-0 text-white fw-bold",
                            ),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                html.I(className="fas fa-trash"),
                                id={
                                    "type": f"delete-user-{card_type}-btn",
                                    "item_id": data_id,
                                    f"{card_type}_id": item_id,
                                },
                                color="light",
                                outline=True,
                                size="sm",
                                className="btn-sm",
                            )
                        ],
                        width=4,
                        className="text-end",
                    ),
                ],
                className="align-items-center",
            ),
        ],
        className=f"py-3 px-4 {card_config['header_color']} text-white",
    )

    # Create card body - LIKE FEEDBACK SYSTEM: ALL COMPONENTS EXIST TOGETHER
    card_body = dbc.CardBody(
        [
            dbc.Container(
                [
                    # Display content area (shown in display mode)
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.P(
                                                content_text
                                                or f"No {card_type} available",
                                                id={
                                                    "type": "unified-card-display-content",
                                                    "item_id": item_id,
                                                    "card_type": card_type,
                                                    "data_id": data_id,
                                                },
                                                className="ai-card-content-text text-center mt-2",
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                            # Notes display (if any)
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Small(
                                                f"Notes: {notes_text}"
                                                if notes_text
                                                else "No notes",
                                                className="ai-card-metadata",
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            )
                            if notes_text
                            else html.Div(),
                        ],
                        id={
                            "type": "unified-display-content",
                            "item_id": item_id,
                            "card_type": card_type,
                            "data_id": data_id,
                        },
                        style={"display": "block" if mode == "display" else "none"},
                    ),
                    # Edit content area (shown in edit mode)
                    html.Div(
                        [
                            # Content input section
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                card_config["content_label"],
                                                className="fw-semibold text-dark mb-2",
                                            ),
                                            dbc.Textarea(
                                                id={
                                                    "type": "user-content-input",
                                                    "item_id": item_id,
                                                    "card_type": card_type,
                                                    "data_id": data_id,
                                                },
                                                value=content_text,
                                                size="sm",
                                                className="mb-3",
                                                rows=3,
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                            # Notes section
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                card_config["notes_label"],
                                                className="fw-semibold text-dark mb-2",
                                            ),
                                            dbc.Textarea(
                                                id={
                                                    "type": "user-content-notes",
                                                    "item_id": item_id,
                                                    "card_type": card_type,
                                                    "data_id": data_id,
                                                },
                                                value=notes_text,
                                                size="sm",
                                                className="mb-3",
                                                rows=2,
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                        ],
                        id={
                            "type": "unified-edit-content",
                            "item_id": item_id,
                            "card_type": card_type,
                            "data_id": data_id,
                        },
                        style={"display": "block" if mode == "edit" else "none"},
                    ),
                    # Button area - ALL BUTTONS EXIST TOGETHER (like feedback)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Hr(className="my-3"),
                                    # ALL BUTTONS EXIST SIMULTANEOUSLY
                                    dbc.ButtonGroup(
                                        [
                                            # Edit button (visible in display mode)
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-edit me-2"
                                                    ),
                                                    card_config["edit_text"],
                                                ],
                                                id={
                                                    "type": "edit-user-content-btn",
                                                    "item_id": item_id,
                                                    "card_type": card_type,
                                                    "data_id": data_id,
                                                },
                                                color="primary",
                                                outline=True,
                                                size="sm",
                                                style={
                                                    "display": "inline-block"
                                                    if mode == "display"
                                                    else "none"
                                                },
                                            ),
                                            # Save button (visible in edit mode)
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-save me-2"
                                                    ),
                                                    card_config["save_text"],
                                                ],
                                                id={
                                                    "type": "save-user-content-btn",
                                                    "item_id": item_id,
                                                    "card_type": card_type,
                                                    "data_id": data_id,
                                                },
                                                color="success",
                                                size="sm",
                                                className="me-2",
                                                style={
                                                    "display": "inline-block"
                                                    if mode == "edit"
                                                    else "none"
                                                },
                                            ),
                                            # Cancel button (visible in edit mode)
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-times me-2"
                                                    ),
                                                    "Cancel",
                                                ],
                                                id={
                                                    "type": "cancel-user-content-btn",
                                                    "item_id": item_id,
                                                    "card_type": card_type,
                                                    "data_id": data_id,
                                                },
                                                color="secondary",
                                                outline=True,
                                                size="sm",
                                                style={
                                                    "display": "inline-block"
                                                    if mode == "edit"
                                                    else "none"
                                                },
                                            ),
                                        ],
                                        className="w-100",
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                ],
                fluid=True,
                className="p-0",
            ),
        ],
        className="p-4",
    )

    return dbc.Card(
        [card_header, card_body],
        className="mb-3 shadow-sm",
        id={
            "type": "unified-user-card",
            "item_id": item_id,
            "card_type": card_type,
            "data_id": data_id,
            "mode": mode,
        },
    )


def _create_edit_mode_body(
    data_id, item_id, card_type, card_config, content_text, notes_text
):
    """Create the card body for edit mode with input fields and save button"""

    return dbc.CardBody(
        [
            dbc.Container(
                [
                    # Content input section
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        card_config["content_label"],
                                        className="fw-semibold text-dark mb-2",
                                    ),
                                    dbc.Textarea(
                                        id={
                                            "type": "user-content-input",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        value=content_text,
                                        size="sm",
                                        className="mb-3",
                                        rows=3,
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    # Notes section
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        card_config["notes_label"],
                                        className="fw-semibold text-dark mb-2",
                                    ),
                                    dbc.Textarea(
                                        id={
                                            "type": "user-content-notes",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        value=notes_text,
                                        size="sm",
                                        className="mb-3",
                                        rows=2,
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    # Action buttons row
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Hr(className="my-3"),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-save me-2"),
                                            card_config["save_text"],
                                        ],
                                        id={
                                            "type": "save-user-content-btn",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        color="success",
                                        size="sm",
                                        className="me-2",
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-times me-2"),
                                            "Cancel",
                                        ],
                                        id={
                                            "type": "cancel-user-content-btn",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        color="secondary",
                                        outline=True,
                                        size="sm",
                                        className="me-3",
                                    ),
                                    # Hidden edit button (needed for MATCH pattern)
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-edit me-2"),
                                            card_config["edit_text"],
                                        ],
                                        id={
                                            "type": "edit-user-content-btn",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        color="primary",
                                        outline=True,
                                        size="sm",
                                        style={
                                            "display": "none"
                                        },  # Hidden in edit mode
                                    ),
                                    html.Span(
                                        id={
                                            "type": "user-content-save-status",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        className="text-muted small",
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                ],
                fluid=True,
                className="p-0",
            ),
        ],
        className="p-4",
    )


def _create_display_mode_body(
    data_id, item_id, card_type, card_config, content_text, notes_text
):
    """Create the card body for display mode with read-only content and edit button"""

    return dbc.CardBody(
        [
            dbc.Container(
                [
                    # Content display
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P(
                                        content_text or f"No {card_type} available",
                                        id={
                                            "type": "unified-card-display-content",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        className="ai-card-content-text text-center mt-2",
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    # Notes display (if any)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Small(
                                        f"Notes: {notes_text}"
                                        if notes_text
                                        else "No notes",
                                        className="ai-card-metadata",
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    )
                    if notes_text
                    else html.Div(),
                    # Edit button row
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Hr(className="my-3"),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-edit me-2"),
                                            card_config["edit_text"],
                                        ],
                                        id={
                                            "type": "edit-user-content-btn",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        color="primary",
                                        outline=True,
                                        size="sm",
                                    ),
                                    # Hidden save and cancel buttons (needed for MATCH pattern)
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-save me-2"),
                                            card_config["save_text"],
                                        ],
                                        id={
                                            "type": "save-user-content-btn",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        color="success",
                                        size="sm",
                                        style={
                                            "display": "none"
                                        },  # Hidden in display mode
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-times me-2"),
                                            "Cancel",
                                        ],
                                        id={
                                            "type": "cancel-user-content-btn",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        color="secondary",
                                        outline=True,
                                        size="sm",
                                        style={
                                            "display": "none"
                                        },  # Hidden in display mode
                                    ),
                                    # Hidden text input (needed for MATCH pattern)
                                    dbc.Textarea(
                                        id={
                                            "type": "user-content-input",
                                            "item_id": item_id,
                                            "card_type": card_type,
                                            "data_id": data_id,
                                        },
                                        value=content_text,
                                        size="sm",
                                        style={
                                            "display": "none"
                                        },  # Hidden in display mode
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                ],
                fluid=True,
                className="p-0",
            ),
        ],
        className="p-4",
    )
