from dash import register_page
from components.tag_summary_page import create_tag_summary_page

# Register this page with Dash Pages
register_page(__name__, path="/tag-summary", name="Tag Summary")


def layout():
    """Tag Summary page layout"""
    return create_tag_summary_page()
