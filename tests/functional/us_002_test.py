"""
Functional test for US-002: Basic Auth for Content Service.
"""

import base64
import os
import time

import boto3
import pytest
import requests


# TODO: Refactor to share with us001_test.py or move to conftest.py
@pytest.fixture(scope="module")
def api_gateway_url():
    """
    Get the API Gateway URL from environment or Terraform output.
    """
    url = os.getenv("API_GATEWAY_URL")
    if not url:
        import pathlib
        import subprocess

        current_dir = pathlib.Path(__file__).parent.absolute()
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

    if os.getenv("AWS_ENDPOINT_URL"):
        if "execute-api" in url and "amazonaws.com" in url:
            parts = url.split("/")
            api_id = parts[2].split(".")[0]
            stage = parts[3]
            resource = parts[4]
            url = f"http://localhost:4566/restapis/{api_id}/{stage}/_user_request_/{resource}"

    return url


@pytest.fixture(scope="module")
def users_table():
    """
    Get the users table name and ensure it's ready.
    """
    table_name = "users"  # Currently hardcoded, could be dynamic

    # Setup DynamoDB client
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint_url)

    try:
        table = dynamodb.Table(table_name)
        table.load()
    except Exception:
        # In a real scenario we might fail here, but for TDD we expect infra might not be up yet
        # However, the test should probably skip or fail gracefully if table doesn't exist
        pass

    return dynamodb.Table(table_name)


@pytest.fixture(scope="module")
def seeded_users(users_table):
    """
    Seed the users table with test data.
    """
    users = [
        {"username": "ValidUser", "password": "password123"},
        {"username": "AnotherUser", "password": "secret_password"},
    ]

    try:
        for user in users:
            users_table.put_item(Item=user)
    except Exception as e:
        print(f"Warning: Could not seed table (might not exist yet): {e}")

    return users


def get_basic_auth_header(username, password):
    """Create Basic Auth header value."""
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"


class TestUS002BasicAuth:
    """
    Functional test for US-002: Basic Authentication.
    """

    def test_user_receives_greeting_with_valid_credentials(self, api_gateway_url, seeded_users):
        """
        Scenario: User receives greeting with valid credentials
        """
        username = "ValidUser"
        password = "password123"
        headers = {"Authorization": get_basic_auth_header(username, password)}

        response = requests.get(api_gateway_url, headers=headers)

        assert response.status_code == 200
        assert response.json().get("success") is True

    def test_user_denied_access_with_invalid_credentials(self, api_gateway_url):
        """
        Scenario: User denied access with invalid credentials
        """
        username = "InvalidUser"
        password = "wrongpassword"
        headers = {"Authorization": get_basic_auth_header(username, password)}

        response = requests.get(api_gateway_url, headers=headers)

        assert response.status_code == 401

    def test_user_denied_access_without_credentials(self, api_gateway_url):
        """
        Scenario: User denied access without credentials
        """
        response = requests.get(api_gateway_url)

        assert response.status_code == 401
