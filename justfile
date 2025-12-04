# Load environment variables from .env file
set dotenv-load

# Infrastructure
[group('infra')]
mod infra
# Lambda services
[group('services')]
mod services
# Functional tests
[group('tests')]
mod tests

# Default recipe - show available commands
help:
    @just --list

# Setup development environment
[group('setup')]
setup:
    @echo "Setting up development environment..."
    uv sync --all-extras
    @echo "✓ Development environment ready"

# Clean build artifacts and caches
[group('setup')]
clean:
    @echo "Cleaning build artifacts..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    @echo "✓ Cleanup complete"
