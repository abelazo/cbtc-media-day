# Example Service

A simple example Lambda service demonstrating the project structure.

## Functionality

This service provides a simple greeting API endpoint that:
- Accepts a `name` query parameter
- Returns a personalized greeting message
- Handles errors gracefully

## API

**Endpoint**: GET /hello

**Query Parameters**:
- `name` (optional): Name to greet (defaults to "World")

**Response**:
```json
{
  "message": "Hello, {name}!",
  "success": true
}
```

## Testing

```bash
# Run unit tests
pytest services/content_service/tests/

# Run with coverage
pytest services/content_service/tests/ --cov=services/content_service/src
```

## Deployment

This service is deployed as an AWS Lambda function via Terraform in `/infra/services/`.
