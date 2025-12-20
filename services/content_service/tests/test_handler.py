"""
Unit tests for content service handler.
"""

import base64
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from services.content_service.src.handler import lambda_handler


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "USERS_TABLE_NAME": "test-users",
            "CONTENT_BUCKET_NAME": "test-bucket",
            "CBTC_APP_URL": "https://test-app.com",
        },
    ):
        yield


class TestContentServiceHandler:
    """Unit tests for the Lambda handler."""

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_us004_retrieve_file_success(self, mock_boto_client, mock_boto_resource, mock_env_vars):
        """
        US-004: Retrieve file associated with DNI:Nombre.
        """
        # Mock Auth Header
        dni = "12345678A"
        name = "TestUser"
        credentials = f"{dni}:{name}"
        encoded_auth = base64.b64encode(credentials.encode()).decode()
        event = {"headers": {"Authorization": f"Basic {encoded_auth}"}}
        context = {}

        # Mock DynamoDB response
        mock_dynamo = MagicMock()
        mock_boto_resource.return_value = mock_dynamo
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        # Expect the handler to construct key as "DNI:Name"
        mock_table.get_item.return_value = {"Item": {"photos": ["TestUser/photo1.jpg", "TestUser/photo2.jpg"]}}

        # Mock S3 response
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        file_content = b"fake_image_content"
        mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: file_content)}

        response = lambda_handler(event, context)

        # Assertions
        assert response["statusCode"] == 200
        assert response["isBase64Encoded"] is True
        assert response["headers"]["Content-Type"] == "application/zip"
        assert response["headers"]["Content-Disposition"] == "attachment; filename=photos.zip"

        # Verify the response body is a valid base64-encoded zip file
        import io
        import zipfile

        zip_content = base64.b64decode(response["body"])
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            # Verify zip contains the expected file
            assert "photo1.jpg" in zip_file.namelist()
            # Verify the content matches
            assert zip_file.read("photo1.jpg") == file_content

        # Verify DynamoDB call with colon separator
        mock_table.get_item.assert_called_with(Key={"username": f"{name}"})

        # Verify S3 call
        mock_s3.get_object.assert_called_with(Bucket="test-bucket", Key="TestUser/photo1.jpg")

    @patch("boto3.resource")
    def test_us004_no_photos_found(self, mock_boto_resource, mock_env_vars):
        """
        US-004: Handle no photos found.
        """
        credentials = "87654321B:NoPhoto"
        encoded_auth = base64.b64encode(credentials.encode()).decode()
        event = {"headers": {"Authorization": f"Basic {encoded_auth}"}}
        context = {}

        mock_dynamo = MagicMock()
        mock_boto_resource.return_value = mock_dynamo
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        # Scenario 1: No item found
        mock_table.get_item.return_value = {}

        response = lambda_handler(event, context)

        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["message"] == "No photos associated to this player"

    @patch("boto3.resource")
    def test_us004_dynamodb_error(self, mock_boto_resource, mock_env_vars):
        """US-004: Handle DynamoDB error."""
        credentials = "Error:User"
        encoded_auth = base64.b64encode(credentials.encode()).decode()
        event = {"headers": {"Authorization": f"Basic {encoded_auth}"}}

        mock_dynamo = MagicMock()
        mock_boto_resource.return_value = mock_dynamo
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_table.get_item.side_effect = Exception("DynamoError")

        response = lambda_handler(event, {})

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "Internal server error" in body["message"]
