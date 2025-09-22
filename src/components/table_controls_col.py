from dash import html
import dash_bootstrap_components as dbc


def metadata_modal():
    return dbc.Modal(
        # Basic Metadata Card (positioned between table controls and reading pane)
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.I(className="fas fa-info-circle me-2"),
                                        html.Span(
                                            "Basic Metadata", className="fw-bold"
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="align-items-center",
                        )
                    ],
                    className="py-3 px-4 text-white bg-secondary",
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            id="basic-metadata-content",
                            children=[
                                dbc.Alert(
                                    [
                                        html.I(className="fas fa-info-circle me-2"),
                                        "Click on a row to see basic metadata",
                                    ],
                                    color="light",
                                    className="text-center mb-0",
                                )
                            ],
                            className="metadata-content",
                        )
                    ],
                    className="p-3",
                ),
            ],
            className="",
            outline=True,
            style={
                "flex-shrink": "0",
            },
            id="basic-metadata-card",
        ),
        id="basic-metadata-modal",
    )


def middle_col():
    """Create the table controls sidebar component with dbc cards"""

    middle_col = dbc.Stack(
        [
            # Table Controls Card (fixed at top, standalone appearance)
            # dbc.Card(
            #     [
            #         dbc.CardHeader(
            #             [
            #                 html.I(className="fas fa-cogs me-2"),
            #                 html.Span("Table Controls", className="fw-bold"),
            #             ],
            #             className="py-3 px-4 bg-primary text-white",
            #         ),
            #         dbc.CardBody(
            #             [
            #                 # Pagination controls at the top
            #                 html.Div(
            #                     [
            #                         dbc.ButtonGroup(
            #                             [
            #                                 dbc.Button(
            #                                     "‹‹",
            #                                     id="page-first-btn",
            #                                     size="sm",
            #                                     outline=True,
            #                                     color="primary",
            #                                     style={"font-size": "0.7rem"},
            #                                 ),
            #                                 dbc.Button(
            #                                     "‹",
            #                                     id="page-prev-btn",
            #                                     size="sm",
            #                                     outline=True,
            #                                     color="primary",
            #                                     style={"font-size": "0.7rem"},
            #                                 ),
            #                                 html.Span(
            #                                     id="page-info",
            #                                     children="Page 1 of 1",
            #                                     style={
            #                                         "font-size": "0.7rem",
            #                                         "line-height": "2rem",
            #                                         "margin": "0 0.5rem",
            #                                         "white-space": "nowrap",
            #                                         "color": "#6c757d",
            #                                     },
            #                                 ),
            #                                 dbc.Button(
            #                                     "›",
            #                                     id="page-next-btn",
            #                                     size="sm",
            #                                     outline=True,
            #                                     color="primary",
            #                                     style={"font-size": "0.7rem"},
            #                                 ),
            #                                 dbc.Button(
            #                                     "››",
            #                                     id="page-last-btn",
            #                                     size="sm",
            #                                     outline=True,
            #                                     color="primary",
            #                                     style={"font-size": "0.7rem"},
            #                                 ),
            #                             ],
            #                             size="sm",
            #                             className="d-flex align-items-center justify-content-center mb-3",
            #                         ),
            #                     ],
            #                 ),
            #                 # Forum selector
            #                 html.Div(
            #                     [
            #                         html.Label(
            #                             "Forum:",
            #                             className="form-label mb-2",
            #                             style={
            #                                 "font-size": "0.8rem",
            #                                 "font-weight": "bold",
            #                             },
            #                         ),
            #                         dcc.Dropdown(
            #                             id="table-forum-selector",
            #                             options=[
            #                                 {"label": "All Forums", "value": "all"},
            #                                 {
            #                                     "label": "Cervical Cancer Forum",
            #                                     "value": "cervical",
            #                                 },
            #                                 {
            #                                     "label": "Ovarian Cancer Forum",
            #                                     "value": "ovarian",
            #                                 },
            #                                 {
            #                                     "label": "Vaginal Cancer Forum",
            #                                     "value": "vaginal",
            #                                 },
            #                                 {
            #                                     "label": "Vulval Cancer Forum",
            #                                     "value": "vulval",
            #                                 },
            #                                 {
            #                                     "label": "Womb Cancer Forum",
            #                                     "value": "womb",
            #                                 },
            #                             ],
            #                             value="all",
            #                             style={
            #                                 "font-size": "0.8rem",
            #                                 "margin-bottom": "1rem",
            #                             },
            #                         ),
            #                     ],
            #                 ),
            #                 # Export controls
            #                 html.Div(
            #                     [
            #                         html.Label(
            #                             "Export Data:",
            #                             className="form-label mb-2",
            #                             style={"font-size": "0.8rem"},
            #                         ),
            #                         dbc.ButtonGroup(
            #                             [
            #                                 dbc.Button(
            #                                     "Export CSV",
            #                                     id="export-csv-btn",
            #                                     size="sm",
            #                                     color="secondary",
            #                                     outline=True,
            #                                     style={"font-size": "0.7rem"},
            #                                 ),
            #                                 dbc.Button(
            #                                     "Export Filtered",
            #                                     id="export-filtered-btn",
            #                                     size="sm",
            #                                     color="secondary",
            #                                     outline=True,
            #                                     style={"font-size": "0.7rem"},
            #                                 ),
            #                             ],
            #                             size="sm",
            #                         ),
            #                     ],
            #                 ),
            #             ],
            #             className="p-2",
            #         ),
            #     ],
            #     id="table-controls-section",
            #     style={
            #         "display": "block",
            #         "border": "1px solid #dee2e6",
            #         "border-radius": "0.375rem",
            #         "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
            #         "background-color": "#ffffff",
            #         "margin-bottom": "0.75rem",
            #         "flex-shrink": "0",  # Don't allow shrinking
            #     },  # Fixed standalone card at top
            # ),
            # # Basic Metadata Card (positioned between table controls and reading pane)
            # dbc.Card(
            #     [
            #         dbc.CardHeader(
            #             [
            #                 dbc.Row(
            #                     [
            #                         dbc.Col(
            #                             [
            #                                 html.I(className="fas fa-info-circle me-2"),
            #                                 html.Span(
            #                                     "Basic Metadata", className="fw-bold"
            #                                 ),
            #                             ],
            #                             width=12,
            #                         )
            #                     ],
            #                     className="align-items-center",
            #                 )
            #             ],
            #             className="py-3 px-4 text-white bg-secondary",
            #         ),
            #         dbc.CardBody(
            #             [
            #                 html.Div(
            #                     id="basic-metadata-content",
            #                     children=[
            #                         dbc.Alert(
            #                             [
            #                                 html.I(className="fas fa-info-circle me-2"),
            #                                 "Click on a row to see basic metadata",
            #                             ],
            #                             color="light",
            #                             className="text-center mb-0",
            #                         )
            #                     ],
            #                     className="metadata-content",
            #                 )
            #             ],
            #             className="p-3",
            #         ),
            #     ],
            #     className="",
            #     outline=True,
            #     style={"flex-shrink": "0", "visibility": "hidden"},
            #     id="basic-metadata-card",
            # ),
        ],
        className="h-100 d-flex flex-column",
        id="middle-column",
    )
    return middle_col, metadata_modal()
