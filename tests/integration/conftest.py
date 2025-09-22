"""
Integration test fixtures for MRPC

Provides fixtures for starting the live app server for integration testing.
"""

import pytest
import subprocess
import time
import requests
import os
from pathlib import Path


@pytest.fixture(scope="session")
def live_app_server():
    """
    Start the app.py server for integration testing.

    Runs the actual app.py file in a subprocess and waits for it to be ready.
    Cleans up the server process after all tests complete.

    Returns:
        dict: Server information including URL and process
    """
    # Configuration
    host = "127.0.0.1"
    port = 8060
    server_url = f"http://{host}:{port}"

    # Path to app.py
    app_path = Path(__file__).parent.parent.parent / "app.py"

    # Environment variables for the server
    env = os.environ.copy()
    env.update(
        {
            "DASH_HOST": host,
            "DASH_PORT": str(port),
            "DASH_DEBUG": "False",  # Disable debug mode for testing
        }
    )

    # Start the server process
    process = subprocess.Popen(
        ["python", str(app_path)],
        env=env,
        cwd=str(app_path.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combine stderr with stdout
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    # Wait for server to be ready
    max_wait = 30  # seconds
    wait_interval = 0.5

    print(f"Starting server on {server_url}...")

    for i in range(int(max_wait / wait_interval)):
        # Check if process is still running first
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(f"App server process died early. output: {stdout}")

        try:
            response = requests.get(server_url, timeout=2)
            # Accept both 200 (authenticated) and 401 (needs auth) as "server ready"
            if response.status_code in (200, 401):
                print(
                    f"✅ Server ready after {i * wait_interval:.1f}s (status: {response.status_code})"
                )
                break
        except (requests.ConnectionError, requests.Timeout):
            # Print some progress dots so we know it's trying
            if i % 4 == 0:  # Every 2 seconds
                print(f"⏳ Waiting for server... ({i * wait_interval:.1f}s)")
            pass

        time.sleep(wait_interval)
    else:
        # Timeout - get any remaining output and kill the process
        if process.poll() is None:
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
                output = stdout if stdout else "No output"
            except subprocess.TimeoutExpired:
                process.kill()
                output = "Process killed due to timeout"
        else:
            stdout, stderr = process.communicate()
            output = stdout if stdout else "No output"

        raise RuntimeError(
            f"Server did not start within {max_wait} seconds. Last output: {output}"
        )

    # Return server info
    server_info = {"url": server_url, "host": host, "port": port, "process": process}

    yield server_info

    # Cleanup: Stop the server process
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
