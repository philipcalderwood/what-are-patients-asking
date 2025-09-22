"""
Callback for the Basic Metadata modal
"""

from dash import callback, Input, Output, State


@callback(
    Output("basic-metadata-modal", "is_open"),
    Input("open-metadata-modal-btn", "n_clicks"),
    State("basic-metadata-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_metadata_modal(n_clicks, is_open):
    """Toggle the basic metadata modal open/closed"""
    if n_clicks:
        return not is_open
    return is_open
