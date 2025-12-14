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


def get_dni_auth_header(dni, username):
    """Create DNI:Name auth header value."""
    credentials = f"{dni}:{username}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return encoded_credentials


class TestUS002BasicAuth:
    """
    Functional test for US-002: DNI Authentication.
    """

    def test_user_receives_greeting_with_valid_credentials(self, api_gateway_url, seeded_users):
        """
        Scenario: User receives greeting with valid DNI credentials
        """
        dni = "12345678A"
        username = "ValidUser"
        headers = {"Authorization": get_dni_auth_header(dni, username)}

        response = requests.get(api_gateway_url, headers=headers)

        assert response.status_code == 200
        assert response.json().get("success") is True

    @pytest.mark.skip("Not supported by LocalStack Community")
    def test_user_denied_access_with_invalid_credentials(self, api_gateway_url):
        """
        Scenario: User denied access with invalid DNI credentials
        """
        dni = "99999999Z"  # Invalid DNI not in any user's dnis list
        username = "InvalidUser"  # User doesn't exist
        headers = {"Authorization": get_dni_auth_header(dni, username)}

        response = requests.get(api_gateway_url, headers=headers)

        assert response.status_code == 403  # API Gateway returns 403 for authorization failures

    @pytest.mark.skip("Not supported by LocalStack Community")
    def test_user_denied_access_without_credentials(self, api_gateway_url):
        """
        Scenario: User denied access without credentials
        """
        response = requests.get(api_gateway_url)

        assert response.status_code == 403  # API Gateway returns 403 for authorization failures
