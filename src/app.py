import dash
import os
from dash import dcc, html, Dash, Output, Input, State
from dash_auth import BasicAuth
from callbacks.umap_callbacks import register_umap_callback
import dash_bootstrap_components as dbc
from utilities.mrpc_database import MRPCDatabase, setup_mrpc_database_callbacks
from utilities.auth import basic_auth_callback
from utilities.upload_callbacks import register_upload_callbacks
import callbacks.metadata_modal_callbacks  # noqa
from config import REMOTE_STYLES
from components.sidebar import sidebar

from dotenv import load_dotenv

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError

dbc_css = dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
)
# Initialize Dash app with pages support
app = Dash(
    __name__,
    use_pages=True,  # Enable Dash Pages
    external_stylesheets=[
        REMOTE_STYLES,
        dbc.themes.FLATLY,
        dbc.icons.FONT_AWESOME,
        dbc_css,
    ],
    suppress_callback_exceptions=True,
)

server = app.server  # Expose the server variable for deployments


auth = BasicAuth(app, auth_func=basic_auth_callback, secret_key=secret_key)


@app.server.route("/force-logout")
def force_logout():
    """Force a 401 to clear credentials after invalid auth attempt"""
    from flask import Response

    print("🚪 Force logout endpoint - sending 401 to clear credentials")
    response = Response(
        """
        <html>
        <head>
            <title>Signed Out</title>
        </head>
        <body>
        <h2>You have been signed out</h2>
        <p>Your authentication credentials have been cleared.</p>
        <p>Redirecting to login page...</p>
        </body>
        </html>
        """,
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )
    return response


# Create modern DBC navbar
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("CDE", href="/", className="fw-bold", id="navbar-brand"),
            dbc.NavbarToggler(id="sidebar-toggle", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(
                            dbc.Button(
                                [
                                    html.I(className="fas fa-sign-out-alt me-2"),
                                    "Sign Out",
                                ],
                                href="/force-logout",
                                external_link=True,
                                color="outline-light",
                                size="sm",
                                className="ms-2",
                            )
                        ),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                is_open=True,
                navbar=True,
            ),
        ],
        id="navbar-container",
    ),
    id="navbar",
    color="primary",
    dark=True,
    sticky="top",
    style={"height": "10vh"},
)


# Add a store component to track sidebar state - start collapsed
sidebar_state_store = dcc.Store(id="sidebar-collapsed", data=True)

# Register UMAP visualization callbacks (ONCE only)
register_umap_callback(app)

# Register upload page callbacks
register_upload_callbacks(app)

# Initialize MRPC Database system (single system, no fallbacks to avoid conflicts)
db = MRPCDatabase()
setup_mrpc_database_callbacks(app)
# print(" MRPC Database system loaded successfully")

my_page_container = html.Div(
    dash.page_container, id="my-page-container", className="mh-100"
)

app.layout = dbc.Container(
    [
        dcc.Location(id="location", refresh=False),
        dcc.Store(id="sidebar-collapsed", data=True),
        navbar,
        sidebar,
        my_page_container,
    ],
    fluid=True,
    style={"padding": "0", "max-height": "100vh"},
    class_name="dbc",
)


@app.callback(
    Output("sidebar", "is_open"),
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "is_open")],
)
def toggle_sidebar(n_clicks, is_open):
    """Toggle offcanvas sidebar visibility"""
    if n_clicks:
        return not is_open
    return is_open


# NOTE: I have done some git stupidity here and lost my URL appropriate output
@app.callback(
    Output("location", "search"),
    [Input("forum-data-table", "filter_query")],
)
def update_url_filter_query(filter_query):
    def generate_url_params_from_filter_query(filter_query):
        """Generate URL parameters from the filter query."""
        return f"?filter_query={filter_query}" if filter_query else ""

    """Update the URL with the current filter query from the DataTable"""
    print(f"🔍 DEBUG: Updating URL with filter_query={filter_query}")
    url_query_string = generate_url_params_from_filter_query(filter_query)
    # Encode the filter query as a URL parameter
    return f"?filter_query={url_query_string}" if filter_query else ""


if __name__ == "__main__":
    import os

    # Get configuration from environment variables
    debug = os.getenv("DASH_DEBUG", "True").lower() == "true"
    host = os.getenv("DASH_HOST", "127.0.0.1")
    port = int(os.getenv("DASH_PORT", "8055"))

    app.run(debug=debug, host=host, port=port)
