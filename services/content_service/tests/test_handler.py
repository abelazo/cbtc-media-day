"""
Unit tests for example service handler.
"""

import json
import pytest
from services.content_service.src.handler import lambda_handler


class TestLambdaHandler:
    """Unit tests for the Lambda handler."""
    
    def test_handler_returns_200_with_default_name(self):
        """Test handler returns 200 status code with default greeting."""
        event = {}
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        assert "Content-Type" in response["headers"]
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert "Hello, World!" in body["message"]
    
    def test_handler_returns_200_with_custom_name(self):
        """Test handler returns 200 status code with custom name."""
        event = {
            "queryStringParameters": {
                "name": "Alice"
            }
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert "Hello, Alice!" in body["message"]
    
    def test_handler_has_cors_headers(self):
        """Test handler includes CORS headers."""
        event = {}
        context = {}
        
        response = lambda_handler(event, context)
        
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    
    def test_handler_returns_json_content_type(self):
        """Test handler returns JSON content type."""
        event = {}
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response["headers"]["Content-Type"] == "application/json"
