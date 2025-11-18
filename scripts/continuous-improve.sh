#!/bin/bash

# Continuous improvement script for Auto Job Applier
# This runs Claude Code in a loop to continuously improve the codebase

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
OWNER="adedayoagarau"
REPO="auto-job-applier"
BRANCH_PREFIX="continuous-claude/"
MAX_RUNS=5
MERGE_STRATEGY="squash"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-runs)
            MAX_RUNS="$2"
            shift 2
            ;;
        --max-cost)
            MAX_COST="$2"
            shift 2
            ;;
        --disable-commits)
            DISABLE_COMMITS=true
            shift
            ;;
        --worktree)
            WORKTREE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--max-runs N] [--max-cost X] [--disable-commits] [--worktree NAME]"
            exit 1
            ;;
    esac
done

# Check if continuous-claude is installed
if ! command -v continuous-claude &> /dev/null; then
    echo -e "${RED}Error: continuous-claude not found${NC}"
    echo "Install it with:"
    echo "  curl -fsSL https://raw.githubusercontent.com/AnandChowdhary/continuous-claude/main/install.sh | bash"
    exit 1
fi

# Check if in git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Build command
CMD="continuous-claude"
CMD="$CMD --prompt \"Review SHARED_TASK_NOTES.md and work on the next priority task. Make meaningful progress on one item, then update the notes file with what was done and what's next.\""
CMD="$CMD --owner $OWNER --repo $REPO"
CMD="$CMD --git-branch-prefix $BRANCH_PREFIX"
CMD="$CMD --merge-strategy $MERGE_STRATEGY"

if [ -n "$MAX_RUNS" ] && [ "$MAX_RUNS" != "0" ]; then
    CMD="$CMD --max-runs $MAX_RUNS"
fi

if [ -n "$MAX_COST" ]; then
    CMD="$CMD --max-cost $MAX_COST"
fi

if [ "$DISABLE_COMMITS" = true ]; then
    CMD="$CMD --disable-commits"
fi

if [ -n "$WORKTREE" ]; then
    CMD="$CMD --worktree $WORKTREE"
fi

echo -e "${GREEN}Starting Continuous Claude...${NC}"
echo "Command: $CMD"
echo ""

eval $CMD
