# CBTC Media Day

A serverless AWS application built with Python 3.12 and Terraform, following Test-Driven Development (TDD) principles.

## Architecture

This is a **monorepo** containing all services, infrastructure, shared libraries, and documentation for the CBTC Media Day application.

### Directory Structure

```
/services/              # AWS Lambda services
    <service_name>/
        src/           # Service source code
        tests/         # Unit tests for this service
        requirements.txt
/infra/                # Terraform infrastructure as code
    global/            # Global resources (S3, DynamoDB, IAM)
    services/          # Service-specific infrastructure
/libs/                 # Shared code across services
    shared_code/
/docs/                 # Documentation
    user_stories/      # User Story definitions
    architecture/      # Architecture documentation
    adr/              # Architectural Decision Records
/tests/
    functional/        # End-to-end functional tests per User Story
/scripts/             # Utility scripts
/.github/workflows/   # CI/CD pipelines
```

## Development Methodology

We follow **Test-Driven Development (TDD)** organized around **User Stories**.

### Workflow for Each User Story

1. **Create Functional Test**: Write an end-to-end test simulating the User Story behavior
   - Location: `/tests/functional/<user_story_id>_test.py`

2. **Create Unit Tests**: Write unit tests for the service implementation
   - Location: `/services/<service>/tests/`

3. **Implement Code**: Write minimal code to satisfy functional + unit tests

4. **Refactor**: Keep tests green while improving code quality

### Example User Story Structure

Each User Story is documented in `/docs/user_stories/<user_story_id>.md` with:
- **Title**: Clear description of the feature
- **Description**: Context and user need
- **Acceptance Criteria**: Must match the functional test
- **Impact/Rationale**: Why this feature matters

## Technology Stack

- **Runtime**: Python 3.12 (AWS Lambda)
- **Infrastructure**: Terraform (IaC)
- **Package Manager**: uv (fast Python package installer)
- **Testing**: pytest
- **Linting**: ruff
- **Formatting**: black
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer
- Terraform >= 1.5
- AWS CLI configured

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync

# Install dev dependencies only
uv sync --only-dev

# Install all dependencies including extras
uv sync --all-extras
```

### Running Tests Locally

```bash
# Run all tests
uv run pytest

# Run functional tests only
uv run pytest tests/functional/

# Run unit tests for a specific service
uv run pytest services/<service_name>/tests/

# Run with coverage
uv run pytest --cov=services --cov=libs
```

### Code Quality

```bash
# Lint with ruff
uv run ruff check .

# Format with black
uv run black .

# Check formatting without modifying
uv run black --check .

# Terraform formatting
terraform fmt -check -recursive infra/
```

### Running Terraform

```bash
# Global infrastructure
cd infra/global
terraform init
terraform plan
terraform apply

# Service infrastructure
cd infra/services
terraform init
terraform plan
terraform apply
```

## CI/CD Overview

Our GitHub Actions pipelines run on every PR:

1. **Test Pipeline**: Runs functional + unit tests
2. **Lint Pipeline**: Runs ruff, black --check, terraform fmt -check
3. **Terraform Plan**: Shows infrastructure changes on PR
4. **Deploy Pipeline**: Runs terraform apply on merge to main (with approval for prod)

## Contributing

1. Create a User Story in `/docs/user_stories/`
2. Write functional test in `/tests/functional/`
3. Write unit tests in service `/tests/`
4. Implement code to pass tests
5. Ensure all linters pass
6. Submit PR

## License

[License information to be added]
