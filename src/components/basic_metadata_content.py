def create_basic_metadata_content(point, customdata):
    """Create basic metadata content (original title, username, date, link)"""
    from dash import html

    # Extract basic metadata from customdata
    forum = customdata[1] if len(customdata) > 1 else "N/A"
    post_type = customdata[2] if len(customdata) > 2 else "N/A"
    username = customdata[3] if len(customdata) > 3 else "N/A"
    original_title = customdata[4] if len(customdata) > 4 else "N/A"
    post_url = customdata[5] if len(customdata) > 5 else "N/A"
    date_posted = customdata[9] if len(customdata) > 9 else "N/A"

    # Format the basic metadata
    metadata_items = []

    # Original Title
    if original_title and original_title != "N/A":
        metadata_items.append(
            html.Div(
                [
                    html.Strong(
                        "Title: ", style={"color": "#495057", "font-size": "0.8rem"}
                    ),
                    html.Span(
                        original_title,
                        style={"font-size": "0.8rem", "word-wrap": "break-word"},
                    ),
                ],
                style={"margin-bottom": "0.5rem"},
            )
        )

    # Username
    if username and username != "N/A":
        metadata_items.append(
            html.Div(
                [
                    html.Strong(
                        "Username: ", style={"color": "#495057", "font-size": "0.8rem"}
                    ),
                    html.Span(username, style={"font-size": "0.8rem"}),
                ],
                style={"margin-bottom": "0.5rem"},
            )
        )

    # Forum
    if forum and forum != "N/A":
        metadata_items.append(
            html.Div(
                [
                    html.Strong(
                        "Forum: ", style={"color": "#495057", "font-size": "0.8rem"}
                    ),
                    html.Span(forum.title(), style={"font-size": "0.8rem"}),
                ],
                style={"margin-bottom": "0.5rem"},
            )
        )

    # Date Posted
    if date_posted and date_posted != "N/A":
        metadata_items.append(
            html.Div(
                [
                    html.Strong(
                        "Date Posted: ",
                        style={"color": "#495057", "font-size": "0.8rem"},
                    ),
                    html.Span(str(date_posted), style={"font-size": "0.8rem"}),
                ],
                style={"margin-bottom": "0.5rem"},
            )
        )

    # Post Type
    if post_type and post_type != "N/A":
        metadata_items.append(
            html.Div(
                [
                    html.Strong(
                        "Post Type: ", style={"color": "#495057", "font-size": "0.8rem"}
                    ),
                    html.Span(post_type, style={"font-size": "0.8rem"}),
                ],
                style={"margin-bottom": "0.5rem"},
            )
        )

    # Post URL
    if post_url and post_url != "N/A" and post_url.startswith("http"):
        metadata_items.append(
            html.Div(
                [
                    html.Strong(
                        "Link: ", style={"color": "#495057", "font-size": "0.8rem"}
                    ),
                    html.A(
                        "View Original Post",
                        href=post_url,
                        target="_blank",
                        style={"font-size": "0.8rem", "color": "#007bff"},
                    ),
                ],
                style={"margin-bottom": "0.5rem"},
            )
        )

    return html.Div(metadata_items)
