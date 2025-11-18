#!/bin/bash

# Run continuous Claude to improve code quality
# Focus on TypeScript types, error handling, and best practices

set -e

OWNER="adedayoagarau"
REPO="auto-job-applier"

PROMPT="Improve code quality and maintainability. Focus on:
1. Replace TypeScript 'any' types with proper interfaces
2. Add comprehensive error handling with try-catch blocks
3. Fix async/sync mismatches (use async SQLAlchemy or thread pools)
4. Add proper logging throughout the application
5. Refactor large functions into smaller, testable units
6. Add JSDoc/docstring comments for public APIs
7. Fix linter warnings and errors
8. Improve code organization and module structure

Work on one area per iteration.
Run linters and type checkers after each change.
Update SHARED_TASK_NOTES.md with improvements made."

continuous-claude \
    --prompt "$PROMPT" \
    --max-runs 15 \
    --owner "$OWNER" \
    --repo "$REPO" \
    --git-branch-prefix "quality/" \
    --merge-strategy squash
