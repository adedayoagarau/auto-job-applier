#!/bin/bash

# Run continuous Claude to add unit tests to the codebase
# Goal: Increase test coverage from 0% to 80%+

set -e

OWNER="adedayoagarau"
REPO="auto-job-applier"

PROMPT="Add comprehensive unit tests to the codebase. Focus on:
1. Backend API endpoints (test all routes in web_app.py)
2. Database operations (application_tracker.py)
3. Job scraping logic (job_scraper.py)
4. Frontend components (React components)

Use pytest for backend, Jest/React Testing Library for frontend.
Aim for 80%+ code coverage. Work incrementally - add tests for one module per iteration.
Update SHARED_TASK_NOTES.md with progress after each iteration."

continuous-claude \
    --prompt "$PROMPT" \
    --max-runs 20 \
    --owner "$OWNER" \
    --repo "$REPO" \
    --git-branch-prefix "tests/" \
    --merge-strategy squash
