from utilities.backend import load_existing_feedback
import uuid


def create_inference_feedback_component(data_id, inference_type, display_label, value):
    """Create integrated feedback component for individual inferences with persistence"""
    from dash import html
    import dash_bootstrap_components as dbc

    # Check for existing feedback
    existing_feedback = load_existing_feedback(data_id, inference_type)

    # Generate unique response ID - use existing one if available
    if existing_feedback and existing_feedback.get("response_id"):
        response_id = existing_feedback["response_id"]
    else:
        response_id = str(uuid.uuid4())

    # Determine initial state based on existing feedback
    if existing_feedback:
        # Existing feedback found - start in locked state
        rating = existing_feedback.get("rating", "")
        feedback_text = existing_feedback.get("feedback_text", "")

        # Handle potential NaN values from pandas - convert to string
        if not isinstance(feedback_text, str):
            feedback_text = (
                str(feedback_text)
                if feedback_text and str(feedback_text) != "nan"
                else ""
            )

        formatted_time = existing_feedback.get("formatted_time", "")

        if rating == "positive":
            container_style = {
                "padding": "0.75rem",
                "border": "2px solid #28a745",
                "border-radius": "0.375rem",
                "background-color": "#d4edda",
                "margin-bottom": "0.75rem",
                "transition": "all 0.3s ease",
            }
            status_color = "#155724"
            status_icon = "fa-thumbs-up"
            status_text = f"Positive feedback submitted on {formatted_time}"
        elif rating == "negative":
            container_style = {
                "padding": "0.75rem",
                "border": "2px solid #dc3545",
                "border-radius": "0.375rem",
                "background-color": "#f8d7da",
                "margin-bottom": "0.75rem",
                "transition": "all 0.3s ease",
            }
            status_color = "#721c24"
            status_icon = "fa-thumbs-down"
            status_text = f"Negative feedback submitted on {formatted_time}"
        else:
            # Text-only feedback
            container_style = {
                "padding": "0.75rem",
                "border": "2px solid #17a2b8",
                "border-radius": "0.375rem",
                "background-color": "#d1ecf1",
                "margin-bottom": "0.75rem",
                "transition": "all 0.3s ease",
            }
            status_color = "#0c5460"
            status_icon = "fa-comment"
            status_text = f"Text feedback submitted on {formatted_time}"

        # Create locked state status message
        status_message = html.Div(
            [
                html.I(
                    className=f"fas {status_icon}",
                    style={"color": status_color, "margin-right": "0.25rem"},
                ),
                status_text,
            ],
            style={
                "color": status_color,
                "font-size": "0.75rem",
                "margin-bottom": "0.5rem",
            },
        )

        # Show existing feedback text if available
        if feedback_text.strip():
            status_message = html.Div(
                [
                    status_message,
                    html.Div(
                        f'"{feedback_text}"',
                        style={
                            "font-style": "italic",
                            "color": status_color,
                            "font-size": "0.7rem",
                            "margin-top": "0.25rem",
                            "padding": "0.25rem",
                            "background-color": "rgba(255,255,255,0.3)",
                            "border-radius": "0.25rem",
                        },
                    ),
                ]
            )

        # Create update button for locked state
        buttons_container = dbc.Button(
            [
                html.I(className="fas fa-edit", style={"margin-right": "0.25rem"}),
                "Update",
            ],
            id={
                "type": "feedback-update-btn",
                "data_id": data_id,
                "inference_type": inference_type,
                "response_id": response_id,
            },
            size="sm",
            color="secondary",
            outline=True,
            style={"font-size": "0.7rem", "padding": "0.2rem 0.5rem"},
        )

        # Text area starts hidden for locked state
        textarea_is_open = False

    else:
        # No existing feedback - start in unlocked state
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

        # Create initial feedback buttons
        buttons_container = html.Div(
            [
                dbc.Button(
                    html.I(className="fas fa-thumbs-up"),
                    id={
                        "type": "feedback-btn",
                        "data_id": data_id,
                        "inference_type": inference_type,
                        "rating": "positive",
                        "response_id": response_id,
                    },
                    size="sm",
                    color="success",
                    outline=True,
                    style={
                        "padding": "0.3rem 0.6rem",
                        "margin-right": "0.25rem",
                        "font-size": "0.8rem",
                    },
                ),
                dbc.Button(
                    html.I(className="fas fa-thumbs-down"),
                    id={
                        "type": "feedback-btn",
                        "data_id": data_id,
                        "inference_type": inference_type,
                        "rating": "negative",
                        "response_id": response_id,
                    },
                    size="sm",
                    color="danger",
                    outline=True,
                    style={"padding": "0.3rem 0.6rem", "font-size": "0.8rem"},
                ),
            ],
            style={"display": "flex", "gap": "0.25rem"},
        )

        # Text area starts hidden for new feedback
        textarea_is_open = False

    return html.Div(
        [
            # Inference content and feedback in integrated card
            html.Div(
                [
                    # Main inference display
                    html.Div(
                        [
                            html.Strong(
                                f"{display_label}:",
                                style={
                                    "font-size": "0.85rem",
                                    "color": "#495057",
                                    "margin-bottom": "0.25rem",
                                    "display": "block",
                                },
                            ),
                            html.Div(
                                str(value) if value else "N/A",
                                style={
                                    "font-size": "0.8rem",
                                    "color": "#6c757d",
                                    "margin-bottom": "0.5rem",
                                    "line-height": "1.4",
                                },
                            ),
                        ]
                    ),
                    # Feedback controls
                    html.Div(
                        [
                            # Status message
                            html.Div(
                                status_message,
                                id={
                                    "type": "feedback-status",
                                    "data_id": data_id,
                                    "inference_type": inference_type,
                                    "response_id": response_id,
                                },
                            ),
                            # Feedback buttons or update button
                            html.Div(
                                buttons_container,
                                id={
                                    "type": "feedback-buttons-container",
                                    "data_id": data_id,
                                    "inference_type": inference_type,
                                    "response_id": response_id,
                                },
                            ),
                            # Optional feedback text area
                            dbc.Collapse(
                                [
                                    dbc.Textarea(
                                        id={
                                            "type": "feedback-text",
                                            "data_id": data_id,
                                            "inference_type": inference_type,
                                            "response_id": response_id,
                                        },
                                        placeholder="Optional: Add your feedback comments here...",
                                        size="sm",
                                        value=existing_feedback.get("feedback_text", "")
                                        if existing_feedback
                                        else "",
                                        style={
                                            "font-size": "0.7rem",
                                            "min-height": "2.5rem",
                                            "resize": "vertical",
                                            "margin-bottom": "0.5rem",
                                        },
                                    ),
                                    dbc.Button(
                                        "Submit Text",
                                        id={
                                            "type": "feedback-text-submit",
                                            "data_id": data_id,
                                            "inference_type": inference_type,
                                            "response_id": response_id,
                                        },
                                        size="sm",
                                        color="primary",
                                        outline=True,
                                        style={
                                            "font-size": "0.65rem",
                                            "padding": "0.2rem 0.5rem",
                                        },
                                    ),
                                ],
                                id={
                                    "type": "feedback-collapse",
                                    "data_id": data_id,
                                    "inference_type": inference_type,
                                    "response_id": response_id,
                                },
                                is_open=textarea_is_open,
                            ),
                        ],
                        style={
                            "padding-top": "0.5rem",
                            "border-top": "1px solid #e9ecef",
                        },
                    ),
                ],
                # Dynamic container styling
                id={
                    "type": "feedback-container",
                    "data_id": data_id,
                    "inference_type": inference_type,
                    "response_id": response_id,
                },
                style=container_style,
            )
        ]
    )
