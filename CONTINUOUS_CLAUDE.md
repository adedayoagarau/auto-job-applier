# Continuous Claude Setup

This project is configured to use [Continuous Claude](https://github.com/AnandChowdhary/continuous-claude) for autonomous, iterative code improvements.

## What is Continuous Claude?

Continuous Claude orchestrates Claude Code in a continuous loop, autonomously:
- Creating feature branches
- Making incremental improvements
- Committing changes
- Creating pull requests
- Waiting for CI checks
- Merging when ready

Unlike one-shot AI coding assistance, Continuous Claude maintains persistent context across iterations, enabling it to tackle large, multi-step projects that would normally exhaust the context window.

## Installation

### Prerequisites

1. **Claude Code CLI** - Already available in this environment
2. **GitHub CLI** - Install on your local machine:
   ```bash
   # macOS
   brew install gh

   # Ubuntu/Debian
   sudo apt install gh

   # Other platforms: https://github.com/cli/cli#installation
   ```

3. **jq** - JSON parsing utility (usually pre-installed)
   ```bash
   # macOS
   brew install jq

   # Ubuntu/Debian
   sudo apt install jq
   ```

### Install Continuous Claude

On your local machine (not in this Claude Code session):

```bash
curl -fsSL https://raw.githubusercontent.com/AnandChowdhary/continuous-claude/main/install.sh | bash
```

### Authenticate GitHub CLI

```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

## Usage

### Quick Start

From your local machine, navigate to this project directory and run:

```bash
# General purpose improvement loop (5 iterations)
./scripts/continuous-improve.sh --max-runs 5

# Or run until $10 spent
./scripts/continuous-improve.sh --max-cost 10.00

# Run without creating commits/PRs (testing mode)
./scripts/continuous-improve.sh --max-runs 3 --disable-commits
```

### Specific Improvement Tasks

We've created helper scripts for common improvement tasks:

#### 1. Add Unit Tests (80%+ coverage goal)

```bash
./scripts/add-tests.sh
```

This runs up to 20 iterations to add comprehensive tests:
- Backend API endpoint tests (pytest)
- Database operation tests
- Job scraping logic tests
- Frontend component tests (Jest)

#### 2. Security Hardening

```bash
./scripts/security-hardening.sh
```

Runs 10 iterations focusing on:
- API authentication (JWT/API keys)
- Input validation
- File upload security
- Rate limiting
- XSS/injection prevention

#### 3. Code Quality Improvements

```bash
./scripts/code-quality.sh
```

Runs 15 iterations to improve:
- TypeScript type safety (remove `any`)
- Error handling
- Async/sync consistency
- Code documentation
- Linter compliance

### Advanced Usage

#### Run Multiple Tasks in Parallel

Use git worktrees to run multiple continuous loops simultaneously:

```bash
# Terminal 1: Add tests
./scripts/add-tests.sh --worktree tests-worker

# Terminal 2: Security improvements (different terminal)
./scripts/security-hardening.sh --worktree security-worker

# Terminal 3: Code quality (different terminal)
./scripts/code-quality.sh --worktree quality-worker
```

#### Custom Tasks

Run continuous-claude directly with custom prompts:

```bash
continuous-claude \
    --prompt "Add comprehensive logging throughout the application" \
    --max-runs 5 \
    --owner adedayoagarau \
    --repo auto-job-applier \
    --git-branch-prefix "feature/" \
    --merge-strategy squash
```

#### Cost-Limited Runs

Instead of limiting iterations, limit by cost:

```bash
continuous-claude \
    --prompt "Refactor the codebase for better maintainability" \
    --max-cost 25.00 \
    --owner adedayoagarau \
    --repo auto-job-applier
```

#### Overnight Runs

Set up a cron job or scheduled task to run improvements automatically:

```bash
# Run every night at 2 AM
0 2 * * * cd /path/to/auto-job-applier && ./scripts/continuous-improve.sh --max-cost 5.00
```

## How It Works

### Context Persistence

Continuous Claude uses `SHARED_TASK_NOTES.md` to maintain context across iterations:

1. **First iteration**: Claude reads the notes, works on the top priority task
2. **Updates notes**: Records what was done and what's next
3. **Next iteration**: New Claude instance reads updated notes, continues work
4. **Repeat**: Process continues until max runs/cost reached

This pattern prevents context window exhaustion and enables tackling large projects.

### Workflow

Each iteration follows this pattern:

```
Read SHARED_TASK_NOTES.md
  ↓
Work on next priority task
  ↓
Make incremental progress
  ↓
Update SHARED_TASK_NOTES.md
  ↓
Commit changes
  ↓
Create PR (if enabled)
  ↓
Wait for checks
  ↓
Merge (if checks pass)
  ↓
Next iteration...
```

### Branch Management

- Default prefix: `continuous-claude/`
- Each iteration creates a new branch
- PRs are automatically created
- Merges happen after CI checks pass

## Configuration

### Edit SHARED_TASK_NOTES.md

This file defines the priority queue for improvements. Edit it to:
- Add new tasks
- Reprioritize existing tasks
- Remove completed items
- Add context for specific areas

### Modify Scripts

Edit the scripts in `scripts/` to customize:
- Max runs/cost
- Branch prefixes
- Merge strategies
- Prompts and goals

## Best Practices

### 1. Start Small

Begin with a small number of iterations to verify the setup:

```bash
./scripts/continuous-improve.sh --max-runs 2
```

### 2. Monitor First Runs

Watch the first few iterations to ensure:
- PRs are created correctly
- CI checks pass
- Merges happen as expected
- Context is maintained in notes file

### 3. Review PRs

Even with autonomous merging, review the PRs to:
- Understand what changed
- Catch any issues
- Learn Claude's approach

### 4. Keep Notes Current

Regularly update `SHARED_TASK_NOTES.md`:
- Remove completed tasks
- Add new priorities
- Provide additional context
- Update architecture decisions

### 5. Use Cost Limits

For open-ended tasks, use `--max-cost` instead of `--max-runs`:

```bash
# Better for exploratory work
--max-cost 10.00

# vs fixed iterations
--max-runs 10
```

## Troubleshooting

### GitHub CLI Not Authenticated

```bash
gh auth status
# If not authenticated:
gh auth login
```

### Continuous Claude Not Found

Ensure it's in your PATH:

```bash
echo $PATH
ls ~/.local/bin/continuous-claude
```

Add to PATH if needed:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### PRs Not Being Created

Check GitHub CLI permissions:

```bash
gh auth refresh -s repo,workflow
```

### Context Not Persisting

Verify `SHARED_TASK_NOTES.md` is being updated:

```bash
git log --oneline SHARED_TASK_NOTES.md
```

## Examples

### Example 1: Fix All Linter Errors

```bash
continuous-claude \
    --prompt "Fix all ESLint and Pylint errors. Work on one file at a time." \
    --max-runs 10 \
    --owner adedayoagarau \
    --repo auto-job-applier
```

### Example 2: Add Feature with Tests

```bash
continuous-claude \
    --prompt "Add user authentication with email/password. Include unit tests for each component." \
    --max-cost 15.00 \
    --owner adedayoagarau \
    --repo auto-job-applier \
    --git-branch-prefix "feature/auth-"
```

### Example 3: Performance Optimization

```bash
continuous-claude \
    --prompt "Profile and optimize application performance. Focus on database queries, API response times, and frontend rendering." \
    --max-runs 8 \
    --owner adedayoagarau \
    --repo auto-job-applier
```

## Stopping a Run

To stop a continuous run:

1. Press `Ctrl+C` in the terminal
2. The current iteration will complete
3. No new iterations will start
4. Progress is saved in `SHARED_TASK_NOTES.md`

## Resources

- [Continuous Claude GitHub](https://github.com/AnandChowdhary/continuous-claude)
- [Claude Code Documentation](https://code.claude.com)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

## Current Configuration

**Repository**: adedayoagarau/auto-job-applier
**Branch Prefix**: continuous-claude/
**Merge Strategy**: squash
**Notes File**: SHARED_TASK_NOTES.md

## Next Steps

1. Install prerequisites on your local machine
2. Run a test with `--max-runs 2 --disable-commits`
3. Review the changes
4. Enable commits and run a full loop
5. Monitor the PRs and merges
6. Let it run overnight for larger improvements!
