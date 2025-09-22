from utilities.backend import load_existing_feedback


def create_review_content_card(
    data_id,
    content_type,
    display_label,
    value,
    card_type="ai_feedback",
    show_header=False,
    additional_content=None,
    card_class="ai-content-card h-100",
    body_class="ai-content-card-body d-flex flex-column h-100",
):
    """
    Create a unified, reusable card component for content review with various interaction types.

    This replaces the old create_ai_content_review_card function and provides a more flexible,
    reusable component that can handle different types of content cards.

    Args:
        data_id: Unique identifier for the data item
        content_type: Type of content (e.g., "LLM_inferred_question", "tag_hierarchy_path")
        display_label: Label to display (e.g., "AI Inferred Question", "AI Inferred Category")
        value: The actual content value
        card_type: Type of card - "ai_feedback", "basic", "metadata" (default: "ai_feedback")
        show_header: Whether to show a card header with the display_label (default: False)
        additional_content: Optional list of additional content elements to include
        card_class: CSS classes for the card container
        body_class: CSS classes for the card body
    """

    # Handle different card types
    if card_type == "basic":
        return _create_basic_card(
            display_label,
            value,
            show_header,
            additional_content,
            card_class,
            body_class,
        )
    elif card_type == "metadata":
        return _create_metadata_card(
            display_label,
            value,
            show_header,
            additional_content,
            card_class,
            body_class,
        )
    elif card_type == "ai_feedback":
        return _create_ai_feedback_card(
            data_id,
            content_type,
            display_label,
            value,
            show_header,
            additional_content,
            card_class,
            body_class,
        )
    else:
        raise ValueError(f"Unknown card_type: {card_type}")


