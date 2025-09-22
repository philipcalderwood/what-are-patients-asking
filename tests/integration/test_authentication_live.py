import dash
import pytest
from .auth_utils import complete_authentication_workflow


@pytest.mark.integration
def test_001_auth(dash_br):
    """Test live deployment authentication and navigation using PyAutoGUI"""

    # Use the complete authentication workflow utility
    results = complete_authentication_workflow(
        dash_br=dash_br, target_url=live_app_server["url"], verbose=True
    )

    # The workflow handles all authentication and verification
    # Additional assertions can be added here if needed
    assert results["success"], (
        f"Authentication workflow failed: {results.get('error', 'Unknown error')}"
    )

    # Optional: Add specific assertions based on results
    nav_count = results["elements_found"].get("nav_links", 0)
    assert nav_count >= 6, f"Expected at least 6 navigation elements, found {nav_count}"

    print(f" Test completed successfully - {nav_count} navigation elements verified")
