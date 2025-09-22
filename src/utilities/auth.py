from utilities.mrpc_database import MRPCDatabase
import base64


def authenticate_user(email, password):
    """
    Authenticate user credentials against the database

    Args:
        email (str): User's email address
        password (str): User's password

    Returns:
        dict or None: User information dict if authentication successful, None otherwise
    """
    db = MRPCDatabase()
    user_info = db.verify_user(email, password)

    if user_info:
        return user_info
    else:
        return None


def get_current_user():
    """
    Extract current user from Basic Auth headers in any callback/method

    Returns:
        dict or None: User information dict with id, first_name, last_name, email if authenticated
    """
    try:
        from flask import request

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Basic "):
            # Decode the base64 encoded credentials
            encoded_credentials = auth_header.split(" ")[1]
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded.split(":", 1)

            # Verify against our database
            return authenticate_user(username, password)
        return None
    except Exception as e:
        print(f"Error extracting current user: {e}")
        return None


def get_current_user_id():
    """
    Get current authenticated user's ID for database foreign keys

    Returns:
        int or None: User ID if authenticated, None otherwise
    """
    current_user = get_current_user()
    if current_user:
        return current_user["id"]
    return None


def is_admin(user_id: int = None) -> bool:
    """
    Check if the user is an admin (only Philip Calderwood - User ID 1)

    Args:
        user_id: User ID to check (default: current authenticated user)

    Returns:
        bool: True if user is admin, False otherwise
    """
    # Use provided user_id or get current authenticated user
    check_user_id = user_id if user_id is not None else get_current_user_id()

    # Only User ID 1 (Philip Calderwood) has admin privileges
    return check_user_id == 1


def require_admin():
    """
    Require admin privileges or raise exception

    Raises:
        Exception: If user is not authenticated or not admin

    Returns:
        dict: Admin user information
    """
    current_user = get_current_user()
    if not current_user:
        raise Exception("Authentication required for admin function")

    if not is_admin(current_user["id"]):
        raise Exception(
            f"Admin privileges required. User {current_user['first_name']} {current_user['last_name']} (ID: {current_user['id']}) is not authorized."
        )

    return current_user


def basic_auth_callback(username, password):
    """
    Primary authentication callback for Flask-BasicAuth middleware.

    This function serves as the authentication interface for the Dash application's
    BasicAuth system. It validates user credentials and returns user data on success.

    Args:
        username (str): User email address (treated as username for BasicAuth)
        password (str): User password

    Returns:
        dict: User data dictionary if authentication succeeds, None if it fails
    """
    # BasicAuth passes username/password - we treat username as email
    return authenticate_user(username, password)


def initialize_users():
    """
    Initialize the database with default users
    ⚠️ This should only be called ONCE during initial setup, not every app run!
    """
    db = MRPCDatabase()
    return db.initialize_default_users()


def get_all_users():
    """
    Get all users from the database
    """
    db = MRPCDatabase()
    return db.get_all_users()


def create_user(first_name, last_name, email, password):
    """
    Create a new user in the database
    """
    db = MRPCDatabase()
    return db.create_user(first_name, last_name, email, password)