def create_feedback_components(
    data_id, content_type, existing_feedback=None, response_id=None
):
    """
    Create reusable feedback components (buttons, display, input) for AI content feedback.

    Args:
        data_id: Unique identifier for the data item
        content_type: Type of content being reviewed (e.g., "LLM_inferred_question")
        existing_feedback: Optional existing feedback data dict
        response_id: Optional response ID, will generate new one if not provided

    Returns:
        dict: Dictionary containing structured DBC components:
            - feedback_buttons_row: Complete Row with feedback buttons
            - feedback_display_area: DBC Container with feedback display or placeholder
            - feedback_input_area: Complete Row with collapsible input
            - response_id: The response ID used
    """
    from dash import html
    import dash_bootstrap_components as dbc
    import uuid

    # Load existing feedback if not provided
    if existing_feedback is None:
        existing_feedback = load_existing_feedback(data_id, content_type)

    # Generate unique response ID - use existing one if available
    if existing_feedback and existing_feedback.get("response_id"):
        response_id = existing_feedback["response_id"]
    elif response_id is None:
        response_id = str(uuid.uuid4())

    # Create thumbs up/down buttons with clean dbc components
    feedback_buttons = dbc.ButtonGroup(
        [
            dbc.Button(
                [
                    html.I(className="fas fa-thumbs-up"),
                    html.Span("Good", className="feedback-button-text ms-1"),
                ],
                id={
                    "type": "ai-content-thumbs-up",
                    "data_id": data_id,
                    "content_type": content_type,
                    "response_id": response_id,
                },
                size="sm",
                color="success"
                if existing_feedback and existing_feedback.get("rating") == "positive"
                else "outline-success",
                className="feedback-button feedback-button-positive",
            ),
            dbc.Button(
                [
                    html.I(className="fas fa-thumbs-down"),
                    html.Span("Poor", className="feedback-button-text ms-1"),
                ],
                id={
                    "type": "ai-content-thumbs-down",
                    "data_id": data_id,
                    "content_type": content_type,
                    "response_id": response_id,
                },
                size="sm",
                color="danger"
                if existing_feedback and existing_feedback.get("rating") == "negative"
                else "outline-danger",
                className="feedback-button feedback-button-negative",
            ),
        ],
        size="sm",
        className="ai-content-feedback-buttons",
    )

    # Create edit button
    show_edit_button = existing_feedback and existing_feedback.get("feedback_text")
    edit_button = dbc.Button(
        [html.I(className="fas fa-edit me-1"), "Edit"],
        id={
            "type": "edit-ai-feedback",
            "data_id": data_id,
            "content_type": content_type,
            "response_id": response_id,
        },
        size="sm",
        color="secondary",
        outline=True,
        className="ai-content-edit-button",
        style={"display": "block" if show_edit_button else "none"},
    )

    # Create structured feedback buttons row
    feedback_buttons_row = dbc.Row(
        [
            dbc.Col(
                feedback_buttons, width="auto", className="d-flex align-items-center"
            ),
            dbc.Col(
                edit_button, width="auto", className="ms-auto d-flex align-items-center"
            ),
        ],
        className="mb-3 feedback-buttons-row",
        justify="between",
        align="center",
    )

    # Create feedback display area with explicit DBC structure
    if existing_feedback and existing_feedback.get("feedback_text"):
        feedback_text = existing_feedback["feedback_text"]
        user_display_name = existing_feedback.get("user_display_name", "Unknown User")
        formatted_time = existing_feedback.get("formatted_time", "")
        rating = existing_feedback.get("rating", "")

        # Create feedback display with full DBC structure
        feedback_display_area = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                # User feedback header with DBC components
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.H6(
                                                f"{user_display_name} Feedback",
                                                className="mb-1 fw-semibold text-secondary",
                                                style={"font-size": "0.85rem"},
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            html.Small(
                                                formatted_time,
                                                className="text-muted fst-italic",
                                                style={"font-size": "0.75rem"},
                                            ),
                                            width="auto",
                                            className="ms-auto",
                                        ),
                                    ],
                                    className="mb-2",
                                    align="center",
                                ),
                                # Simple feedback text with DBC Card using Bootstrap colors
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.P(
                                                    feedback_text,
                                                    className="mb-0 fst-italic text-body",
                                                    style={"line-height": "1.5"},
                                                )
                                            ],
                                            className="py-2 px-3",
                                        )
                                    ],
                                    color="success"
                                    if rating == "positive"
                                    else "danger"
                                    if rating == "negative"
                                    else "secondary",
                                    outline=True,
                                    className="mb-0 border-start border-3",
                                ),
                            ],
                            width=12,
                        )
                    ],
                    className="mb-0",
                )
            ],
            fluid=True,
            className="user-feedback-display-area p-0",
        )
    else:
        # Create placeholder with "Your Feedback" default section
        feedback_display_area = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            html.H6(
                                                "Your Feedback",
                                                className="mb-0 text-center text-muted",
                                                style={"font-size": "0.9rem"},
                                            ),
                                            className="py-2 bg-light",
                                        ),
                                        dbc.CardBody(
                                            html.P(
                                                "You have not provided any feedback yet.",
                                                className="text-muted fst-italic text-center mb-0",
                                                style={
                                                    "font-size": "0.8rem",
                                                    "min-height": "2rem",
                                                    "display": "flex",
                                                    "align-items": "center",
                                                    "justify-content": "center",
                                                },
                                            ),
                                            className="py-3",
                                        ),
                                    ],
                                    color="light",
                                    outline=True,
                                    className="feedback-placeholder-card",
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mb-0",
                )
            ],
            fluid=True,
            className="feedback-placeholder-area p-0",
        )

    # Create structured feedback input area
    feedback_input_area = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Collapse(
                        [
                            dbc.Container(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        "Please provide justification for your feedback:",
                                                        className="fw-semibold mb-2 text-dark",
                                                        style={"font-size": "0.85rem"},
                                                    ),
                                                    dbc.Textarea(
                                                        id={
                                                            "type": "ai-content-justification",
                                                            "data_id": data_id,
                                                            "content_type": content_type,
                                                            "response_id": response_id,
                                                        },
                                                        value=existing_feedback.get(
                                                            "feedback_text", ""
                                                        )
                                                        if existing_feedback
                                                        else "",
                                                        size="sm",
                                                        className="mb-3",
                                                        placeholder="Enter your feedback here...",
                                                        style={"min-height": "4rem"},
                                                    ),
                                                ],
                                                width=12,
                                            )
                                        ],
                                        className="mb-2",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.ButtonGroup(
                                                        [
                                                            dbc.Button(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-save me-1"
                                                                    ),
                                                                    "Save Feedback",
                                                                ],
                                                                id={
                                                                    "type": "save-ai-justification",
                                                                    "data_id": data_id,
                                                                    "content_type": content_type,
                                                                    "response_id": response_id,
                                                                },
                                                                size="sm",
                                                                color="primary",
                                                                outline=True,
                                                            ),
                                                            dbc.Button(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-times me-1"
                                                                    ),
                                                                    "Cancel",
                                                                ],
                                                                id={
                                                                    "type": "cancel-ai-justification",
                                                                    "data_id": data_id,
                                                                    "content_type": content_type,
                                                                    "response_id": response_id,
                                                                },
                                                                size="sm",
                                                                color="secondary",
                                                                outline=True,
                                                            ),
                                                        ],
                                                        size="sm",
                                                    ),
                                                ],
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Div(
                                                        id={
                                                            "type": "ai-feedback-status",
                                                            "data_id": data_id,
                                                            "content_type": content_type,
                                                            "response_id": response_id,
                                                        },
                                                        className="d-flex align-items-center ms-3",
                                                        style={"font-size": "0.8rem"},
                                                    )
                                                ],
                                                width="auto",
                                                className="d-flex align-items-center",
                                            ),
                                        ],
                                        align="center",
                                    ),
                                ],
                                fluid=True,
                                className="p-3 bg-light rounded",
                                style={"border": "1px solid #dee2e6"},
                            )
                        ],
                        id={
                            "type": "ai-justification-collapse",
                            "data_id": data_id,
                            "content_type": content_type,
                            "response_id": response_id,
                        },
                        is_open=False,
                        className="ai-content-collapse",
                    )
                ],
                width=12,
            )
        ],
        className="feedback-input-row",
    )

    return {
        "feedback_buttons_row": feedback_buttons_row,
        "feedback_display_area": feedback_display_area,
        "feedback_input_area": feedback_input_area,
        "response_id": response_id,
    }


