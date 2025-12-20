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

        # Mock DynamoDB response with multiple photos
        mock_dynamo = MagicMock()
        mock_boto_resource.return_value = mock_dynamo
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        # Expect the handler to construct key as "DNI:Name"
        mock_table.get_item.return_value = {
            "Item": {"photos": ["TestUser/photo1.jpg", "TestUser/photo2.jpg", "TestUser/photo3.jpg"]}
        }

        # Mock S3 response - return different content for each photo
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        # Setup exceptions mock to avoid 'catching classes that do not inherit from BaseException'
        mock_s3.exceptions = MagicMock()
        mock_s3.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})

        photo_contents = {
            "TestUser/photo1.jpg": b"fake_image_content_1",
            "TestUser/photo2.jpg": b"fake_image_content_2",
            "TestUser/photo3.jpg": b"fake_image_content_3",
        }

        def get_object_side_effect(Bucket, Key):
            return {"Body": MagicMock(read=lambda: photo_contents[Key])}

        mock_s3.get_object.side_effect = get_object_side_effect

        response = lambda_handler(event, context)

        # Assertions
        assert response["statusCode"] == 200
        assert response["isBase64Encoded"] is True
        assert response["headers"]["Content-Type"] == "application/zip"
        assert response["headers"]["Content-Disposition"] == "attachment; filename=cbtc-media-day-2025.zip"

        # Verify the response body is a valid base64-encoded zip file
        import io
        import zipfile

        zip_content = base64.b64decode(response["body"])
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            # Verify zip contains all expected files
            assert "photo1.jpg" in zip_file.namelist()
            assert "photo2.jpg" in zip_file.namelist()
            assert "photo3.jpg" in zip_file.namelist()

            # Verify the content matches for each photo
            assert zip_file.read("photo1.jpg") == photo_contents["TestUser/photo1.jpg"]
            assert zip_file.read("photo2.jpg") == photo_contents["TestUser/photo2.jpg"]
            assert zip_file.read("photo3.jpg") == photo_contents["TestUser/photo3.jpg"]

        # Verify DynamoDB call with colon separator
        mock_table.get_item.assert_called_with(Key={"username": f"{name}"})

        # Verify S3 calls for all photos
        assert mock_s3.get_object.call_count == 3

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

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_us004_partial_success_some_photos_missing(self, mock_boto_client, mock_boto_resource, mock_env_vars):
        """US-004: Handle partial success when some photos are missing from S3."""
        credentials = "12345678A:TestUser"
        encoded_auth = base64.b64encode(credentials.encode()).decode()
        event = {"headers": {"Authorization": f"Basic {encoded_auth}"}}
        context = {}

        # Mock DynamoDB with 3 photos
        mock_dynamo = MagicMock()
        mock_boto_resource.return_value = mock_dynamo
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            "Item": {"photos": ["TestUser/photo1.jpg", "TestUser/photo2.jpg", "TestUser/photo3.jpg"]}
        }

        # Mock S3 - photo2 is missing
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        # Setup exceptions mock to avoid 'catching classes that do not inherit from BaseException'
        mock_s3.exceptions = MagicMock()
        mock_s3.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})

        photo_contents = {
            "TestUser/photo1.jpg": b"content_1",
            "TestUser/photo3.jpg": b"content_3",
        }

        def get_object_side_effect(Bucket, Key):
            if Key not in photo_contents:
                # Simulate NoSuchKey exception
                raise mock_s3.exceptions.NoSuchKey("The specified key does not exist.")
            return {"Body": MagicMock(read=lambda: photo_contents[Key])}

        mock_s3.get_object.side_effect = get_object_side_effect

        response = lambda_handler(event, context)

        # Should return 200 with only the 2 available photos
        assert response["statusCode"] == 200

        # Verify zip contains only the 2 available photos
        import io
        import zipfile

        zip_content = base64.b64decode(response["body"])
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "photo1.jpg" in zip_file.namelist()
            assert "photo2.jpg" not in zip_file.namelist()  # Missing
            assert "photo3.jpg" in zip_file.namelist()
            assert zip_file.read("photo1.jpg") == photo_contents["TestUser/photo1.jpg"]
            assert zip_file.read("photo3.jpg") == photo_contents["TestUser/photo3.jpg"]

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_us004_all_photos_missing(self, mock_boto_client, mock_boto_resource, mock_env_vars):
        """US-004: Return 404 when all photos are missing from S3."""
        credentials = "12345678A:TestUser"
        encoded_auth = base64.b64encode(credentials.encode()).decode()
        event = {"headers": {"Authorization": f"Basic {encoded_auth}"}}
        context = {}

        # Mock DynamoDB with photos
        mock_dynamo = MagicMock()
        mock_boto_resource.return_value = mock_dynamo
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_table.get_item.return_value = {"Item": {"photos": ["TestUser/photo1.jpg", "TestUser/photo2.jpg"]}}

        # Mock S3 - all photos are missing
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.exceptions = MagicMock()
        mock_s3.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})
        mock_s3.get_object.side_effect = mock_s3.exceptions.NoSuchKey("The specified key does not exist.")

        response = lambda_handler(event, context)

        # Should return 404 since no photos were retrieved
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["message"] == "No photos associated to this player"

    @patch("boto3.resource")
    @patch("boto3.client")
    def test_us004_s3_error_handling(self, mock_boto_client, mock_boto_resource, mock_env_vars):
        """US-004: Handle S3 errors gracefully and continue processing."""
        credentials = "12345678A:TestUser"
        encoded_auth = base64.b64encode(credentials.encode()).decode()
        event = {"headers": {"Authorization": f"Basic {encoded_auth}"}}
        context = {}

        # Mock DynamoDB with 3 photos
        mock_dynamo = MagicMock()
        mock_boto_resource.return_value = mock_dynamo
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            "Item": {"photos": ["TestUser/photo1.jpg", "TestUser/photo2.jpg", "TestUser/photo3.jpg"]}
        }

        # Mock S3 - photo2 throws generic error
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        # Setup exceptions mock to avoid 'catching classes that do not inherit from BaseException'
        mock_s3.exceptions = MagicMock()
        mock_s3.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})

        call_count = [0]

        def get_object_side_effect(Bucket, Key):
            call_count[0] += 1
            if call_count[0] == 2:  # Second call (photo2)
                raise Exception("S3 Service Error")
            content = f"content_{call_count[0]}".encode()
            return {"Body": MagicMock(read=lambda: content)}

        mock_s3.get_object.side_effect = get_object_side_effect

        response = lambda_handler(event, context)

        # Should return 200 with the 2 successful photos
        assert response["statusCode"] == 200

        # Verify zip contains only the 2 successful photos
        import io
        import zipfile

        zip_content = base64.b64decode(response["body"])
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert len(zip_file.namelist()) == 2
            assert "photo1.jpg" in zip_file.namelist()
            assert "photo3.jpg" in zip_file.namelist()
