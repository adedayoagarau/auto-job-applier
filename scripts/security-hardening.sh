#!/bin/bash

# Run continuous Claude to improve security
# Focus on authentication, input validation, and other security concerns

set -e

OWNER="adedayoagarau"
REPO="auto-job-applier"

PROMPT="Improve security of the Auto Job Applier application. Focus on:
1. Add API authentication (JWT or API key based)
2. Implement input validation for all endpoints
3. Fix file upload vulnerabilities (path traversal, size limits)
4. Add rate limiting to prevent abuse
5. Sanitize user inputs to prevent XSS and injection attacks
6. Add CSRF protection
7. Implement secure session management

Work on one security improvement per iteration.
Test thoroughly after each change.
Update SHARED_TASK_NOTES.md with what was secured and what's next."

continuous-claude \
    --prompt "$PROMPT" \
    --max-runs 10 \
    --owner "$OWNER" \
    --repo "$REPO" \
    --git-branch-prefix "security/" \
    --merge-strategy squash
