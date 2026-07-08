# GitHub Workflow

## Branching Strategy

- Main branch contains stable code.
- All work is done on feature branches.
- Branch names follow:

feature/[description]

fix/[description]

docs/[description]

Branches are deleted after merging.

---

## Commit Message Convention

Format:

[type]: description

Types:

- feat
- fix
- docs
- refactor
- chore

Example:

feat: add data validation

Reason:

Keeps Git history clear and supports automated changelog generation.

---

## Pull Request Review Process

Every Pull Request requires at least one approval before merging.

Review focuses on:

- Correctness
- Readability
- Data integrity
- Test coverage

Commit messages are also reviewed.

---

## GitHub Issues

Every feature starts with an Issue.

Each Issue contains:

- Title
- Description
- Label
- Assignee

Issues are closed automatically when the Pull Request is merged.