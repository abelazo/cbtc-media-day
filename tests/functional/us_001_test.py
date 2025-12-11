"""
Functional test for US-001 Example User Story.

This test makes actual HTTP requests to the deployed API Gateway endpoint.
"""

import base64
import json
import os

import boto3
import pytest
import requests


# TODO: Review a better implementation (e.g. based on environment variables)
@pytest.fixture(scope="module")
def api_gateway_url():
    """
    Get the API Gateway URL from environment or Terraform output.

    Returns:
        str: The base URL for the API Gateway endpoint
    """
    # Check if URL is provided via environment variable
    url = os.getenv("API_GATEWAY_URL")

    if not url:
        # Try to get from Terraform output
        import pathlib
        import subprocess

        # Calculate correct path relative to this file
        current_dir = pathlib.Path(__file__).parent.absolute()
        # project root/tests/functional -> project root/infra/services
        infra_dir = current_dir.parent.parent / "infra" / "services"

        try:
            result = subprocess.run(
                ["terraform", "output", "-raw", "api_gateway_url"],
                cwd=str(infra_dir),
                capture_output=True,
                text=True,
                check=True,
            )
            url = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("API Gateway not deployed. Run infrastructure deployment first.")

    # Convert AWS URL to LocalStack format if using LocalStack
    if os.getenv("AWS_ENDPOINT_URL"):
        # Extract API ID and stage from URL
        # Format: https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/{resource}
        if "execute-api" in url and "amazonaws.com" in url:
            parts = url.split("/")
            api_id = parts[2].split(".")[0]  # Extract API ID from domain
            stage = parts[3]  # Extract stage (e.g., v1)
            resource = parts[4]  # Extract resource (e.g., content)
            # Use LocalStack internal format
            url = f"http://localhost:4566/restapis/{api_id}/{stage}/_user_request_/{resource}"

    return url


@pytest.fixture(scope="module")
def seeded_users():
    """
    Seed the users table with test data.
    """
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint_url)
    table = dynamodb.Table("users")

    users = [
        {"username": "ValidUser", "password": "password123"},
        {"username": "TestUser", "password": "testpass"},
    ]

    try:
        for user in users:
            table.put_item(Item=user)
    except Exception as e:
        print(f"Warning: Could not seed table: {e}")

    return users


@pytest.fixture(scope="module")
def auth_headers():
    """
    Create valid auth headers for testing.
    """
    username = "ValidUser"
    password = "password123"
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


class TestUS001ExampleUserStory:
    """
    Functional test for US-001: User can get a personalized greeting.

    Acceptance Criteria:
    1. User can call the API without parameters and receive a default greeting
    2. User can provide a name and receive a personalized greeting
    3. The API returns proper status codes and JSON responses
    """

    def test_user_receives_default_greeting(self, api_gateway_url, auth_headers, seeded_users):
        """
        AC1: User can call the API without parameters and receive a default greeting.
        """
        # Make HTTP GET request to API Gateway
        response = requests.get(api_gateway_url, headers=auth_headers)

        # Verify response
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "Hello, World!"

    def test_user_receives_personalized_greeting(self, api_gateway_url, auth_headers, seeded_users):
        """
        AC2: User can provide a name and receive a personalized greeting.
        """
        # Make HTTP GET request with query parameter
        response = requests.get(api_gateway_url, params={"name": "TestUser"}, headers=auth_headers)

        # Verify response
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "Hello, TestUser!"

    def test_api_returns_proper_json_response(self, api_gateway_url, auth_headers, seeded_users):
        """
        AC3: The API returns proper status codes and JSON responses.
        """
        # Make HTTP GET request with query parameter
        response = requests.get(api_gateway_url, params={"name": "Alice"}, headers=auth_headers)

        # Verify response structure
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"

        # Verify body is valid JSON
        body = response.json()
        assert "message" in body
        assert "success" in body
