import dash_bootstrap_components as dbc
from dash import html


def generate_ai_category_card(data_id, ai_category_data, category_number=1):
    """Create a component for a single AI-generated category"""

    category_type = ai_category_data.get("category_type", "")
    category_value = ai_category_data.get("category_value", "")
    confidence_score = ai_category_data.get("confidence_score", 0)
    model_version = ai_category_data.get("model_version", "")
    created_at = ai_category_data.get("created_at", "")

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6(
                                        f"AI Category {category_number}",
                                        className="ai-card-header-title mb-0",
                                    ),
                                    html.Small(
                                        category_type.replace("_", " ").title()
                                        if category_type
                                        else "",
                                        className="ai-card-metadata",
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Badge(
                                        f"Confidence: {confidence_score:.2f}"
                                        if confidence_score
                                        else "N/A",
                                        color="warning",
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
                className="py-3 px-4 bg-light",
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
                                                category_value
                                                or "No category available",
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
        className="ai-category-card mb-3 shadow-sm",
    )


def load_existing_ai_categories(data_id: str):
    """Load existing AI categories from database for a given item"""
    try:
        from utilities.mrpc_database import MRPCDatabase

        db = MRPCDatabase()
        existing_ai_categories = db.get_ai_categories(data_id)

        ai_category_components = []
        for index, ai_category_data in enumerate(existing_ai_categories, 1):
            ai_category_component = generate_ai_category_card(
                data_id,
                ai_category_data,
                category_number=index,
            )
            ai_category_components.append(ai_category_component)

        return ai_category_components

    except Exception as e:
        print(f"❌ Error loading existing AI categories: {e}")
        return []
