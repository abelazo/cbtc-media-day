# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CBTC Media Day is a serverless AWS application for managing and distributing media day photos. It's a monorepo containing Lambda services, data pipelines, Terraform infrastructure, and a React frontend.

## Build & Development Commands

All commands use `just` (a command runner). Run `just --list` to see all available recipes.

### Setup & Dependencies
```bash
just sync-all                     # Install all Python dependencies (uv workspaces)
# Backend
just sync authorizer              # Install authorizer dependencies
just sync content_service         # Install content_service dependencies
# Pipelines
just sync players_tutors          # Install players_tutors pipeline dependencies
# Frontend
just app::install                 # Install frontend dependencies (bun)
```

### Testing
```bash
# Backend Unit Tests
just services::test-all           # All backend services unit tests
just services::content::test      # Content service unit tests
just services::authorizer::test   # Authorizer unit tests
# Pipeline Unit Tests
just pipelines::test-all             # All pipeline tests
just pipelines::players-tutors::test # Players Tutors pipeline tests

# E2E tests (requires LocalStack running)
just e2e::run                     # All functional tests
just e2e::run-story us_004        # Single user story test
```

### Run
```bash
# Backend Unit Tests
just pipelines::players-tutors::run # Run players_tutors pipeline locally
```

### Code Quality
```bash
just services::lint-all           # Lint all services (ruff + black --check)
just services::format-all         # Auto-format services (black + ruff --fix)
just pipelines::lint-all          # Lint pipelines
just app::lint                    # Lint frontend (eslint)
```

### Building & Deployment
```bash
just services::build-all          # Build all Lambda packages
just infra::global::apply local   # Deploy global infra to LocalStack
just infra::services::apply local # Deploy services to LocalStack
```

### Local Development with LocalStack
```bash
just infra::localstack-start                           # Start LocalStack
just infra::bootstrap::init local && just infra::bootstrap::apply local
just infra::global::init local && just infra::global::apply local
just services::build-all
just infra::services::init local && just infra::services::apply local
just app::dev                                          # Start frontend dev server
```

## Architecture

### Directory Structure
- `services/` - Backend services based on AWS Lambda functions (authorizer, content_service)
- `pipelines/` - Data processing pipelines (players_tutors)
- `infra/` - Terraform IaC (bootstrap, global, services stacks)
- `app/` - React frontend (Vite + Bun)
- `tests/functional/` - E2E tests organized by user story
- `docs/user_stories/` - Feature specifications

### Key Services
- **authorizer**: API Gateway Lambda Authorizer - decodes base64 "DNI:Name" from Authorization header, validates against DynamoDB users table
- **content_service**: Photo retrieval service - fetches user photos from S3, returns as zip file

### Tech Stack
- Python 3.12 (Lambda and data pipelines) with uv workspaces
- React 19 + Vite + Bun (frontend)
- Terraform >= 1.31.1
- LocalStack for local AWS emulation
- pytest for testing

## Development Methodology

This project follows TDD organized around User Stories:
1. Create user story in `docs/user_stories/US-XXX.md`
2. Write functional test in `tests/functional/us_xxx_test.py`
3. Write unit tests in `services/<service>/tests/`
4. Implement code to pass tests

## Code Style

- Python: 120 char line length, ruff + black
- Tests named `*_test.py` or `test_*.py`
- Each service/pipeline is a separate uv workspace package with its own `pyproject.toml` and `justfile`

## AWS Resources

- **DynamoDB**: users table (username key, with dnis list and photos attributes)
- **S3**: Lambda source bucket, content (photos) bucket
- **API Gateway**: REST API with custom authorizer
