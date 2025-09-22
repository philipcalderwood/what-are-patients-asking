import dash_bootstrap_components as dbc
from dash import html, dcc


# NOTE: Used throughout the app
def create_simple_navbar():
    """Create a simple navigation bar for homepage (without view/dataset controls)"""

    # Get current user information
    try:
        from utilities.auth import get_current_user, is_admin

        current_user = get_current_user()

        if current_user:
            user_display = f"{current_user['first_name']} {current_user['last_name']}"
            user_role = "Admin" if is_admin() else "User"
            user_info_text = f"{user_display} ({user_role})"
        else:
            user_info_text = "Not authenticated"
    except Exception:
        user_info_text = "Authentication unavailable"

    return dbc.Navbar(
        [
            dbc.Container(
                [
                    # Toggle button and Brand section only
                    dbc.Row(
                        [
                            # Sidebar toggle button
                            dbc.Col(
                                dbc.Button(
                                    "☰",  # Hamburger menu icon
                                    id="navbar-sidebar-toggle",
                                    color="link",
                                    className="text-white fs-5 p-2 border-0",
                                    n_clicks=0,
                                ),
                                width="auto",
                                className="pe-3",
                            ),
                            # Brand
                            dbc.Col(
                                dbc.NavbarBrand(
                                    "Data Explorer",
                                    className="fs-6 fw-bold m-0",
                                ),
                                width="auto",
                                style={"padding": "0"},
                            ),
                            # User info and sign-out (right side)
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Span(
                                            user_info_text,
                                            style={
                                                "color": "#fff",
                                                "font-size": "0.9rem",
                                                "margin-right": "1rem",
                                            },
                                        ),
                                        dbc.Button(
                                            [
                                                html.I(
                                                    className="fas fa-sign-out-alt me-2",
                                                ),
                                                "Sign Out",
                                            ],
                                            id="sign-out-button",
                                            color="outline-light",
                                            size="sm",
                                            className="small",
                                        ),
                                    ],
                                    className="d-flex align-items-center",
                                ),
                                width="auto",
                                className="ms-auto",
                            ),
                        ],
                        align="center",
                        className="g-0 w-100",
                    ),
                ],
                fluid=True,
                className="d-flex align-items-center",
            )
        ],
        id="main-navbar",  # Same ID as full navbar for consistent styling
        color="secondary",
        dark=True,
        className="py-2 border-bottom",
    )


# NOTE: Used in the forum explorer view
def create_navbar():
    """Create a navigation bar with view and dataset selectors for Forum Explorer"""

    return dbc.Navbar(
        [
            dbc.Container(
                [
                    # Toggle button and Brand section
                    dbc.Row(
                        [
                            # Sidebar toggle button
                            dbc.Col(
                                dbc.Button(
                                    "☰",  # Hamburger menu icon
                                    id="navbar-sidebar-toggle",
                                    color="link",
                                    className="text-white fs-5 p-2 border-0",
                                    n_clicks=0,
                                ),
                                width="auto",
                                className="pe-3",
                            ),
                            # Brand
                            dbc.Col(
                                dbc.NavbarBrand(
                                    "Forum Explorer",
                                    className="fs-6 fw-bold m-0",
                                ),
                                width="auto",
                                className="p-0",
                            ),
                        ],
                        align="center",
                        className="g-0",
                        style={"margin-right": "2rem"},
                    ),
                    # User info and sign-out section
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                id="navbar-user-info",
                                                style={
                                                    "color": "#f8f9fa",
                                                    "font-size": "0.8rem",
                                                    "font-weight": "500",
                                                    "padding": "0.25rem 0.75rem",
                                                    "background-color": "rgba(255, 255, 255, 0.1)",
                                                    "border-radius": "0.25rem",
                                                    "border": "1px solid rgba(255, 255, 255, 0.2)",
                                                    "display": "flex",
                                                    "align-items": "center",
                                                    "margin-right": "0.5rem",
                                                },
                                            ),
                                            dbc.Button(
                                                html.I(className="fas fa-sign-out-alt"),
                                                id="sign-out-button-main",
                                                color="outline-light",
                                                size="sm",
                                                title="Sign Out",
                                                style={
                                                    "font-size": "0.8rem",
                                                    "padding": "0.25rem 0.5rem",
                                                },
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "align-items": "center",
                                        },
                                    )
                                ],
                                width="auto",
                                style={"margin-left": "1rem"},
                            ),
                        ],
                        align="center",
                        className="g-0",
                    ),
                ],
                fluid=True,
                style={
                    "display": "flex",
                    "align-items": "center",
                    "justify-content": "space-between",
                },
            )
        ],
        id="main-navbar",  # Add ID for potential styling updates
        color="secondary",
        dark=True,  # Make text white on the colored background
        className="py-2 border-bottom",
    )


