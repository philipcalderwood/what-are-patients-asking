#!/usr/bin/env python3

import dash
from dash import Dash, html, Input, Output
import dash_bootstrap_components as dbc
from components.sidebar import sidebar

def test_sidebar_browser():
    app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.FLATLY])
    
    # Create a simple layout with the sidebar
    app.layout = dbc.Container([
        dbc.Button("Toggle Sidebar", id="sidebar-toggle", className="mb-3"),
        sidebar,
        html.Div("Main content", id="main-content")
    ])
    
    # Add the toggle callback
    @app.callback(
        Output("sidebar", "is_open"),
        Input("sidebar-toggle", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(n_clicks):
        return True if n_clicks else False
    
    print(f'Starting app with {len(dash.page_registry)} pages registered')
    app.run(debug=True, port=8056)

if __name__ == "__main__":
    test_sidebar_browser()
