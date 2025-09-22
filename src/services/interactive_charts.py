"""
Interactive Charts Module

This module contains functions for creating interactive Dash/Plotly charts
for the MRPC Data Explorer application.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utilities.mrpc_database import MRPCDatabase


def create_posts_per_category_timeline(df):
    """Create an interactive timeline chart showing posts per category aggregated by day"""
    if df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            title="No data available for timeline chart",
            xaxis_title="Date",
            yaxis_title="Number of Posts",
            height=400,
        )
        return fig

    # Robust date parsing with error handling
    df = df.copy()

    try:
        # First attempt: try to parse dates with error handling
        df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")

        # Check how many dates failed to parse
        invalid_dates = df["date_posted"].isna().sum()
        total_rows = len(df)

        if invalid_dates > 0:
            print(
                f"⚠️ Warning: {invalid_dates}/{total_rows} dates could not be parsed and will be excluded"
            )

        # Remove rows with invalid dates
        df = df.dropna(subset=["date_posted"])

        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                title="No valid dates found in data",
                xaxis_title="Date",
                yaxis_title="Number of Posts",
                height=400,
                annotations=[
                    {
                        "text": f"All {total_rows} date entries were invalid",
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": 0.5,
                        "showarrow": False,
                        "font": {"size": 16, "color": "red"},
                    }
                ],
            )
            return fig

    except Exception as e:
        print(f"❌ Error parsing dates: {str(e)}")
        fig = go.Figure()
        fig.update_layout(
            title="Error parsing date data",
            xaxis_title="Date",
            yaxis_title="Number of Posts",
            height=400,
            annotations=[
                {
                    "text": f"Date parsing error: {str(e)[:100]}...",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 14, "color": "red"},
                }
            ],
        )
        return fig

    # Extract date (without time) for daily aggregation
    df["date"] = df["date_posted"].dt.date

    # Use llm_cluster_name as the category (more readable than cluster_label)
    category_col = (
        "llm_cluster_name" if "llm_cluster_name" in df.columns else "cluster_label"
    )

    # Group by date and category, count posts
    timeline_data = (
        df.groupby(["date", category_col]).size().reset_index(name="post_count")
    )

    # Get unique categories for color assignment
    categories = timeline_data[category_col].unique()

    # Create color palette
    colors = px.colors.qualitative.Set3
    if len(categories) > len(colors):
        colors = colors * (len(categories) // len(colors) + 1)

    # Create figure
    fig = go.Figure()

    # Add trace for each category
    for i, category in enumerate(categories):
        category_data = timeline_data[timeline_data[category_col] == category]

        # Truncate long category names for legend
        display_name = (
            category[:50] + "..." if len(str(category)) > 50 else str(category)
        )

        fig.add_trace(
            go.Scatter(
                x=category_data["date"],
                y=category_data["post_count"],
                mode="lines+markers",
                name=display_name,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6),
                hovertemplate=f"<b>{display_name}</b><br>"
                + "Date: %{x}<br>"
                + "Posts: %{y}<br>"
                + "<extra></extra>",
            )
        )

    # Update layout
    fig.update_layout(
        title="Posts per Category Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Posts",
        height=500,
        hovermode="x unified",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
        ),
        margin=dict(l=60, r=150, t=80, b=60),
        showlegend=True,
    )

    # Make x-axis show dates nicely
    fig.update_xaxes(tickformat="%b %d\n%Y", tickangle=45)

    return fig


def create_category_distribution_chart(df):
    """Create a pie chart showing distribution of posts across categories"""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No data available for category distribution",
            height=400,
        )
        return fig

    # Use llm_cluster_name as the category
    category_col = (
        "llm_cluster_name" if "llm_cluster_name" in df.columns else "cluster_label"
    )

    # Count posts per category
    category_counts = df[category_col].value_counts()

    # Create pie chart
    fig = go.Figure(
        data=[
            go.Pie(
                labels=category_counts.index,
                values=category_counts.values,
                hole=0.3,  # Make it a donut chart
                hovertemplate="<b>%{label}</b><br>Posts: %{value}<br>Percentage: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="Posts Distribution by Category",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
        ),
        margin=dict(l=60, r=150, t=80, b=60),
    )

    return fig


def create_forum_activity_heatmap(df):
    """Create a heatmap showing activity patterns by forum and time"""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No data available for activity heatmap",
            height=400,
        )
        return fig

    # Robust date parsing with error handling
    df = df.copy()

    try:
        # Parse dates with error handling
        df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")

        # Remove rows with invalid dates
        invalid_dates = df["date_posted"].isna().sum()
        if invalid_dates > 0:
            print(f"⚠️ Warning: {invalid_dates} dates could not be parsed for heatmap")

        df = df.dropna(subset=["date_posted"])

        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                title="No valid dates found for activity heatmap",
                height=400,
            )
            return fig

        # Extract day of week and hour
        df["day_of_week"] = df["date_posted"].dt.day_name()
        df["hour"] = df["date_posted"].dt.hour

    except Exception as e:
        print(f"❌ Error parsing dates for heatmap: {str(e)}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating activity heatmap",
            height=400,
        )
        return fig

    # Group by forum, day of week, and hour
    heatmap_data = (
        df.groupby(["forum", "day_of_week", "hour"])
        .size()
        .reset_index(name="post_count")
    )

    # Create pivot table for heatmap
    pivot_data = heatmap_data.pivot_table(
        index=["forum", "day_of_week"],
        columns="hour",
        values="post_count",
        fill_value=0,
    )

    # Create heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_data.values,
            x=list(range(24)),  # Hours 0-23
            y=[f"{forum} - {day}" for forum, day in pivot_data.index],
            colorscale="Blues",
            hovertemplate="Hour: %{x}<br>Forum/Day: %{y}<br>Posts: %{z}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Forum Activity Heatmap (by Day and Hour)",
        xaxis_title="Hour of Day",
        yaxis_title="Forum - Day of Week",
        height=600,
        margin=dict(l=200, r=60, t=80, b=60),
    )

    return fig


def get_chart_data(forum="all"):
    """Get data for charts from database"""
    db = MRPCDatabase()
    if forum == "all":
        return db.get_all_posts_as_dataframe()
    else:
        return db.get_posts_by_forum(forum)
