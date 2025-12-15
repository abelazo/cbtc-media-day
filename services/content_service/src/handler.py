"""
Content Service Lambda Handler.

Implements US-004: Retrieve file based on DNI/Nombre authentication.
"""

import base64
import json
import logging
import os
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
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    try:
        # 1. Parse Authorization Header
        auth_header = event.get("headers", {}).get("Authorization")
        if not auth_header:
            # If Authorization header is missing, we might return 401 or 400.
            # Given the requirements, we expect it to be there.
            # For now, let's treat it as a bad request or unauthorized.
            # But the requirements imply we just used the header.
            return {
                "statusCode": 401,
                "headers": headers,
                "body": json.dumps({"message": "Missing Authorization header", "success": False}),
            }

        try:
            decoded_bytes = base64.b64decode(auth_header)
            decoded_str = decoded_bytes.decode("utf-8")
            username = decoded_str
        except Exception:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"message": "Invalid Authorization header format", "success": False}),
            }

        # 2. Query DynamoDB
        table_name = _get_env_var("USERS_TABLE_NAME")
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        response = table.get_item(Key={"username": username})
        item = response.get("Item")

        if not item or "dnis" not in item or not item["dnis"]:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"message": "No hay fotos asociadas a este jugador", "success": False}),
            }

        # 3. Get S3 Object
        s3_keys = item["dnis"]
        first_key = s3_keys[0]

        bucket_name = _get_env_var("CONTENT_BUCKET_NAME")
        s3_client = boto3.client("s3")

        s3_response = s3_client.get_object(Bucket=bucket_name, Key=first_key)
        content = s3_response["Body"].read()

        # Return content
        # If strictly binary, we might need base64 encoding for API Gateway proxy integration.
        # But `requests` in python handles binary content if the response is raw?
        # API Gateway Text vs Binary behavior can be tricky.
        # For now, let's try returning raw body (string) if utf-8, or handle binary.
        # The test expects `response.content == setup_data["content"]` which is bytes.
        # If we return a string in "body", API Gateway might wrap it.
        # To return binary via API Gateway Proxy:
        # 1. body: base64_encoded_string
        # 2. isBase64Encoded: true

        # Let's be robust and use base64 output.
        # Except the unit test expects `response["body"] == "file_content"`.
        # I should probably update the unit test to expect base64 if I implement it here.
        # But let's first implement the logic.

        # Assuming the file is an image, it is binary.
        # So we MUST use base64 encoding.

        # Wait, I just wrote the unit test to expect "file_content".
        # I should update the unit test to handle this or keep it simple if I thought it was text.
        # But "photos" implies binary images.

        # I will update existing implementation to assume text for now to satisfy the EXACT unit test I just wrote,
        # OR (better) I update the unit test to match reality (binary).
        # Since I'm in implementation step, I can do what is right.

        # Refined Unit Test Strategy:
        # Since I already wrote the unit test and it failed because I hadn't implemented logic,
        # Now I am implementing logic.
        # If I change logic to return base64, I must update the unit test too.
        # But I should stick to one tool call for the file.
        # I will write the handler.py to return the body strictly as read from S3 (mocked as bytes).
        # If `content` is bytes, I cannot put it in `json.dumps` or direct string body without decoding.
        # So I really SHOULD use base64.

        b64_content = base64.b64encode(content).decode("utf-8")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "image/jpeg",  # Or determine from key/s3
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
