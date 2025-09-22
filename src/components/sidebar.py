import dash_bootstrap_components as dbc
import dash
from dash import html


sidebar = dbc.Offcanvas(
    [
        html.Div(
            [
                html.H4("Navigation", className="text-primary mb-3"),
                html.Hr(),
                dbc.Nav(
                    [
                        dbc.NavLink(
                            [html.I(className="fas fa-home me-2"), page["name"]],
                            href=page["relative_path"],
                            active="exact",
                            className="py-2",
                        )
                        for page in dash.page_registry.values()
                    ]
                    + [
                        html.Hr(),
                        dbc.NavLink(
                            [
                                html.I(className="fas fa-sign-out-alt me-2"),
                                "Sign Out",
                            ],
                            href="/sign-out",
                            external_link=True,
                            className="py-2 text-danger",
                        ),
                    ],
                    vertical=True,
                    pills=True,
                ),
            ],
            className="p-3",
        )
    ],
    id="sidebar",
    title="Navigation",
    is_open=False,
    placement="start",
    className="bg-light",
)
