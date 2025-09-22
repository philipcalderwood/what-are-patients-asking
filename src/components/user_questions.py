import dash_bootstrap_components as dbc


def create_user_question_component(
    data_id, question_id, question_text="", notes_text="", question_number=1
):
    """Create a component for a single user-inferred question with notes using dbc Card"""
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
                                        f"Inferred Question {question_number}",
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
                                            "type": "delete-user-question-btn",
                                            "item_id": data_id,
                                            "question_id": question_id,
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
                    # Question input section
                    dbc.Container(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Question",
                                                className="fw-semibold text-dark mb-2",
                                            ),
                                            dbc.Textarea(
                                                id={
                                                    "type": "user-question-input",
                                                    "item_id": data_id,
                                                    "question_id": question_id,
                                                },
                                                value=question_text,
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
                                                "Category",
                                                className="fw-semibold text-dark mb-2",
                                            ),
                                            dbc.Textarea(
                                                id={
                                                    "type": "user-question-notes",
                                                    "item_id": data_id,
                                                    "question_id": question_id,
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
                                                    "Save Question",
                                                ],
                                                id={
                                                    "type": "save-user-question-btn",
                                                    "item_id": data_id,
                                                    "question_id": question_id,
                                                },
                                                color="success",
                                                size="sm",
                                                className="me-3",
                                            ),
                                            html.Span(
                                                id={
                                                    "type": "user-question-save-status",
                                                    "item_id": data_id,
                                                    "question_id": question_id,
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
            "type": "user-question-container",
            "data_id": data_id,
            "question_id": question_id,
        },
    )


def load_existing_user_questions(data_id: str):
    """Load existing user questions from database for a given item"""
    try:
        from utilities.mrpc_database import MRPCDatabase

        db = MRPCDatabase()
        existing_questions = db.get_user_questions(data_id)

        question_components = []
        for index, question_data in enumerate(existing_questions, 1):
            question_component = create_user_question_component(
                data_id,
                question_data["question_id"],
                question_data["question_text"] or "",
                question_data["notes_text"] or "",
                question_number=index,
            )
            question_components.append(question_component)

        return question_components

    except Exception as e:
        print(f"❌ Error loading existing user questions: {e}")
        return []


def create_user_questions_content(point, customdata):
    """Create user questions content with dbc components"""
    from dash import html

    data_id = customdata[0] if len(customdata) > 0 else "unknown"

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # Container for existing user questions
                            html.Div(
                                id={
                                    "type": "user-questions-container",
                                    "item_id": data_id,
                                },
                                children=load_existing_user_questions(data_id),
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
                            # Add new question button with Bootstrap styling only
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
                        width=12,
                    ),
                ]
            ),
        ],
        fluid=True,
        className="p-0",
    )