def _create_ai_feedback_card(
    data_id,
    content_type,
    display_label,
    value,
    show_header,
    additional_content,
    card_class,
    body_class,
):
    """Create AI feedback card with thumbs up/down and justification features using structured DBC components"""
    from dash import html
    import dash_bootstrap_components as dbc

    # Use the reusable feedback component with structured DBC layout
    feedback_components = create_feedback_components(data_id, content_type)

    # Keep card neutral - apply colors only to specific feedback elements
    card_color = "light"  # Always use neutral card color

    # Prepare card content
    card_content = []

    # Add header if requested
    if show_header:
        card_content.append(
            dbc.CardHeader(
                html.H6(display_label, className="mb-0 text-center"),
                className="py-2",
            )
        )

    # Create structured card body using DBC Container for better control
    card_body_content = dbc.Container(
        [
            # Main content section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                str(value) if value else "N/A",
                                className="ai-content-main-text",
                                style={
                                    "font-size": "0.95rem",
                                    "line-height": "1.5",
                                    "color": "#495057",
                                },
                            ),
                        ],
                        width=12,
                    )
                ],
                className="mb-3 main-content-row",
            ),
            # Feedback display section - now using structured DBC area
            dbc.Row(
                [dbc.Col([feedback_components["feedback_display_area"]], width=12)],
                className="mb-3 feedback-display-row",
            ),
            # Feedback buttons section - using structured row
            feedback_components["feedback_buttons_row"],
            # Feedback input section - using structured area
            feedback_components["feedback_input_area"],
        ],
        fluid=True,
        className="ai-feedback-card-container p-0",
    )

    # Add any additional content to the container
    if additional_content:
        additional_row = dbc.Row(
            [
                dbc.Col(
                    additional_content
                    if isinstance(additional_content, list)
                    else [additional_content],
                    width=12,
                )
            ],
            className="mt-3 additional-content-row",
        )
        # Insert additional content into the container's children
        if hasattr(card_body_content, "children"):
            card_body_content.children.append(additional_row)

    card_content.append(
        dbc.CardBody(
            card_body_content,
            className=f"{body_class} p-3",  # Enhanced padding for better spacing
        )
    )

    return dbc.Card(
        card_content,
        color=card_color,
        outline=True,
        className=card_class,
    )


def _create_basic_card(
    display_label, value, show_header, additional_content, card_class, body_class
):
    """Create a basic card without feedback functionality"""
    from dash import html
    import dash_bootstrap_components as dbc

    card_content = []

    # Add header if requested
    if show_header:
        card_content.append(
            dbc.CardHeader(
                html.H6(display_label, className="mb-0 text-center"),
                className="py-2",
            )
        )

    # Create main card body content
    body_content = [
        html.Div(
            str(value) if value else "N/A",
            className="main-content-text",
        ),
    ]

    # Add any additional content
    if additional_content:
        if isinstance(additional_content, list):
            body_content.extend(additional_content)
        else:
            body_content.append(additional_content)

    card_content.append(
        dbc.CardBody(
            body_content,
            className=body_class,
            style={"padding": "0.75rem"},
        )
    )

    return dbc.Card(
        card_content,
        color="light",
        outline=True,
        className=card_class,
    )


def _create_metadata_card(
    display_label, value, show_header, additional_content, card_class, body_class
):
    """Create a metadata-style card"""
    from dash import html
    import dash_bootstrap_components as dbc

    card_content = []

    # Add header if requested
    if show_header:
        card_content.append(
            dbc.CardHeader(
                html.H6(display_label, className="mb-0 text-center"),
                className="py-2",
            )
        )

    # Create main card body content
    body_content = [
        html.Div(
            str(value) if value else "No data available",
            className="metadata-content",
        ),
    ]

    # Add any additional content
    if additional_content:
        if isinstance(additional_content, list):
            body_content.extend(additional_content)
        else:
            body_content.append(additional_content)

    card_content.append(
        dbc.CardBody(
            body_content,
            className=body_class,
            style={"padding": "0.75rem"},
        )
    )

    return dbc.Card(
        card_content,
        color="light",
        outline=True,
        className=card_class,
    )
