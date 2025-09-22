def create_metadata_sidebar():
    """Create the metadata sidebar component with unified card flow without visible sections"""
    from dash import html

    return html.Div(
        [
            # Single unified section for all cards to flow together
            html.Div(
                [
                    # AI Questions content (individual cards will be inserted here)
                    html.Div(id="ai-question-content", children=[]),
                    # AI Categories content (individual cards will be inserted here)
                    html.Div(id="ai-categories-content", children=[]),
                    # User Questions content (individual cards will be inserted here)
                    html.Div(id="user-questions-content", children=[]),
                    # User Topics content (individual cards will be inserted here)
                    html.Div(id="user-topics-content", children=[]),
                ],
                className="unified-card-flow",
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "gap": "0",  # Space between individual cards
                },
            ),
        ],
        id="metadata-sidebar",
        className="h-100 overflow-scroll",
        style={
            "padding": "1rem",
            "scrollbar-width": "none",
        },  # Add some padding around the unified flow
    )
