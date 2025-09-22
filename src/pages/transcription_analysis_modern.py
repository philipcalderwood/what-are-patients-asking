"""
Modern Dash Transcription Analysis Page
Proper Dash component structure with clean separation of concerns
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, register_page
import plotly.graph_objects as go
import pandas as pd
from utilities.mrpc_database import MRPCDatabase

# Register this page with Dash Pages
register_page(
    __name__,
    path="/modern-transcription-analysis",
    name="Modern Transcription Analysis",
)


def layout():
    """Layout function required by Dash Pages"""
    return create_transcription_analysis_page()


def create_transcription_analysis_page():
    """Create the main transcription analysis page with proper Dash structure"""

    return html.Div(
        [
            dbc.Container(
                [
                    # Header
                    html.H1("Transcription Data Analysis", className="mb-4"),
                    html.P(
                        "Modern Dash analysis of experimental transcription data across five key categories.",
                        className="lead mb-4",
                    ),
                    # Filters Card
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5("Data Filters", className="mb-3"),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Upload Filter:",
                                                        className="form-label",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="modern-transcription-upload-filter",
                                                        placeholder="All Uploads (default)",
                                                        className="mb-3",
                                                        clearable=True,
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Date Range:",
                                                        className="form-label",
                                                    ),
                                                    dcc.DatePickerRange(
                                                        id="modern-transcription-date-filter",
                                                        display_format="YYYY-MM-DD",
                                                        className="mb-3",
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="modern-filter-status",
                                        className="text-muted",
                                    ),
                                ]
                            )
                        ],
                        className="mb-4",
                    ),
                    # Summary Stats Card
                    dbc.Card(
                        [
                            dbc.CardHeader("Data Summary"),
                            dbc.CardBody([html.Div(id="modern-summary-stats")]),
                        ],
                        className="mb-4",
                    ),
                    # Poll Usability Analysis Card
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                "Poll Usability Analysis (Likert Scale 1-5)"
                            ),
                            dbc.CardBody(
                                [
                                    dcc.Graph(id="modern-poll-usability-chart"),
                                    html.Hr(),
                                    html.Div(id="modern-poll-usability-stats"),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Digital Access Analysis Card
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                "💻 Digital Access Analysis (Boolean Fields)"
                            ),
                            dbc.CardBody(
                                [
                                    dcc.Graph(id="modern-digital-access-chart"),
                                    html.Hr(),
                                    html.Div(id="modern-digital-access-stats"),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                ],
                fluid=True,
            ),
        ]
    )


# Callback to load upload options
@callback(
    Output("modern-transcription-upload-filter", "options"),
    Input("modern-transcription-upload-filter", "id"),
)
def load_upload_options(_):
    """Load available uploads for filtering"""
    try:
        db = MRPCDatabase()
        all_data = db.get_all_transcription_data()

        if not all_data:
            return []

        df = pd.DataFrame(all_data)

        # Get unique uploads
        upload_options = []
        if "upload_id" in df.columns and "upload_name" in df.columns:
            uploads = df[["upload_id", "upload_name"]].drop_duplicates()
            upload_options = [
                {
                    "label": f"{row['upload_name']} (ID: {row['upload_id']})",
                    "value": row["upload_id"],
                }
                for _, row in uploads.iterrows()
            ]

        return upload_options

    except Exception as e:
        print(f"Error loading upload options: {e}")
        return []


# Main callback to update all charts and stats
@callback(
    [
        Output("modern-filter-status", "children"),
        Output("modern-summary-stats", "children"),
        Output("modern-poll-usability-chart", "figure"),
        Output("modern-poll-usability-stats", "children"),
        Output("modern-digital-access-chart", "figure"),
        Output("modern-digital-access-stats", "children"),
    ],
    [
        Input("modern-transcription-upload-filter", "value"),
        Input("modern-transcription-date-filter", "start_date"),
        Input("modern-transcription-date-filter", "end_date"),
    ],
)
def update_analysis(selected_upload_id, start_date, end_date):
    """Update all analysis components based on filters"""

    try:
        # Load data
        db = MRPCDatabase()
        all_data = db.get_all_transcription_data()

        if not all_data:
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text="No data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return (
                "No data available",
                "No transcription data found",
                empty_fig,
                "No data available",
                empty_fig,
                "No data available",
            )

        df = pd.DataFrame(all_data)

        # Apply filters
        original_count = len(df)

        if selected_upload_id:
            df = df[df["upload_id"] == selected_upload_id]
            upload_filter_text = (
                f"Upload: {df['upload_name'].iloc[0] if not df.empty else 'Unknown'}"
            )
        else:
            upload_filter_text = "All uploads"

        if start_date or end_date:
            df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce")
            if start_date:
                df = df[df["session_date"] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df["session_date"] <= pd.to_datetime(end_date)]
            date_filter_text = (
                f"Date range: {start_date or 'Beginning'} to {end_date or 'Now'}"
            )
        else:
            date_filter_text = "All dates"

        filtered_count = len(df)
        filter_status = f"Showing {filtered_count} of {original_count} sessions. Filters: {upload_filter_text}, {date_filter_text}"

        if df.empty:
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text="No data matches filters",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return (
                filter_status,
                "No data matches the selected filters",
                empty_fig,
                "No data available",
                empty_fig,
                "No data available",
            )

        # Generate components
        summary_stats = create_summary_stats(df)
        poll_fig, poll_stats = create_poll_usability_analysis(df)
        digital_fig, digital_stats = create_digital_access_analysis(df)

        return (
            filter_status,
            summary_stats,
            poll_fig,
            poll_stats,
            digital_fig,
            digital_stats,
        )

    except Exception as e:
        error_msg = f"Error updating analysis: {e}"
        print(error_msg)
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Error loading data",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return (
            "Error loading data",
            error_msg,
            empty_fig,
            error_msg,
            empty_fig,
            error_msg,
        )


def create_summary_stats(df):
    """Create summary statistics component"""
    total_sessions = len(df)
    unique_participants = (
        df["participant_id"].nunique() if "participant_id" in df.columns else 0
    )
    unique_uploads = df["upload_id"].nunique() if "upload_id" in df.columns else 0

    # Date range
    date_range_text = "Date range not available"
    if "session_date" in df.columns:
        dates = pd.to_datetime(df["session_date"], errors="coerce").dropna()
        if not dates.empty:
            start_date = dates.min().strftime("%Y-%m-%d")
            end_date = dates.max().strftime("%Y-%m-%d")
            date_range_text = (
                f"{start_date} to {end_date}" if start_date != end_date else start_date
            )

    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(
                                        str(total_sessions), className="text-primary"
                                    ),
                                    html.P("Total Sessions", className="mb-0"),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(
                                        str(unique_participants),
                                        className="text-success",
                                    ),
                                    html.P("Unique Participants", className="mb-0"),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(str(unique_uploads), className="text-info"),
                                    html.P("Data Sources", className="mb-0"),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6(date_range_text, className="text-muted"),
                                    html.P("Date Range", className="mb-0"),
                                ]
                            )
                        ]
                    )
                ],
                width=3,
            ),
        ]
    )


def create_poll_usability_analysis(df):
    """Create poll usability analysis with proper Plotly visualization"""

    if "poll_usability" not in df.columns:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Poll usability data not available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return empty_fig, "Poll usability data not available"

    # Clean the data
    usability_data = df["poll_usability"].dropna()

    if usability_data.empty:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="No valid poll usability data",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return empty_fig, "No valid poll usability data"

    # Create distribution chart
    fig = go.Figure()

    # Histogram
    fig.add_trace(
        go.Histogram(
            x=usability_data,
            nbinsx=5,
            name="Distribution",
            marker_color="lightblue",
            opacity=0.7,
        )
    )

    # Add mean line
    mean_value = usability_data.mean()
    fig.add_vline(
        x=mean_value,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_value:.1f}",
    )

    fig.update_layout(
        title="Poll Usability Ratings Distribution (1-5 Scale)",
        xaxis_title="Usability Rating",
        yaxis_title="Number of Sessions",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(range=[0.5, 5.5], dtick=1),
    )

    # Create statistics
    stats = dbc.Row(
        [
            dbc.Col(
                [
                    html.H6("Mean Rating"),
                    html.H4(f"{mean_value:.2f}", className="text-primary"),
                ],
                width=2,
            ),
            dbc.Col(
                [
                    html.H6("Median Rating"),
                    html.H4(f"{usability_data.median():.1f}", className="text-success"),
                ],
                width=2,
            ),
            dbc.Col(
                [
                    html.H6("Standard Deviation"),
                    html.H4(f"{usability_data.std():.2f}", className="text-info"),
                ],
                width=2,
            ),
            dbc.Col(
                [
                    html.H6("High Ratings (4-5)"),
                    html.H4(
                        f"{len(usability_data[usability_data >= 4])}",
                        className="text-warning",
                    ),
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.H6("Low Ratings (1-2)"),
                    html.H4(
                        f"{len(usability_data[usability_data <= 2])}",
                        className="text-danger",
                    ),
                ],
                width=3,
            ),
        ]
    )

    return fig, stats


def create_digital_access_analysis(df):
    """Create digital access analysis for boolean fields"""

    digital_fields = ["zoom_ease", "resource_access"]
    available_fields = [field for field in digital_fields if field in df.columns]

    if not available_fields:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Digital access data not available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return empty_fig, "Digital access data not available"

    # Convert boolean fields
    success_rates = {}
    for field in available_fields:
        # Clean boolean conversion
        field_data = (
            df[field]
            .map(
                lambda x: True
                if x is True or str(x).lower().strip() == "true" or x == 1
                else False
                if x is False or str(x).lower().strip() == "false" or x == 0
                else None
            )
            .dropna()
        )

        if not field_data.empty:
            success_rate = (field_data.sum() / len(field_data)) * 100
            success_rates[field.replace("_", " ").title()] = success_rate

    if not success_rates:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="No valid digital access data",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return empty_fig, "No valid digital access data"

    # Create bar chart
    fig = go.Figure(
        data=[
            go.Bar(
                x=list(success_rates.keys()),
                y=list(success_rates.values()),
                marker_color=["#1f77b4", "#ff7f0e"],
                text=[f"{rate:.1f}%" for rate in success_rates.values()],
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title="Digital Access Success Rates",
        yaxis_title="Success Rate (%)",
        yaxis=dict(range=[0, 100]),
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
    )

    # Create statistics
    stats_cards = []
    for field, rate in success_rates.items():
        stats_cards.append(
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6(field),
                                    html.H4(f"{rate:.1f}%", className="text-primary"),
                                    html.P("Success Rate", className="mb-0 text-muted"),
                                ]
                            )
                        ]
                    )
                ],
                width=6,
            )
        )

    stats = dbc.Row(stats_cards)

    return fig, stats
