"""
Configuration file for the MRPC Dashboard application.
Contains global settings and constants used across modules.
"""

# Global table column configuration
# This defines the display order for table columns across the application
TABLE_COLUMN_ORDER = [
    "original_title",
    "LLM_inferred_question",
    "llm_cluster_name",
    "forum",
    "date_posted",
    "username",
    "post_type",
    "cluster_label",
    "cluster",
    "id",
    "post_url",
]

# Common style patterns
PLACEHOLDER_TEXT_STYLE = {
    "text-align": "center",
    "color": "#666",
    "font-style": "italic",
    "margin-top": "3.125rem",  # 50px equivalent
}

METADATA_ITEM_STYLE = {
    "margin-bottom": "0.9375rem",  # 15px equivalent
    "padding": "0.5rem",  # 8px equivalent
    "background-color": "#fff",
    "border": "1px solid #e0e0e0",
    "border-radius": "0.1875rem",  # 3px equivalent
    "font-size": "0.75rem",  # 12px equivalent (reduced from 13px)
    "word-wrap": "break-word",
}

METADATA_LABEL_STYLE = {
    "display": "block",
    "margin-bottom": "0.3125rem",  # 5px equivalent
    "color": "#333",
    "font-size": "0.8125rem",  # 13px equivalent (reduced from 14px)
}

# ========== TABLE VIEW STYLES ==========
TABLE_CONTAINER_STYLE = {
    "min-height": "0",  # Allow shrinking
    "display": "flex",
    "flex-direction": "column",
    "margin-bottom": "0",  # Remove any bottom margin
    "justify-content": "space-between",
}

TABLE_READING_PANE_STYLE = {
    "flex": "1",  # Take 1/5 (20%) of the available space
    # "min-height": "150px",  # Minimum height to ensure usability
    "padding": "0.75rem",  # Slightly reduced padding for better text positioning
    "border": "1px solid #dee2e6",  # Match table border color
    "border-top": "none",  # Remove top border to blend with table
    "border-radius": "0 0 0.375rem 0.375rem",  # Only bottom corners rounded
    "background-color": "#f8f9fa",
    "overflow": "auto",  # Let textarea handle its own scrolling
    "box-sizing": "border-box",
    "font-size": "13px",  # Slightly larger text for readability
    "line-height": "1.5",
    "display": "flex",  # Use flex to control textarea positioning
    "flex-direction": "column",  # Stack children vertically
}

TABLE_VIEW_MAIN_CONTAINER_STYLE = {
    "flex": "2",  # Take remaining space in flex container
    "display": "flex",
    "flex-direction": "column",
    "box-sizing": "border-box",
    "height": "100%",  # Use 100% of parent instead of viewport calc
    "min-height": "0",  # Allow shrinking
    # "overflow": "hidden",  # Removed - allow natural scrolling
}

CONTAINER_BOOTSTRAP_STYLE = {
    "flex": "1",  # Take available space in flex parent
    "min-height": "0",  # Allow shrinking in flex layout
    "display": "flex !important",  # Higher specificity than Bootstrap
    "flex-direction": "column !important",  # Force column layout
    "box-sizing": "border-box !important",  # Force border-box sizing
    "margin": "20",  # Remove any margins
    "padding": "0",  # Remove any padding for seamless layout
    # "overflow": "scroll",  # Prevent outer scrolling
}

# ========== DATATABLE STYLES ==========
DATATABLE_CELL_STYLE = {}

# DATATABLE_DATA_STYLE = {
#     "minHeight": "44px",  # Slightly increased row height for better touch targets
#     "border": "none",  # Remove individual cell borders for cleaner look
#     "cursor": "pointer",
#     "backgroundColor": "#ffffff",
#     "transition": "all 0.2s ease",  # Smooth transitions for all properties
# }

# DATATABLE_HEADER_STYLE = {
#     "backgroundColor": "#f8f9fa",
#     "fontWeight": "600",  # Slightly bolder
#     "border": "none",  # Remove individual borders for cleaner look
#     "borderBottom": "2px solid #dee2e6",  # Strong bottom border to separate from data
#     "textAlign": "center",
#     "cursor": "pointer",
#     "fontSize": "10px",  # Reduced by 2px from 12px for better table density
#     "color": "#495057",
#     "height": "48px",  # Increased header height for better proportion
#     "padding": "12px 16px",  # Match cell padding
#     "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
#     "letterSpacing": "0.025em",  # Slight letter spacing for headers
#     "textTransform": "uppercase",  # Make headers uppercase for distinction
# }

# DATATABLE_TABLE_STYLE = {
#     # Fill the available container space and allow scrolling
#     "overflowY": "auto",
#     "overflowX": "auto",
#     "height": "100%",  # Use 100% instead of forcing with !important
#     "border": "1px solid #dee2e6",
#     "borderRadius": "0.375rem 0.375rem 0 0",  # Only top corners rounded to blend with reading pane
#     "box-sizing": "border-box",
#     "marginBottom": "0",  # Remove any margin
# }

