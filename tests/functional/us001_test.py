"""
Functional test for US-001 Example User Story.

This test simulates the end-to-end behavior described in the User Story.
"""

import json
import pytest
from services.example_service.src.handler import lambda_handler


class TestUS001ExampleUserStory:
    """
    Functional test for US-001: User can get a personalized greeting.
    
    Acceptance Criteria:
    1. User can call the API without parameters and receive a default greeting
    2. User can provide a name and receive a personalized greeting
    3. The API returns proper status codes and JSON responses
    """
    
    def test_user_receives_default_greeting(self):
        """
        AC1: User can call the API without parameters and receive a default greeting.
        """
        # Simulate API Gateway event
        event = {
            "httpMethod": "GET",
            "path": "/hello",
            "queryStringParameters": None
        }
        context = {}
        
        # Call handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["message"] == "Hello, World!"
    
    def test_user_receives_personalized_greeting(self):
        """
        AC2: User can provide a name and receive a personalized greeting.
        """
        # Simulate API Gateway event with name parameter
        event = {
            "httpMethod": "GET",
            "path": "/hello",
            "queryStringParameters": {
                "name": "TestUser"
            }
        }
        context = {}
        
        # Call handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["message"] == "Hello, TestUser!"
    
    def test_api_returns_proper_json_response(self):
        """
        AC3: The API returns proper status codes and JSON responses.
        """
        event = {
            "httpMethod": "GET",
            "path": "/hello",
            "queryStringParameters": {"name": "Alice"}
        }
        context = {}
        
        # Call handler
        response = lambda_handler(event, context)
        
        # Verify response structure
        assert "statusCode" in response
        assert "headers" in response
        assert "body" in response
        assert response["headers"]["Content-Type"] == "application/json"
        
        # Verify body is valid JSON
        body = json.loads(response["body"])
        assert "message" in body
        assert "success" in body
