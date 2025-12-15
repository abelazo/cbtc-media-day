"""
Functional test for US-004: User Can Retrieve Personal Photos.

This test makes actual HTTP requests to the deployed API Gateway endpoint.
"""

import base64
import json
import os
import uuid

import boto3
import pytest
import requests


# Helper to create valid auth headers
def create_auth_header(dni: str, name: str) -> dict:
    credentials = f"{dni}:{name}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


@pytest.fixture(scope="module")
def s3_client():
    """Boto3 S3 client."""
    endpoint = os.getenv("AWS_ENDPOINT_URL")
    return boto3.client("s3", endpoint_url=endpoint, region_name="eu-west-1")


@pytest.fixture(scope="module")
def dynamodb_client():
    """Boto3 DynamoDB client."""
    endpoint = os.getenv("AWS_ENDPOINT_URL")
    return boto3.client("dynamodb", endpoint_url=endpoint, region_name="eu-west-1")


@pytest.fixture(scope="module")
def setup_data(s3_client, dynamodb_client):
    """
    Sets up S3 file and DynamoDB entry for the test.
    Returns the test data used.
    """
    user_dni = "12345678A"
    user_name = "TestUser"
    unique_id = str(uuid.uuid4())
    s3_key = f"{user_name}/photo_{unique_id}.jpg"
    file_content = b"This is a test image content."
    username_key = f"{user_dni}:{user_name}"

    # Bucket and Table names should be available from environment or outputs
    # For now assuming standard naming or provided via env_vars/config
    # Ideally, these come from Terraform outputs or test config
    # We will assume 'content-bucket' and 'UsersTable' or similar are discoverable

    # Note: In a real e2e test, we often need to know the actual resource names.
    # We can try to discover them or expect them in env vars.
    # For this test, I will assume we can get them from env_vars fixture if it exists,
    # or I will list buckets/tables to find the right ones if possible,
    # but for simplicity let's rely on standard names or passed in config.

    # Since I don't see an env_vars fixture in US-001, I'll assume for now I might need
    # to hardcode or discover. Let's look at how US-001 does it.
    # US-001 doesn't invoke AWS services, so it doesn't need resource names.

    # Strategies:
    # 1. Use `terraform output` (but that runs outside python usually)
    # 2. Assume names based on project conventions (e.g. "cbtc-media-day-local-content")

    bucket_name = "cbtc-media-day-local-content"
    table_name = "users"

    # Upload file to S3
    s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=file_content)

    # Add entry to DynamoDB
    endpoint = os.getenv("AWS_ENDPOINT_URL")
    dynamodb_resource = boto3.resource("dynamodb", endpoint_url=endpoint, region_name="eu-west-1")
    table = dynamodb_resource.Table(table_name)
    table.put_item(Item={"username": username_key, "dnis": [s3_key]})

    yield {
        "dni": user_dni,
        "name": user_name,
        "s3_key": s3_key,
        "content": file_content,
        "bucket": bucket_name,
        "table": table_name,
        "username_key": username_key,
    }

    # Teardown
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        table.delete_item(Key={"username": username_key})
    except Exception:
        pass


class TestUS004RetrievePhotos:
    """
    Functional test for US-004.
    """

    def test_user_retrieves_associated_file(self, api_gateway_url, setup_data):
        """
        Scenario: User retrieves associated file
        """
        dni = setup_data["dni"]
        name = setup_data["name"]
        headers = create_auth_header(dni, name)

        response = requests.get(api_gateway_url, headers=headers)

        assert response.status_code == 200
        # Response might be base64 encoded string (bytes)
        # We need to decode it to compare with original content
        try:
            # Check if response is base64
            retrieved_content = base64.b64decode(response.content)
        except Exception:
            # If not base64, use as is
            retrieved_content = response.content

        assert retrieved_content == setup_data["content"]
        # Optionally check Content-Type if we set it

    def test_no_photos_associated(self, api_gateway_url):
        """
        Scenario: No photos associated
        """
        dni = "87654321B"
        name = "NoPhotoUser"
        headers = create_auth_header(dni, name)

        response = requests.get(api_gateway_url, headers=headers)

        assert response.status_code == 404
        assert "No hay fotos asociadas a este jugador" in response.text
