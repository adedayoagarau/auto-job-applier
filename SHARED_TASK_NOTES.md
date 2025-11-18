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
✅ **NEW: Comprehensive security and quality improvements** (Nov 18, 2025)
   - JWT authentication system with protected endpoints
   - Input validation on all API endpoints
   - File upload security (type checking, size limits, path traversal prevention)
   - Async/sync mismatch fixes (database operations in thread pool)
   - Comprehensive error handling and resource cleanup
   - Alembic database migration system
   - Unit test suite (21 tests, 95% passing)
   - Default admin user: admin@autojobapplier.com / Admin123!

## Priority Tasks (In Order)

### ✅ Completed Tasks

1. ✅ **API Authentication** - JWT-based auth with protected endpoints
2. ✅ **Input Validation** - Pydantic validators on all request models
3. ✅ **Error Handling** - Comprehensive try-catch blocks with cleanup
4. ✅ **Async/Sync Fixes** - Database operations in thread pool
5. ✅ **Database Migrations** - Alembic setup with initial migration
6. ✅ **Testing** - 21 unit/integration tests (auth, API endpoints)

### High Priority - Remaining

7. **Rate Limiting**
   - Prevent API abuse on sensitive endpoints
   - Protect against DoS attacks
   - Use slowapi or FastAPI-limiter
   - Add per-user and per-IP rate limits

8. **Environment Variables & Secrets Management**
   - Move JWT secret key to environment variable
   - Validate required environment variables on startup
   - Create .env.example file
   - Document configuration requirements

9. **User Database Migration**
   - Move users from in-memory store to database
   - Create User model with SQLAlchemy
   - Add user management endpoints
   - Tie applications to specific users

### Medium Priority - User Experience

10. **Frontend Authentication Integration**
    - Add login/register pages
    - Store JWT token in localStorage/cookies
    - Add authentication context provider
    - Implement automatic token refresh
    - Add logout functionality

11. **Loading States**
    - Show loading spinners during API calls
    - Better user feedback during job searches
    - Skeleton loaders for applications list
    - Progress indicators for long operations

12. **TypeScript Improvements**
    - Replace `any` types with proper interfaces
    - Create types for API responses (using backend Pydantic models)
    - Generate TypeScript types from OpenAPI schema
    - Better type safety throughout frontend

13. **Retry Logic**
    - Implement retry for failed API requests
    - Exponential backoff for rate-limited requests
    - Better resilience for network issues
    - User-friendly error messages

### Lower Priority - Polish

14. **Expand Test Coverage**
    - Job scraping tests
    - Form filling tests
    - Resume parsing tests
    - Background task tests
    - Frontend component tests (Jest/React Testing Library)
    - Aim for 80%+ code coverage

15. **Documentation**
    - API documentation (OpenAPI/Swagger)
    - User guide for setting up and using the app
    - Developer guide for contributing
    - Architecture documentation

## Known Issues

### ✅ Fixed

- ~~File upload endpoint vulnerable to path traversal~~ → Fixed with path validation
- ~~No size limits on resume uploads~~ → Fixed (10MB limit)
- ~~Database sessions not using context managers properly~~ → Fixed with cleanup blocks
- ~~No authentication on API endpoints~~ → Fixed with JWT authentication

### Remaining

- Web scraping selectors are hardcoded (brittle) - should use more robust selectors
- No environment variable validation on startup - need to check required config
- JWT secret key hardcoded in code - should be in environment variable
- Users stored in memory - need database persistence
- No rate limiting - API vulnerable to abuse
- Pydantic v1 validators deprecated - should migrate to v2 @field_validator

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

**Start with**: Rate limiting (item #7) - prevent API abuse
**Then**: Environment variables (item #8) - move secrets out of code
**Or**: User database migration (item #9) - persist users in database

**Focus**: Finish security hardening, then improve UX

**Testing**: After each change, verify:
1. Run tests: `pytest` (should have 95%+ passing)
2. Backend runs without errors: `source venv/bin/activate && python web_app.py`
3. Frontend builds successfully: `cd frontend && npm run dev`
4. Test at http://localhost:3000
5. Login with: admin@autojobapplier.com / Admin123!

**Running the app**:
```bash
# Backend
source venv/bin/activate
python web_app.py

# Frontend (in separate terminal)
cd frontend
npm run dev

# Run tests
pytest

# Run migrations
alembic upgrade head
```

## Resources

- Backend entry point: `web_app.py`
- Frontend main page: `frontend/app/page.tsx`
- Database models: `src/application_tracker.py`
- Job scraping: `src/job_scraper.py`
- Configuration: `config.py`
