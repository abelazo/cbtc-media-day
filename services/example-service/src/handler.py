"""
Example Lambda Service

This is a template service demonstrating the structure for Lambda handlers.
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Example Lambda handler function.
    
    Args:
        event: Lambda event payload
        context: Lambda context object
    
    Returns:
        API Gateway response format
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Example business logic
        name = event.get("queryStringParameters", {}).get("name", "World")
        message = f"Hello, {name}!"
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "message": message,
                "success": True
            })
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "message": "Internal server error",
                "success": False,
                "error": str(e)
            })
        }
