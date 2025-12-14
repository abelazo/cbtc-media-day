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
def auth_headers():
    """
    Create valid auth headers for testing.
    Uses DNI:Name format encoded in base64.
    """
    dni = "12345678A"
    name = "ValidUser"
    credentials = f"{dni}:{name}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": encoded}


class TestUS001HelloWorld:
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
