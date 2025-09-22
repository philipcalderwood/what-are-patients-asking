"""
Transcription Analysis Page
Creates analysis dashboard for transcription data with interactive visualizations
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback, register_page
import plotly.graph_objects as go
import pandas as pd
from utilities.mrpc_database import MRPCDatabase
from utilities.upload_service import upload_service

# Register this page with Dash Pages
register_page(__name__, path="/transcription-analysis", name="Transcription Analysis")


def layout():
    """Layout function required by Dash Pages"""
    return create_transcription_analysis_page()


def create_transcription_analysis_page():
    """Create the main transcription analysis page"""

    return html.Div(
        [
            # Page content
            dbc.Container(
                [
                    html.H1("Transcription Data Analysis", className="mb-4"),
                    html.P(
                        "Analyze experimental transcription data across five key categories: "
                        "Digital Access, Emotional Response, Information Quality, Behavioral Outcomes, and Support Systems.",
                        className="lead mb-4",
                    ),
                    # Filter controls
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5("Filter Data", className="mb-3"),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Upload Filter:",
                                                        className="form-label",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="transcription-upload-filter",
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
                                                        id="transcription-date-filter",
                                                        display_format="YYYY-MM-DD",
                                                        className="mb-3",
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="transcription-filter-info",
                                        className="text-muted",
                                    ),
                                ]
                            )
                        ],
                        className="mb-4",
                    ),
                    # Analysis dashboard - shows all data by default
                    html.Div(id="transcription-analysis-content"),
                ],
                fluid=True,
            ),
        ]
    )


def create_transcription_dashboard(transcription_df: pd.DataFrame):
    """Create analysis dashboard for transcription data"""

    if transcription_df.empty:
        return dbc.Alert(
            "No transcription data available for analysis.",
            color="warning",
            className="mb-4",
        )

    # Calculate summary statistics
    total_sessions = len(transcription_df)
    unique_participants = (
        transcription_df["participant_id"].nunique()
        if "participant_id" in transcription_df.columns
        else 0
    )
    unique_uploads = (
        transcription_df["upload_id"].nunique()
        if "upload_id" in transcription_df.columns
        else 0
    )

    # Calculate date range if available
    date_range_text = "Date range not available"
    if "session_date" in transcription_df.columns:
        dates = pd.to_datetime(
            transcription_df["session_date"], errors="coerce"
        ).dropna()
        if not dates.empty:
            start_date = dates.min().strftime("%Y-%m-%d")
            end_date = dates.max().strftime("%Y-%m-%d")
            date_range_text = (
                f"{start_date} to {end_date}" if start_date != end_date else start_date
            )

    return html.Div(
        [
            # Enhanced summary stats
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                str(total_sessions),
                                                className="text-primary",
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
                                            html.P(
                                                "Unique Participants", className="mb-0"
                                            ),
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
                                                str(unique_uploads),
                                                className="text-info",
                                            ),
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
                                            html.H6(
                                                date_range_text,
                                                className="text-warning mb-1",
                                            ),
                                            html.P(
                                                "Date Range", className="mb-0 small"
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Key performance indicators
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                f"{(transcription_df['zoom_ease'].mean() * 100):.0f}%"
                                                if "zoom_ease"
                                                in transcription_df.columns
                                                else "N/A",
                                                className="text-success",
                                            ),
                                            html.P(
                                                "Zoom Accessibility",
                                                className="mb-0 small",
                                            ),
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
                                            html.H5(
                                                f"{transcription_df['reassurance_provided'].mean():.1f}/5"
                                                if "reassurance_provided"
                                                in transcription_df.columns
                                                else "N/A",
                                                className="text-primary",
                                            ),
                                            html.P(
                                                "Avg Reassurance",
                                                className="mb-0 small",
                                            ),
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
                                            html.H5(
                                                f"{(transcription_df['exercise_engaged'].mean() * 100):.0f}%"
                                                if "exercise_engaged"
                                                in transcription_df.columns
                                                else "N/A",
                                                className="text-info",
                                            ),
                                            html.P(
                                                "Exercise Engagement",
                                                className="mb-0 small",
                                            ),
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
                                            html.H5(
                                                f"{(transcription_df['family_involved'].mean() * 100):.0f}%"
                                                if "family_involved"
                                                in transcription_df.columns
                                                else "N/A",
                                                className="text-warning",
                                            ),
                                            html.P(
                                                "Family Support", className="mb-0 small"
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Visualization dashboard
            dbc.Row(
                [
                    dbc.Col([create_digital_access_summary(transcription_df)], width=6),
                    dbc.Col(
                        [create_emotional_response_chart(transcription_df)], width=6
                    ),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [create_behavioral_outcomes_chart(transcription_df)], width=6
                    ),
                    dbc.Col([create_info_quality_chart(transcription_df)], width=6),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [dbc.Col([create_support_systems_chart(transcription_df)], width=12)]
            ),
        ]
    )


def create_digital_access_summary(df):
    """Digital access metrics visualization"""

    # Calculate metrics
    metrics = {}
    if "zoom_ease" in df.columns:
        metrics["Zoom Ease"] = df["zoom_ease"].mean() * 100
    if "resource_access" in df.columns:
        metrics["Resource Access"] = df["resource_access"].mean() * 100
    if "poll_usability" in df.columns:
        metrics["Poll Usability (Avg)"] = df["poll_usability"].mean()

    if not metrics:
        return dbc.Card(
            [
                dbc.CardHeader("📱 Digital Access"),
                dbc.CardBody(
                    [dbc.Alert("No digital access data available", color="warning")]
                ),
            ]
        )

    # Create bar chart for percentage metrics
    percentage_metrics = {k: v for k, v in metrics.items() if "Usability" not in k}
    usability_metric = {k: v for k, v in metrics.items() if "Usability" in k}

    fig = go.Figure()

    if percentage_metrics:
        fig.add_trace(
            go.Bar(
                x=list(percentage_metrics.keys()),
                y=list(percentage_metrics.values()),
                name="Success Rate (%)",
                marker_color="lightblue",
                yaxis="y",
            )
        )

    if usability_metric:
        fig.add_trace(
            go.Bar(
                x=list(usability_metric.keys()),
                y=list(usability_metric.values()),
                name="Rating (1-5)",
                marker_color="lightgreen",
                yaxis="y2",
            )
        )

    fig.update_layout(
        title="Digital Access Metrics",
        yaxis=dict(title="Percentage (%)", side="left"),
        yaxis2=dict(title="Rating (1-5)", side="right", overlaying="y", range=[0, 5]),
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return dbc.Card(
        [
            dbc.CardHeader("📱 Digital Access"),
            dbc.CardBody([dcc.Graph(figure=fig, config={"displayModeBar": False})]),
        ]
    )


def create_emotional_response_chart(df):
    """Emotional response trends visualization"""

    emotional_columns = ["presession_anxiety", "reassurance_provided"]
    available_columns = [col for col in emotional_columns if col in df.columns]

    if not available_columns:
        return dbc.Card(
            [
                dbc.CardHeader("💭 Emotional Response"),
                dbc.CardBody(
                    [dbc.Alert("No emotional response data available", color="warning")]
                ),
            ]
        )

    fig = go.Figure()

    for col in available_columns:
        values = df[col].dropna()

        fig.add_trace(
            go.Box(
                y=values,
                name=col.replace("_", " ").title(),
                boxpoints="all",
                jitter=0.3,
                pointpos=-1.8,
            )
        )

    fig.update_layout(
        title="Emotional Response Distribution",
        yaxis_title="Rating (1-5)",
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return dbc.Card(
        [
            dbc.CardHeader("💭 Emotional Response"),
            dbc.CardBody([dcc.Graph(figure=fig, config={"displayModeBar": False})]),
        ]
    )


def create_behavioral_outcomes_chart(df):
    """Behavioral outcomes visualization"""

    behavioral_columns = ["exercise_engaged", "lifestyle_change", "postop_adherence"]
    available_columns = [col for col in behavioral_columns if col in df.columns]

    if not available_columns:
        return dbc.Card(
            [
                dbc.CardHeader("🎯 Behavioral Outcomes"),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            "No behavioral outcomes data available", color="warning"
                        )
                    ]
                ),
            ]
        )

    # Calculate success rates
    success_rates = {}
    for col in available_columns:
        success_rate = df[col].mean() * 100 if not df[col].isna().all() else 0
        success_rates[col.replace("_", " ").title()] = success_rate

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(success_rates.keys()),
                y=list(success_rates.values()),
                marker_color=["#1f77b4", "#ff7f0e", "#2ca02c"][: len(success_rates)],
            )
        ]
    )

    fig.update_layout(
        title="Behavioral Outcomes Success Rate",
        yaxis_title="Success Rate (%)",
        yaxis=dict(range=[0, 100]),
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return dbc.Card(
        [
            dbc.CardHeader("🎯 Behavioral Outcomes"),
            dbc.CardBody([dcc.Graph(figure=fig, config={"displayModeBar": False})]),
        ]
    )


def create_info_quality_chart(df):
    """Information quality assessment visualization"""

    info_columns = ["info_useful", "info_missing", "info_takeaway_desired"]
    available_columns = [col for col in info_columns if col in df.columns]

    if not available_columns:
        return dbc.Card(
            [
                dbc.CardHeader("Information Quality"),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            "No information quality data available", color="warning"
                        )
                    ]
                ),
            ]
        )

    fig = go.Figure()

    # Handle different data types
    for col in available_columns:
        values = df[col].dropna()

        if col == "info_useful":
            # Likert scale - show distribution
            fig.add_trace(
                go.Histogram(
                    x=values,
                    name="Usefulness Rating",
                    nbinsx=5,
                    marker_color="lightblue",
                )
            )
        else:
            # Binary - show percentage
            percentage = values.mean() * 100 if len(values) > 0 else 0
            fig.add_trace(
                go.Bar(
                    x=[col.replace("_", " ").title()],
                    y=[percentage],
                    name=col.replace("_", " ").title(),
                    marker_color="lightcoral",
                )
            )

    fig.update_layout(
        title="Information Quality Metrics",
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return dbc.Card(
        [
            dbc.CardHeader("Information Quality"),
            dbc.CardBody([dcc.Graph(figure=fig, config={"displayModeBar": False})]),
        ]
    )


def create_support_systems_chart(df):
    """Support systems analysis visualization"""

    support_columns = ["family_involved", "support_needed"]
    available_columns = [col for col in support_columns if col in df.columns]

    if not available_columns:
        return dbc.Card(
            [
                dbc.CardHeader("🤝 Support Systems"),
                dbc.CardBody(
                    [dbc.Alert("No support systems data available", color="warning")]
                ),
            ]
        )

    # Create a comprehensive support analysis
    support_data = {}
    for col in available_columns:
        if not df[col].isna().all():
            support_data[col.replace("_", " ").title()] = df[col].mean() * 100

    if not support_data:
        return dbc.Card(
            [
                dbc.CardHeader("🤝 Support Systems"),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            "No valid support systems data available", color="warning"
                        )
                    ]
                ),
            ]
        )

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(support_data.keys()),
                y=list(support_data.values()),
                marker_color="mediumpurple",
            )
        ]
    )

    fig.update_layout(
        title="Support Systems Engagement",
        yaxis_title="Engagement Rate (%)",
        yaxis=dict(range=[0, 100]),
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return dbc.Card(
        [
            dbc.CardHeader("🤝 Support Systems"),
            dbc.CardBody([dcc.Graph(figure=fig, config={"displayModeBar": False})]),
        ]
    )


# Callback for loading transcription upload filter options
@callback(
    Output("transcription-upload-filter", "options"),
    Input("transcription-upload-filter", "id"),
)
def load_transcription_upload_options(_):
    """Load available transcription uploads for filtering"""
    try:
        # Get transcription uploads only
        uploads = upload_service.get_user_uploads(
            upload_type="transcription_data", status="active"
        )

        if not uploads:
            return []

        options = []
        for upload in uploads:
            label = f"{upload.get('user_readable_name', 'Unnamed')} ({upload.get('created_at', 'Unknown date')})"
            options.append({"label": label, "value": upload.get("id")})

        return options

    except Exception as e:
        print(f"Error loading transcription uploads for filter: {e}")
        return []


# Callback for displaying filter info and analysis (loads all data by default)
@callback(
    [
        Output("transcription-filter-info", "children"),
        Output("transcription-analysis-content", "children"),
    ],
    [
        Input("transcription-upload-filter", "value"),
        Input("transcription-date-filter", "start_date"),
        Input("transcription-date-filter", "end_date"),
    ],
)
def update_transcription_analysis_with_filters(
    selected_upload_id, start_date, end_date
):
    """Update analysis based on filters (shows all data by default)"""

    try:
        # Get all transcription data first
        db = MRPCDatabase()
        all_transcription_data = db.get_all_transcription_data()

        if not all_transcription_data:
            return "No transcription data available", dbc.Alert(
                "No transcription data found. Please upload transcription data first.",
                color="info",
                className="mb-4",
            )

        # Convert to DataFrame for easier filtering
        df = pd.DataFrame(all_transcription_data)

        # Convert boolean fields to proper boolean values for calculations
        boolean_fields = [
            "zoom_ease",
            "resource_access",
            "info_useful",
            "info_missing",
            "info_takeaway_desired",
            "exercise_engaged",
            "lifestyle_change",
            "postop_adherence",
            "family_involved",
            "support_needed",
        ]

        for field in boolean_fields:
            if field in df.columns:
                # Clean conversion: Only accept True/False and 0/1, reject Likert scale values
                def convert_boolean(x):
                    if pd.isna(x):
                        return None
                    # Handle proper boolean values
                    if x is True or str(x).lower().strip() == "true":
                        return True
                    elif x is False or str(x).lower().strip() == "false":
                        return False
                    # Handle 0/1 integer values
                    elif x == 1:
                        return True
                    elif x == 0:
                        return False
                    else:
                        # Reject Likert scale and other invalid values
                        print(
                            f"⚠️ Rejecting non-boolean value: {x} (type: {type(x)}) in field {field}"
                        )
                        return None

                df[field] = df[field].map(convert_boolean)

        # Apply upload filter if selected
        if selected_upload_id:
            df = df[df["upload_id"] == selected_upload_id]
            upload_filter_text = (
                f"Upload: {df['upload_name'].iloc[0] if not df.empty else 'Unknown'}"
            )
        else:
            upload_filter_text = "All uploads"

        # Apply date filter if provided
        if start_date or end_date:
            # Convert session_date to datetime for filtering
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

        # Create filter info display
        total_sessions = len(df)
        unique_uploads = df["upload_id"].nunique() if not df.empty else 0
        filter_info = f"Showing {total_sessions} sessions from {unique_uploads} uploads. Filters: {upload_filter_text}, {date_filter_text}"

        if df.empty:
            return filter_info, dbc.Alert(
                "No data matches the selected filters. Please adjust your filter criteria.",
                color="warning",
                className="mb-4",
            )

        # Create analysis dashboard with filtered data
        dashboard = create_transcription_dashboard(df)

        return filter_info, dashboard

    except Exception as e:
        error_msg = f"Error loading transcription analysis: {e}"
        print(error_msg)
        return "Error loading data", dbc.Alert(f"Error: {e}", color="danger")
