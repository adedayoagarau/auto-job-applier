# Shared Task Notes - Auto Job Applier

> This file maintains context across continuous Claude iterations. It helps coordinate work between automated improvements and manual changes.

## Current State

**Project**: Web-based Auto Job Applier
- **Backend**: FastAPI on port 8000 (Python 3.12)
- **Frontend**: Next.js 14 + React + TypeScript on port 3000
- **Database**: SQLite with SQLAlchemy ORM
- **UI**: shadcn/ui components with dark mode support
- **Automation**: Playwright for browser automation, Claude API for AI assistance

## Recent Completions

✅ Migrated from CLI to web-based application
✅ Implemented React + Next.js + shadcn/ui frontend
✅ Added dark mode toggle with theme support
✅ Fixed critical bugs:
   - Database schema consistency (applied_date → applied_at)
   - JobScraper method signature (platforms as List[str])
   - WebSocket memory leak prevention
   - CORS security hardening
✅ Set up development environment with proper dependencies

## Priority Tasks (In Order)

### High Priority - Core Functionality

1. **Add API Authentication**
   - Currently no authentication on API endpoints
   - Security risk for production use
   - Suggest JWT or API key authentication

2. **Input Validation**
   - Add validation for all API endpoints (job title, location, etc.)
   - Prevent injection attacks (command injection, XSS, SQL injection)
   - Use Pydantic models for request validation

3. **Error Handling Improvements**
   - Add try-catch blocks around API calls
   - Implement graceful degradation
   - Better error messages for users

4. **Fix Async/Sync Mismatches**
   - Some blocking calls in async functions (database, browser automation)
   - Should use async SQLAlchemy or run in thread pool
   - Prevents blocking the event loop

### Medium Priority - User Experience

5. **Add Loading States**
   - Show loading spinners during API calls
   - Better user feedback during job searches
   - Skeleton loaders for applications list

6. **Retry Logic**
   - Implement retry for failed API requests
   - Exponential backoff for rate-limited requests
   - Better resilience

7. **TypeScript Improvements**
   - Replace `any` types with proper interfaces
   - Create types for API responses
   - Better type safety

### Lower Priority - Infrastructure

8. **Database Migrations**
   - Set up Alembic for schema migrations
   - Makes it easier to update database structure
   - Important for production deployments

9. **Testing**
   - Add unit tests for backend (pytest)
   - Add integration tests for API endpoints
   - Frontend component tests (Jest/React Testing Library)

10. **Rate Limiting**
    - Prevent API abuse
    - Protect against DoS
    - Use slowapi or similar

## Known Issues

- File upload endpoint vulnerable to path traversal
- No size limits on resume uploads
- Database sessions not using context managers properly
- Web scraping selectors are hardcoded (brittle)
- No environment variable validation on startup

## Configuration Notes

- **API Key**: Set `ANTHROPIC_API_KEY` in `config.py`
- **Resume**: Place resume in `data/resumes/` directory
- **Database**: Located at `data/applications.db` (auto-created)

## Architecture Decisions

- Separated frontend (Next.js) and backend (FastAPI) for flexibility
- WebSocket for real-time updates (activity log, statistics)
- CSS variables for theming (shadcn/ui pattern)
- SQLite for simplicity (can migrate to PostgreSQL later)

## Next Iteration Guidance

**Start with**: API authentication (item #1) - critical security issue
**Then**: Input validation (item #2) - another security concern
**Focus**: Security and stability before new features

**Testing**: After each change, verify:
1. Backend runs without errors: `python web_app.py`
2. Frontend builds successfully: `cd frontend && npm run dev`
3. Test at http://localhost:3000

## Resources

- Backend entry point: `web_app.py`
- Frontend main page: `frontend/app/page.tsx`
- Database models: `src/application_tracker.py`
- Job scraping: `src/job_scraper.py`
- Configuration: `config.py`
