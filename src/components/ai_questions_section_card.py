import dash_bootstrap_components as dbc


def load_existing_ai_questions(data_id: str):
    """Load existing AI questions from database for a given item and return cards
    Passed customdata[0] uuid id in posts then gathers all questions associated against post URL then generates cards"""
    try:
        from utilities.mrpc_database import MRPCDatabase

        db = MRPCDatabase()
        existing_ai_questions = db.get_ai_questions(data_id)

        ai_question_components = []
        print(
            f"ℹ️ Loaded {len(existing_ai_questions)} existing AI questions for data_id {data_id}"
        )
        for index, ai_question_data in enumerate(existing_ai_questions, 1):
            ai_question_component = create_ai_question_component(
                data_id,
                ai_question_data,
                question_number=index,
            )
            ai_question_components.append(ai_question_component)
        print(ai_question_component)
        return ai_question_components

    except Exception as e:
        print(f"❌ Error loading existing AI questions: {e}")
        return []


def create_ai_question_component(data_id, ai_question_data, question_number=1):
    """Create a component for a single AI-generated question"""
    from dash import html

    question_text = ai_question_data.get("question_text", "")
    confidence_score = ai_question_data.get("confidence_score", 0)
    model_version = ai_question_data.get("model_version", "")
    created_at = ai_question_data.get("created_at", "")

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6(
                                        f"AI Question {question_number}",
                                        className="mb-0 text-white fw-bold",
                                    )
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Badge(
                                        f"Confidence: {confidence_score:.2f}"
                                        if confidence_score
                                        else "N/A",
                                        color="light",
                                        className="me-2",
                                    ),
                                ],
                                width=4,
                                className="text-end",
                            ),
                        ],
                        className="align-items-center",
                    ),
                ],
                className="py-3 px-4 bg-info text-white",
            ),
            dbc.CardBody(
                [
                    dbc.Container(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.P(
                                                question_text
                                                or "No question available",
                                                className="ai-card-content-text mb-3",
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
                                            html.Small(
                                                f"Model: {model_version}"
                                                if model_version
                                                else "",
                                                className="ai-card-metadata",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                f"Created: {created_at}"
                                                if created_at
                                                else "",
                                                className="ai-card-metadata text-end",
                                            ),
                                        ],
                                        width=6,
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
        id="ai-question-card",
        className=" mb-3 shadow-sm",
    )
