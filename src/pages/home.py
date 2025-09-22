from dash import html, register_page, dcc
import dash_bootstrap_components as dbc

# Register this page with Dash Pages
register_page(__name__, path="/", name="Home")


def layout():
    return html.Div(
        [
            dbc.Container(
                [
                    dbc.Row(
                        dbc.Col(
                            [
                                # Markdown section (you can fill this in later)
                                dcc.Markdown(
                                    """
                                    # Welcome 👋
                                    #### Thank you for testing the CDE data explorer!

                                    - All feedback is welcome
                                    - I think it is functional if not fully featured.
                                    """,
                                    id="home-welcome-content",
                                    className="text-left pt-4 pb-2",
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            html.H5(
                                                "Available Pages",
                                                id="home-pages-title",
                                                className="mb-0 text-dark",  # Changed to black
                                            )
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.ListGroup(
                                                    [
                                                        dbc.ListGroupItem(
                                                            dcc.Link(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-table me-2"
                                                                    ),
                                                                    "Forum Explorer",
                                                                ],
                                                                href="/forum-explorer",
                                                                id="home-link-forum-explorer",
                                                                className="text-decoration-none text-primary text-decoration-underline",  # Blue and underlined
                                                            ),
                                                            action=True,
                                                            className="d-flex align-items-center",
                                                        ),
                                                        dbc.ListGroupItem(
                                                            dcc.Link(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-tags me-2"
                                                                    ),
                                                                    "Tag Summary",
                                                                ],
                                                                href="/tag-summary",
                                                                id="home-link-tag-summary",
                                                                className="text-decoration-none text-primary text-decoration-underline",  # Blue and underlined
                                                            ),
                                                            action=True,
                                                            className="d-flex align-items-center",
                                                        ),
                                                        dbc.ListGroupItem(
                                                            dcc.Link(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-upload me-2"
                                                                    ),
                                                                    "Upload",
                                                                ],
                                                                href="/upload",
                                                                id="home-link-upload",
                                                                className="text-decoration-none text-primary text-decoration-underline",  # Blue and underlined
                                                            ),
                                                            action=True,
                                                            className="d-flex align-items-center",
                                                        ),
                                                    ],
                                                    id="home-navigation-list",
                                                    flush=True,
                                                )
                                            ]
                                        ),
                                    ],
                                    id="home-navigation-card",
                                    className="shadow-sm",
                                ),
                            ],
                            width=8,
                            className="mx-auto",
                        )
                    )
                ],
                fluid=True,
                className="py-2 py-md-3 py-lg-4 px-2 px-md-3",
            ),
        ]
    )
