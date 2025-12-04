"""
Functional test for US-001 Example User Story.

This test makes actual HTTP requests to the deployed API Gateway endpoint.
"""

import json
import os

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
        import subprocess

        try:
            result = subprocess.run(
                ["terraform", "output", "-raw", "api_gateway_url"],
                cwd="../infra/services",
                capture_output=True,
                text=True,
                check=True,
            )
            url = result.stdout.strip()
        except subprocess.CalledProcessError:
            pytest.skip("API Gateway not deployed. Run infrastructure deployment first.")

    # Convert AWS URL to LocalStack format if using LocalStack
    if os.getenv("AWS_ENDPOINT_URL"):
        # Extract API ID from URL
        # Format: https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/{resource}
        if "execute-api" in url and "amazonaws.com" in url:
            api_id = url.split("//")[1].split(".")[0]
            url = f"http://{api_id}.execute-api.localhost.localstack.cloud:4566/v1/content"

    return url


class TestUS001ExampleUserStory:
    """
    Functional test for US-001: User can get a personalized greeting.

    Acceptance Criteria:
    1. User can call the API without parameters and receive a default greeting
    2. User can provide a name and receive a personalized greeting
    3. The API returns proper status codes and JSON responses
    """

    def test_user_receives_default_greeting(self, api_gateway_url):
        """
        AC1: User can call the API without parameters and receive a default greeting.
        """
        # Make HTTP GET request to API Gateway
        response = requests.get(api_gateway_url)

        # Verify response
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "Hello, World!"

    def test_user_receives_personalized_greeting(self, api_gateway_url):
        """
        AC2: User can provide a name and receive a personalized greeting.
        """
        # Make HTTP GET request with query parameter
        response = requests.get(api_gateway_url, params={"name": "TestUser"})

        # Verify response
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "Hello, TestUser!"

    def test_api_returns_proper_json_response(self, api_gateway_url):
        """
        AC3: The API returns proper status codes and JSON responses.
        """
        # Make HTTP GET request with query parameter
        response = requests.get(api_gateway_url, params={"name": "Alice"})

        # Verify response structure
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"

        # Verify body is valid JSON
        body = response.json()
        assert "message" in body
        assert "success" in body