# ========== TEXTAREA STYLES ==========
TEXTAREA_COMPONENT_STYLE = {
    "width": "100%",
    "height": "100%",
    "resize": "none",
    "border": "none",  # Remove border for seamless integration
    "padding": "0.5rem 0.75rem",  # Reduced top/bottom padding for tighter text placement
    "font-family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",  # Match table font
    "font-size": "14px",  # Increased for better readability
    "line-height": "1.6",  # Better line spacing for reading
    "background-color": "transparent",  # Let parent background show through
    "border-radius": "0",  # No border radius for seamless integration
    "overflow-y": "auto",
    "white-space": "pre-wrap",
    "word-wrap": "break-word",
    "box-sizing": "border-box",
    "color": "#2c3e50",  # Darker color for better readability
    "outline": "none",  # Remove focus outline
    "vertical-align": "top",  # Align text to top
}

TEXTAREA_WRAPPER_STYLE = {
    "height": "100%",
    "width": "100%",
    "box-sizing": "border-box",
    "display": "flex",  # Use flex for better positioning control
    "flex-direction": "column",  # Stack elements vertically
}

# ========== MAIN CONTENT AREA STYLES ==========
# TODO: Deprecate
MAIN_CONTENT_VIEW_STYLE = {
    # "flex": "1",
    # "min-height": "0",
    # "display": "flex",
    # "flex-direction": "column",
    # "align-items": "stretch",
}

CLICK_INFO_STYLE = {
    "flex": "0 0 180px",  # Fixed height, don't grow or shrink
    "margin": "0.5rem 1rem",
    "padding": "0.75rem",
    "border": "1px solid #dee2e6",
    "border-radius": "0.375rem",
    "background-color": "#f8f9fa",
    "overflow-y": "auto",
    "box-sizing": "border-box",
}

MAIN_CONTENT_AREA_CONTAINER_STYLE = {
    "flex": "1",
    "display": "flex",
    "flex-direction": "column",
    "box-sizing": "border-box",
    "height": "100%",  # Use 100% of parent instead of viewport calc
    "min-height": "0",
    # "overflow": "hidden",  # Removed - allow natural scrolling
}

# ========== METADATA SIDEBAR STYLES ==========
METADATA_SIDEBAR_INNER_STYLE = {
    "padding": "1rem",
    "background-color": "#f8f9fa",
    "border-radius": "0.375rem",
    # "height": "calc(100% - 3rem)",  # Removed - use natural height
    "overflow-y": "auto",
    "box-sizing": "border-box",
}

METADATA_SIDEBAR_CONTAINER_STYLE = {
    "width": "300px",  # Fixed width for consistency
    "flex": "0 0 300px",  # Don't grow or shrink
    "padding": "0.75rem",
    "background-color": "#ffffff",
    "border": "1px solid #dee2e6",
    "border-radius": "0.375rem",
    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
    "box-sizing": "border-box",
    "height": "100%",  # Use 100% of parent instead of viewport calc
    # "overflow": "hidden",  # Removed - allow natural scrolling
}

METADATA_TITLE_STYLE = {
    "margin": "0 0 1rem 0",
    "text-align": "center",
    "font-size": "16px",  # Reduced from 18px
    "font-weight": "600",
    "color": "#343a40",
    "padding-bottom": "0.5rem",
    "border-bottom": "2px solid #e9ecef",
}

REMOTE_STYLES = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
]

# Common styles
SIDEBAR_WIDTH = "16rem"
TRANSITION_STYLE = "all 0.3s ease-in-out"

# Toggle button style
TOGGLE_BUTTON_WIDTH = "2rem"
TOGGLE_BUTTON_STYLE = {
    "position": "absolute",
    "top": "10px",
    "right": "-30px",
    "background-color": "#007bff",
    "border": "none",
    "border-radius": "0 5px 5px 0",
    "color": "white",
    "font-size": "18px",
    "padding": "5px 10px",
    "cursor": "pointer",
    "z-index": 1001,
}

# Sidebar styling
SIDEBAR_BASE_STYLE = {
    "position": "fixed",
    "top": 0,
    "bottom": 0,
    "width": SIDEBAR_WIDTH,
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "transition": TRANSITION_STYLE,
    "z-index": 1000,
}

SIDEBAR_STYLE = {**SIDEBAR_BASE_STYLE, "left": 0}
SIDEBAR_STYLE_COLLAPSED = {**SIDEBAR_BASE_STYLE, "left": f"-{SIDEBAR_WIDTH}"}

# Content styling
CONTENT_STYLE = {
    "margin-left": SIDEBAR_WIDTH,
    "transition": TRANSITION_STYLE,
    "height": "100vh",  # Set viewport height for proper flex behavior
    "overflow": "auto",  # Let child components handle scrolling
}

CONTENT_STYLE_COLLAPSED = {
    "margin-left": "0",
    "transition": TRANSITION_STYLE,
    "height": "100vh",  # Set viewport height for proper flex behavior
    "overflow": "auto",  # Let child components handle scrolling
}
