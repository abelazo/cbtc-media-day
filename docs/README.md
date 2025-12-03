# Documentation

This directory contains all project documentation for the CBTC Media Day application.

## Structure

### `/user_stories/`
Contains User Story definitions that drive development. Each story includes:
- Title and description
- Acceptance criteria
- Impact and rationale

**Naming convention**: `<user_story_id>.md` (e.g., `US001.md`)

### `/architecture/`
Architecture documentation including:
- System architecture diagrams
- Component interactions
- Data flow diagrams
- API documentation
- Deployment architecture

### `/adr/`
Architectural Decision Records (ADRs) documenting important technical decisions.

**Naming convention**: `<number>-<title>.md` (e.g., `001-use-dynamodb-for-state.md`)

## User Story Template

When creating a new User Story, use this template:

```markdown
# US-XXX: [Title]

**Status**: Draft | In Progress | Completed

## Description
[Context and user need for this feature]

## Acceptance Criteria
1. [Criterion 1 - must match functional test]
2. [Criterion 2 - must match functional test]
3. [Criterion 3 - must match functional test]

## Impact / Rationale
[Why this feature matters and its expected impact]

## Technical Notes
[Optional: Implementation considerations]

## Related Stories
[Optional: Links to related user stories]
```

## ADR Template

When creating an ADR, use this template:

```markdown
# [Number]. [Title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated | Superseded

## Context
[What is the issue that we're seeing that is motivating this decision?]

## Decision
[What is the change that we're proposing and/or doing?]

## Consequences
[What becomes easier or more difficult to do because of this change?]
```
