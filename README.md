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
- Terraform >= 1.31.1
- AWS CLI configured
- Docker and docker-compose (for LocalStack testing)

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


### Developer Default Workflow

The recommended workflow for local development using `just` and LocalStack:

```bash
# 1. Start LocalStack
just infra::start-localstack

# 2. Provision shared infrastructure (S3, etc.)
just infra::init global && just infra::apply global

# 3. Build and deploy service
just services::content::build

# 4. Provision lambda services
just infra::init services && just infra::apply services

# 5. Run functional tests
just tests::run

# 6. Manual Verification
# Replace <API_GW_ID> with the output from 'terraform output -raw api_gateway_id' in infra/services
curl -s http://<API_GW_ID>.execute-api.localhost.localstack.cloud:4566/v1/content
```

### Running Tests Locally

```bash
# Unit tests
just services::<service_name>::test

# Run with coverage
just services::<service_name>::test-coverage
```

### Code Quality

```bash
# Lint with ruff and black
just services::<service_name>::lint

# Terraform formatting
just infra::lint
```

## CI/CD Overview

Our GitHub Actions pipelines run on every PR:

1. **Test Pipeline**: Runs functional + unit tests
2. **Lint Pipeline**: Runs ruff, black --check, terraform fmt -check
3. **LocalStack Test Pipeline**: Deploys infrastructure to LocalStack and runs functional tests
4. **Terraform Plan**: Shows infrastructure changes on PR
5. **Deploy Pipeline**: Runs terraform apply on merge to main (with approval for prod)

## Contributing

1. Create a User Story in `/docs/user_stories/`
2. Write functional test in `/tests/functional/`
3. Write unit tests in service `/tests/`
4. Implement code to pass tests
5. Ensure all linters pass
6. Submit PR

## License

[License information to be added]
