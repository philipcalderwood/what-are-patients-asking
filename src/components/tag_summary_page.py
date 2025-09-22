from dash import html, dcc
import dash_bootstrap_components as dbc

from components.navbars import create_forum_only_navbar


def create_tag_summary_page():
    """Create the tag summary page"""

    return html.Div(
        [
            create_forum_only_navbar(),  # Add navbar with forum switcher
            html.Div(
                [
                    html.H1("Tag Summary", id="tag-summary-heading", className="mb-4"),
                    # Timeline chart section
                    html.Div(
                        [
                            html.H3("Posts per Category Timeline", className="mb-3"),
                            html.P(
                                "Click on legend items to show/hide categories",
                                style={
                                    "color": "#6c757d",
                                    "font-size": "0.9rem",
                                    "margin-bottom": "1rem",
                                },
                            ),
                            dcc.Graph(
                                id="category-timeline-chart", style={"height": "500px"}
                            ),
                        ],
                        style={
                            "margin-bottom": "2rem",
                            "padding": "1.5rem",
                            "background-color": "#ffffff",
                            "border-radius": "0.375rem",
                            "border": "1px solid #dee2e6",
                        },
                    ),
                    # Category distribution pie chart section
                    html.Div(
                        [
                            html.H3("Category Distribution", className="mb-3"),
                            html.P(
                                "Interactive donut chart showing the distribution of posts across categories",
                                style={
                                    "color": "#6c757d",
                                    "font-size": "0.9rem",
                                    "margin-bottom": "1rem",
                                },
                            ),
                            dcc.Graph(
                                id="category-distribution-chart",
                                style={"height": "500px"},
                            ),
                        ],
                        style={
                            "margin-bottom": "2rem",
                            "padding": "1.5rem",
                            "background-color": "#ffffff",
                            "border-radius": "0.375rem",
                            "border": "1px solid #dee2e6",
                        },
                    ),
                    # Summary statistics section
                    html.Div(
                        id="tag-summary-content",
                        children=[
                            html.P(
                                "Select a forum from the dropdown above to see tag summaries for that forum."
                            )
                        ],
                        style={
                            "padding": "2rem",
                            "background-color": "#f8f9fa",
                            "border-radius": "0.375rem",
                            "margin-top": "1rem",
                        },
                    ),
                ],
                style={
                    "padding": "2rem",
                    "max-width": "1200px",
                    "margin": "0 auto",
                },
            ),
        ]
    )
