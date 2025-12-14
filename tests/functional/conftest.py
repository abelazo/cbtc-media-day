import os
import pathlib
import subprocess

import boto3
import pytest


@pytest.fixture(scope="module")
def api_gateway_url():
    """
    Get the API Gateway URL from environment or Terraform output.
    """
    url = os.getenv("API_GATEWAY_URL")
    if not url:
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
            # But fixture usually yields.
            # We'll skip here for now.
            # Ideally we don't skip entire module if one test doesn't need it.
            pytest.skip("API Gateway not deployed. Run infrastructure deployment first.")

    # Convert to LocalStack format if needed
    if os.getenv("AWS_ENDPOINT_URL"):
        # Extract API ID and stage from URL if not already in localstack format
        if "execute-api" in url and "amazonaws.com" in url:
            parts = url.split("/")
            api_id = parts[2].split(".")[0]
            stage = parts[3]
            resource = parts[4]
            # Use LocalStack DNS format which provides better compatibility
            url = f"http://{api_id}.execute-api.localhost.localstack.cloud:4566/{stage}/{resource}"

    return url


@pytest.fixture(scope="module")
def users_table():
    """
    Get the users table name and ensure it's ready.
    """
    table_name = "users"
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint_url)

    try:
        table = dynamodb.Table(table_name)
        # Check if table exists (load metadata)
        table.load()
    except Exception:
        # Table might not exist
        pass

    return dynamodb.Table(table_name)


@pytest.fixture(scope="module")
def seeded_users(users_table):
    """
    Seed the users table with test data.
    """
    users = [
        {"username": "ValidUser", "dnis": ["12345678A", "87654321B"]},
        {"username": "TestUser", "dnis": ["11111111C"]},
    ]

    try:
        for user in users:
            users_table.put_item(Item=user)
    except Exception as e:
        print(f"Warning: Could not seed table: {e}")

    return users
