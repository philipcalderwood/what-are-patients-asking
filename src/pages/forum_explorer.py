from dash import register_page, html
import dash_bootstrap_components as dbc

from components.metadata_sidebar import create_metadata_sidebar
from components.table_controls_col import metadata_modal, middle_col
from services.table_view import create_table_view

register_page(__name__, path="/forum-explorer", name="Forum Explorer")


def layout(**kwargs):
    return html.Div(
        [
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [create_table_view(**kwargs), metadata_modal()],
                                width={"size": 9, "order": 1},
                                lg=9,
                                md=9,
                                sm=9,
                                className="p-3 d-flex flex-column h-100 g-2",
                                id="table-view-column",
                            ),
                            # dbc.Col(
                            #     middle_col(),
                            #     width={"size": 0, "order": 2},
                            #     lg=0,
                            #     md=0,
                            #     sm=0,
                            #     className="",
                            #     id="table-controls-column",
                            # ),
                            dbc.Col(
                                create_metadata_sidebar(),
                                width={"size": 3, "order": 3},
                                lg=3,
                                md=3,
                                sm=12,
                                className="ps-1 d-flex flex-column h-100",
                                id="metadata-sidebar-column",
                            ),
                        ],
                        className="g-2 g-md-3 h-100",
                        id="table-view-rows",
                    )
                ],
                fluid=True,
                className="p-5 d-flex flex-column",
                id="forum-explorer-container",
                style={
                    "height": "90vh",  # Navbar given 10vh
                },
            ),
            # TODO: Remove and tidy up callback
            html.Div(id="tag-modal-container", children=[]),
        ],
    )
