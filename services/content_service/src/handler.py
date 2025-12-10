"""
Example Lambda Service

This is a template service demonstrating the structure for Lambda handlers.
"""

import base64
import json
import logging
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_auth(event: dict[str, Any]) -> bool:
    """
    Check for Basic Auth credentials.
    Returns True if valid, False otherwise.
    """
    headers = event.get("headers") or {}
    # Headers can be case-insensitive, try to normalize or check variants
    auth_header = headers.get("Authorization") or headers.get("authorization")

    if not auth_header:
        logger.info("No Authorization header found")
        return False

    try:
        # Expected format: "Basic <base64_encoded_credentials>"
        scheme, encoded_credentials = auth_header.split(" ", 1)
        if scheme.lower() != "basic":
            logger.info("Invalid auth scheme")
            return False

        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)

        # Check against DynamoDB
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("users")  # TODO: use environment variable for table name

        response = table.get_item(Key={"username": username})
        item = response.get("Item")

        if not item:
            logger.info(f"User {username} not found")
            return False

        if item.get("password") != password:
            logger.info(f"Invalid password for user {username}")
            return False

        logger.info(f"User {username} authenticated successfully")
        return True

    except Exception as e:
        logger.error(f"Error checking auth: {str(e)}")
        return False


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Example Lambda handler function.

    Args:
        event: Lambda event payload
        context: Lambda context object

    Returns:
        API Gateway response format
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # Authenticate
    if not check_auth(event):
        return {
            "statusCode": 401,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "WWW-Authenticate": 'Basic realm="User Visible Realm"',
            },
            "body": json.dumps({"message": "Unauthorized", "success": False}),
        }

    try:
        # Example business logic
        query_params = event.get("queryStringParameters") or {}
        name = query_params.get("name", "World")
        message = f"Hello, {name}!"

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"message": message, "success": True}),
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"message": "Internal server error", "success": False, "error": str(e)}
            ),
        }
