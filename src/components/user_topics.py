import dash_bootstrap_components as dbc
from dash import html


def create_user_topics_content(point, customdata):
    """Create user topics content with dbc components"""

    data_id = customdata[0] if len(customdata) > 0 else "unknown"

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # Container for existing user topics
                            html.Div(
                                id={
                                    "type": "user-topics-container",
                                    "item_id": data_id,
                                },
                                children=load_existing_user_topics(data_id),
                                className="mb-3",
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # Add new topic button with Bootstrap styling only
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
                        width=12,
                    ),
                ]
            ),
        ],
        fluid=True,
        className="p-0",
    )


def create_user_topic_component(
    data_id, topic_id, topic_text="", notes_text="", topic_number=1
):
    """Create a component for a single user-defined topic with notes using dbc Card"""
    from dash import html

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6(
                                        f"User Topic {topic_number}",
                                        className="mb-0 text-dark fw-semibold",
                                    )
                                ],
                                width=10,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-trash"),
                                        id={
                                            "type": "delete-user-topic-btn",
                                            "item_id": data_id,
                                            "topic_id": topic_id,
                                        },
                                        color="danger",
                                        outline=True,
                                        size="sm",
                                        className="btn-sm shadow-sm",
                                    )
                                ],
                                width=2,
                                className="text-end",
                            ),
                        ],
                        className="align-items-center",
                    ),
                ],
                className="py-3 px-4 bg-light",
            ),
            dbc.CardBody(
                [
                    # Topic input section
                    dbc.Container(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Topic",
                                                className="fw-semibold text-dark mb-2",
                                            ),
                                            dbc.Textarea(
                                                id={
                                                    "type": "user-topic-input",
                                                    "item_id": data_id,
                                                    "topic_id": topic_id,
                                                },
                                                value=topic_text,
                                                size="sm",
                                                className="mb-3",
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
                                                "Notes",
                                                className="fw-semibold text-dark mb-2",
                                            ),
                                            dbc.Textarea(
                                                id={
                                                    "type": "user-topic-notes",
                                                    "item_id": data_id,
                                                    "topic_id": topic_id,
                                                },
                                                value=notes_text,
                                                size="sm",
                                                className="mb-3",
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                            # Action buttons
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-save me-2"
                                                    ),
                                                    "Save Topic",
                                                ],
                                                id={
                                                    "type": "save-user-topic-btn",
                                                    "item_id": data_id,
                                                    "topic_id": topic_id,
                                                },
                                                color="success",
                                                size="sm",
                                                className="me-3",
                                            ),
                                            html.Span(
                                                id={
                                                    "type": "user-topic-save-status",
                                                    "item_id": data_id,
                                                    "topic_id": topic_id,
                                                },
                                                className="text-muted small",
                                            ),
                                        ],
                                        width=12,
                                        className="d-flex align-items-center",
                                    ),
                                ]
                            ),
                        ],
                        fluid=True,
                        className="p-0",
                    ),
                ],
                className="p-4",
            ),
        ],
        className="mb-4 shadow-sm",
        id={
            "type": "user-topic-container",
            "data_id": data_id,
            "topic_id": topic_id,
        },
    )


def load_existing_user_topics(data_id: str):
    """Load existing user topics from database for a given item"""
    try:
        # For now, return empty list since user topics may not be implemented in database yet
        # This can be updated when the database support is added
        existing_topics = []  # db.get_user_topics(data_id) when implemented

        topic_components = []
        for index, topic_data in enumerate(existing_topics, 1):
            topic_component = create_user_topic_component(
                data_id,
                topic_data.get("topic_id", f"topic_{index}"),
                topic_data.get("topic_text", ""),
                topic_data.get("notes_text", ""),
                index,
            )
            topic_components.append(topic_component)

        return topic_components

    except Exception as e:
        print(f"❌ Error loading existing user topics: {e}")
        return []
