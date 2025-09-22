#!/usr/bin/env python3

import dash
from dash import Dash, html
import dash_bootstrap_components as dbc
from components.sidebar import sidebar

def test_full_sidebar():
    app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.FLATLY])
    
    print(f'Pages discovered: {len(dash.page_registry)}')
    
    # Test the sidebar component
    print(f'Sidebar type: {type(sidebar)}')
    print(f'Sidebar id: {sidebar.id}')
    print(f'Sidebar children: {len(sidebar.children)}')
    
    # Create a simple layout with the sidebar
    app.layout = dbc.Container([
        dbc.Button("Toggle Sidebar", id="sidebar-toggle", className="mb-3"),
        sidebar,
        html.Div("Main content", id="main-content")
    ])
    
    return app

if __name__ == "__main__":
    test_full_sidebar()