# NOTE: Used in tag summary page
def create_forum_only_navbar():
    """Create a navigation bar with only the forum switcher"""

    # Get current user information
    try:
        from utilities.auth import get_current_user, is_admin

        current_user = get_current_user()
        if current_user:
            user_display = f"{current_user['first_name']} {current_user['last_name']}"
            user_role = "Admin" if is_admin() else "User"
            user_display = f"{user_display} ({user_role})"
        else:
            user_display = "Not logged in"
    except Exception:
        user_display = "Authentication error"

    return dbc.Navbar(
        [
            dbc.Container(
                [
                    # Toggle button and Brand section
                    dbc.Row(
                        [
                            # Sidebar toggle button
                            dbc.Col(
                                dbc.Button(
                                    "☰",  # Hamburger menu icon
                                    id="navbar-sidebar-toggle",
                                    color="link",
                                    style={
                                        "color": "#fff",
                                        "font-size": "1.2rem",
                                        "padding": "0.375rem 0.75rem",
                                        "border": "none",
                                        "background": "none",
                                    },
                                    n_clicks=0,
                                ),
                                width="auto",
                                style={"padding-right": "1rem"},
                            ),
                            # Brand
                            dbc.Col(
                                dbc.NavbarBrand(
                                    "Tag Summary",
                                    style={
                                        "font-size": "1.1rem",
                                        "font-weight": "bold",
                                        "margin": "0",
                                    },
                                ),
                                width="auto",
                                style={"padding": "0"},
                            ),
                        ],
                        align="center",
                        className="g-0",
                        style={"margin-right": "2rem"},
                    ),
                    # Forum selector and user info section
                    dbc.Row(
                        [
                            # Forum selector
                            dbc.Col(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Label(
                                                    "Forum:",
                                                    style={
                                                        "margin-right": "0.5rem",
                                                        "font-weight": "bold",
                                                        "color": "#fff",
                                                        "font-size": "0.8rem",
                                                        "margin-bottom": "0",
                                                        "line-height": "2.25rem",
                                                    },
                                                ),
                                                width="auto",
                                                style={"padding-right": "0"},
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="tag-summary-forum-selector",
                                                    options=[
                                                        {
                                                            "label": "All Forums",
                                                            "value": "all",
                                                        },
                                                        {
                                                            "label": "Cervical Cancer Forum",
                                                            "value": "cervical",
                                                        },
                                                        {
                                                            "label": "Ovarian Cancer Forum",
                                                            "value": "ovarian",
                                                        },
                                                        {
                                                            "label": "Vaginal Cancer Forum",
                                                            "value": "vaginal",
                                                        },
                                                        {
                                                            "label": "Vulval Cancer Forum",
                                                            "value": "vulval",
                                                        },
                                                        {
                                                            "label": "Womb Cancer Forum",
                                                            "value": "womb",
                                                        },
                                                    ],
                                                    value="all",  # Default to all forums
                                                    style={
                                                        "width": "14rem",
                                                        "font-size": "0.75rem",
                                                    },
                                                    clearable=False,
                                                ),
                                                width="auto",
                                                style={"padding-left": "0"},
                                            ),
                                        ],
                                        align="center",
                                        className="g-0",
                                    ),
                                ],
                                width="auto",
                            ),
                            # User info and sign-out section
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-user",
                                                    style={
                                                        "color": "#6c757d",
                                                        "margin-right": "0.5rem",
                                                        "font-size": "0.9rem",
                                                    },
                                                ),
                                                html.Span(
                                                    user_display,
                                                    style={
                                                        "color": "#f8f9fa",
                                                        "font-size": "0.8rem",
                                                        "font-weight": "500",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "display": "flex",
                                                "align-items": "center",
                                                "padding": "0.25rem 0.75rem",
                                                "background-color": "rgba(255, 255, 255, 0.1)",
                                                "border-radius": "0.25rem",
                                                "border": "1px solid rgba(255, 255, 255, 0.2)",
                                                "margin-right": "0.5rem",
                                            },
                                        ),
                                        dbc.Button(
                                            html.I(className="fas fa-sign-out-alt"),
                                            id="sign-out-button-forum",
                                            color="outline-light",
                                            size="sm",
                                            title="Sign Out",
                                            style={
                                                "font-size": "0.8rem",
                                                "padding": "0.25rem 0.5rem",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "align-items": "center",
                                    },
                                ),
                                width="auto",
                                style={"padding-left": "1rem"},
                            ),
                        ],
                        align="center",
                        className="g-0",
                    ),
                ],
                fluid=True,
                style={
                    "display": "flex",
                    "align-items": "center",
                    "justify-content": "space-between",
                },
            )
        ],
        id="main-navbar",  # Same ID as other navbars for consistent styling
        color="secondary",
        dark=True,
        className="py-2 border-bottom",
    )
