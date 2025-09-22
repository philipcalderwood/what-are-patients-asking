"""
Authentication utilities for integration testing

Provides reusable functions for handling browser authentication
in integration tests, particularly for PyAutoGUI-based authentication.
"""

import pyautogui
import dotenv
import os
import time
from typing import Optional, Tuple


def load_test_credentials() -> Tuple[str, str]:
    """
    Load test credentials from environment variables.

    Returns:
        Tuple[str, str]: (username, password)

    Raises:
        ValueError: If credentials are not found in environment
    """
    dotenv.load_dotenv()

    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Test credentials not found. Please set TEST_USERNAME and TEST_PASSWORD "
            "environment variables in your .env file."
        )

    return username, password


def authenticate_with_pyautogui(
    username: str,
    password: str,
    typing_interval: float = 0.01,
    auth_wait_time: float = 1.0,
    verbose: bool = True,
) -> None:
    """
    Handle browser authentication dialog using PyAutoGUI.

    This function types credentials into a browser authentication dialog
    and submits them. It's designed for HTTP Basic Auth dialogs.

    Args:
        username: Username to type
        password: Password to type
        typing_interval: Seconds between keystrokes (default: 0.01 for fast typing)
        auth_wait_time: Seconds to wait for auth dialog to appear (default: 1.0)
        verbose: Whether to print progress messages (default: True)

    Raises:
        Exception: If PyAutoGUI authentication fails
    """
    if verbose:
        print(f"Authenticating with PyAutoGUI (user: {username[:10]}...)")

    # Wait for auth dialog to appear
    time.sleep(auth_wait_time)

    try:
        # Type username
        pyautogui.typewrite(username, interval=typing_interval)
        pyautogui.press("tab")

        # Type password
        pyautogui.typewrite(password, interval=typing_interval)
        pyautogui.press("enter")

        if verbose:
            print("Authentication completed successfully")

    except Exception as e:
        if verbose:
            print(f"Authentication error: {e}")
        raise


def navigate_and_authenticate(
    dash_br,
    target_url: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    page_load_wait: float = 1.0,
    verbose: bool = True,
) -> None:
    """
    Navigate to a URL and handle authentication if required.

    This is a high-level function that combines navigation and authentication
    for integration tests.

    Args:
        dash_br: Dash browser fixture (from pytest-dash)
        target_url: URL to navigate to
        username: Username (if None, loads from environment)
        password: Password (if None, loads from environment)
        page_load_wait: Seconds to wait after authentication (default: 3.0)
        verbose: Whether to print progress messages (default: True)

    Raises:
        ValueError: If credentials cannot be loaded
        Exception: If authentication fails
    """
    if verbose:
        print(f"Navigating to: {target_url}")

    # Load credentials if not provided
    if username is None or password is None:
        username, password = load_test_credentials()

    if verbose:
        print(f"Using credentials for user: {username}")

    # Navigate to target URL
    dash_br.driver.get(target_url)

    # Handle authentication
    authenticate_with_pyautogui(username, password, verbose=verbose)

    # Wait for page to load after authentication
    if verbose:
        print(f"Waiting {page_load_wait}s for page load...")
    time.sleep(page_load_wait)


def verify_authentication_success(
    dash_br,
    expected_elements: Optional[list] = None,
    timeout: int = 30,
    verbose: bool = True,
) -> dict:
    """
    Verify that authentication was successful by checking for expected elements.

    Args:
        dash_br: Dash browser fixture
        expected_elements: List of CSS selectors to check for (default: standard elements)
        timeout: Timeout for element waiting (default: 30)
        verbose: Whether to print progress messages (default: True)

    Returns:
        dict: Results of verification including element counts and status (navbar, nav links, main content)

    Raises:
        Exception: If verification fails
    """
    if expected_elements is None:
        expected_elements = [
            ".navbar-brand",  # Main brand/title
            ".nav-link",  # Navigation links
            "#page-content",  # Main content area
        ]

    if verbose:
        print("Verifying authentication success...")

    results = {
        "success": False,
        "elements_found": {},
        "page_title": "",
        "current_url": "",
        "error": None,
    }

    try:
        # Check for main brand/title
        if ".navbar-brand" in expected_elements:
            dash_br.wait_for_text_to_equal(
                ".navbar-brand", "Data Explorer", timeout=timeout
            )
            brand_element = dash_br.find_element(".navbar-brand")
            assert "Data Explorer" in brand_element.text
            results["elements_found"]["navbar_brand"] = brand_element.text

        # Check for navigation elements
        if ".nav-link" in expected_elements:
            nav_elements = dash_br.find_elements(".nav-link")
            assert len(nav_elements) > 0, "No navigation links found"
            results["elements_found"]["nav_links"] = len(nav_elements)

        # Check for main content area
        if "#page-content" in expected_elements:
            main_content = dash_br.find_element("#page-content")
            assert main_content.is_displayed(), "Main content area not visible"
            results["elements_found"]["main_content"] = True

        # Collect page info
        results["page_title"] = dash_br.driver.title
        results["current_url"] = dash_br.driver.current_url
        results["success"] = True

        if verbose:
            nav_count = results["elements_found"].get("nav_links", 0)
            print(f" Authentication verified - Found {nav_count} navigation elements")

        return results

    except Exception as e:
        results["error"] = str(e)
        results["page_title"] = dash_br.driver.title
        results["current_url"] = dash_br.driver.current_url

        if verbose:
            print(
                f"❌ Authentication verification failed - Title: '{results['page_title']}', URL: {results['current_url']}"
            )

        raise


# Convenience function for complete authentication workflow
def complete_authentication_workflow(
    dash_br, target_url: str = "http://localhost:8055", verbose: bool = True
) -> dict:
    """
    Complete authentication workflow: navigate, authenticate, and verify.

    This is the highest-level convenience function that handles the entire
    authentication process for integration tests.

    Args:
        dash_br: Dash browser fixture
        target_url: URL to test (default: production deployment)
        verbose: Whether to print progress messages (default: True)

    Returns:
        dict: Results of the authentication workflow

    Raises:
        Exception: If any step of the workflow fails
    """
    if verbose:
        print("=== Starting Complete Authentication Workflow ===")

    # Step 1: Navigate and authenticate
    navigate_and_authenticate(dash_br, target_url, verbose=verbose)

    # Step 2: Verify success
    results = verify_authentication_success(dash_br, verbose=verbose)

    if verbose:
        print("=== Authentication Workflow Complete ===")

    return results
