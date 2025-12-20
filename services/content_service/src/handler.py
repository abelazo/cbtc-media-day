"""
Content Service Lambda Handler.

Implements US-004: Retrieve file based on DNI/Nombre authentication.
"""

import base64
import io
import json
import logging
import os
import zipfile
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _get_env_var(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise ValueError(f"Missing environment variable: {name}")
    return val


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for retrieving content.

    Expects 'Authorization' header with base64 encoded "DNI:Name".
    Returns a zip file containing the user's photos.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # CORS headers
    app_url = _get_env_var("CBTC_APP_URL")
    headers = {
        "Access-Control-Allow-Origin": app_url,
        "Content-Type": "application/json",
    }

    try:
        logger.error("Parsing Authorization header")
        auth_header = event.get("headers", {}).get("Authorization")
        if not auth_header:
            return {
                "statusCode": 401,
                "headers": headers,
                "body": json.dumps({"message": "Missing Authorization header", "success": False}),
            }

        try:
            logger.error("Decoding Authorization header")
            if auth_header.startswith("Basic "):
                encoded_auth = auth_header.split(" ")[1]
            else:
                encoded_auth = auth_header

            decoded_bytes = base64.b64decode(encoded_auth)
            decoded_auth = decoded_bytes.decode("utf-8")
            dni, name = decoded_auth.split(":", 1)
        except Exception:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"message": "Invalid Authorization header format", "success": False}),
            }

        table_name = _get_env_var("USERS_TABLE_NAME")
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        logger.error("Verifying user exists and contains photos")
        response = table.get_item(Key={"username": name})
        item = response.get("Item")

        if not item or "photos" not in item or not item["photos"]:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"message": "No photos associated to this player", "success": False}),
            }

        logger.error("Retrieving photos from S3")
        s3_keys = item["photos"]
        first_key = s3_keys[0]

        bucket_name = _get_env_var("CONTENT_BUCKET_NAME")
        s3_client = boto3.client("s3")

        logger.error("Creating ZIP file")
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Get the first photo from S3
            s3_response = s3_client.get_object(Bucket=bucket_name, Key=first_key)
            photo_content = s3_response["Body"].read()

            # Extract filename from S3 key (e.g., "TestUser/photo1.jpg" -> "photo1.jpg")
            filename = first_key.split("/")[-1]

            # Add photo to zip file
            zip_file.writestr(filename, photo_content)

        # Get zip file content
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()

        logger.error("Base64 encoding ZIP content")
        b64_content = base64.b64encode(zip_content).decode("utf-8")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": app_url,
                "Content-Type": "application/zip",
                "Content-Disposition": "attachment; filename=photos.zip",
            },
            "body": b64_content,
            "isBase64Encoded": True,
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": "Internal server error", "success": False, "error": str(e)}),
        }
