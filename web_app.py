"""
AutoJobApplier - Web Application
A web-based interface for the automated job application system.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    BackgroundTasks,
    UploadFile,
    File,
    Depends,
    status,
    Request,
)
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# Import our existing modules
from src.job_scraper import JobScraper
from src.cv_parser import CVParser
from src.form_filler import FormFiller
from src.ai_assistant import AIAssistant
from src.application_tracker import ApplicationTracker
from src.auth import (
    get_current_user,
    create_access_token,
    authenticate_user,
    create_user,
    UserLogin,
    UserCreate,
    Token,
    TokenData,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from src.user_service import user_service
import config

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="AutoJobApplier",
    description="Automated job application system with AI assistance",
    version="1.0.0"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS - restrict to localhost origins only for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global state
websocket_connections: List[WebSocket] = []
job_search_task = None
application_process_running = False


# Pydantic models for API
class JobSearchRequest(BaseModel):
    job_titles: List[str]
    locations: List[str]
    platforms: List[str]
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None

    @validator('job_titles')
    def validate_job_titles(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one job title is required')
        if len(v) > 10:
            raise ValueError('Maximum 10 job titles allowed')
        for title in v:
            if not title or len(title.strip()) == 0:
                raise ValueError('Job title cannot be empty')
            if len(title) > 200:
                raise ValueError('Job title too long (max 200 characters)')
        return v

    @validator('locations')
    def validate_locations(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one location is required')
        if len(v) > 10:
            raise ValueError('Maximum 10 locations allowed')
        for loc in v:
            if not loc or len(loc.strip()) == 0:
                raise ValueError('Location cannot be empty')
            if len(loc) > 200:
                raise ValueError('Location too long (max 200 characters)')
        return v

    @validator('platforms')
    def validate_platforms(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one platform is required')
        valid_platforms = ['indeed', 'linkedin', 'glassdoor', 'ziprecruiter']
        for platform in v:
            if platform.lower() not in valid_platforms:
                raise ValueError(f'Invalid platform: {platform}. Valid platforms: {", ".join(valid_platforms)}')
        return v


class ApplicationConfig(BaseModel):
    auto_submit: bool = False
    max_applications: int = 20
    application_delay: int = 30

    @validator('max_applications')
    def validate_max_applications(cls, v):
        if v < 1:
            raise ValueError('Max applications must be at least 1')
        if v > 100:
            raise ValueError('Max applications cannot exceed 100')
        return v

    @validator('application_delay')
    def validate_application_delay(cls, v):
        if v < 5:
            raise ValueError('Application delay must be at least 5 seconds')
        if v > 300:
            raise ValueError('Application delay cannot exceed 300 seconds')
        return v


class JobApplication(BaseModel):
    job_id: str
    manual_approve: bool = False


class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class PasswordChange(BaseModel):
    """Model for password change request"""
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(BaseModel):
    """Model for user response"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: str
    last_login: Optional[str]


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")


manager = ConnectionManager()


# Helper function to send updates via WebSocket
async def send_update(message_type: str, data: dict):
    """Send update to all connected WebSocket clients"""
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast(message)


# Helper function to get current user with full details
async def get_current_user_full(current_user: TokenData = Depends(get_current_user)):
    """Get current user with full details from database"""
    user = user_service.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


# Helper function to check if user is admin
async def require_admin(current_user: TokenData = Depends(get_current_user)):
    """Dependency that requires the current user to be an admin"""
    user = user_service.get_user_by_id(current_user.user_id)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Root endpoint - serve the main HTML page
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main web interface"""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>AutoJobApplier</title></head>
            <body>
                <h1>AutoJobApplier Web Interface</h1>
                <p>Static files not found. Please ensure the static directory exists.</p>
            </body>
        </html>
        """)


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "data": {"status": "connected"},
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({
                "type": "heartbeat",
                "data": {"status": "alive"},
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# API Endpoints - Authentication

@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")  # 5 registrations per hour per IP
async def register(request: Request, user: UserCreate):
    """Register a new user"""
    try:
        new_user = create_user(
            email=user.email,
            password=user.password,
            full_name=user.full_name
        )

        # Create access token
        access_token = create_access_token(
            data={"sub": new_user["email"], "user_id": new_user["id"]}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@app.post("/api/auth/login", response_model=Token)
@limiter.limit("10/minute")  # 10 login attempts per minute per IP
async def login(request: Request, user: UserLogin):
    """Login and get access token"""
    try:
        authenticated_user = authenticate_user(user.email, user.password)

        if not authenticated_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": authenticated_user["email"], "user_id": authenticated_user["id"]}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login"
        )


@app.get("/api/auth/me")
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """Get current user information"""
    return {
        "email": current_user.email,
        "user_id": current_user.user_id
    }


# API Endpoints - User Management

@app.get("/api/users/me", response_model=UserResponse)
async def get_my_profile(user = Depends(get_current_user_full)):
    """Get current user's full profile"""
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@app.get("/api/users", response_model=List[UserResponse])
@limiter.limit("30/minute")  # 30 requests per minute
async def list_users(
    request: Request,
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0,
    admin_user = Depends(require_admin)
):
    """List all users (admin only)"""
    try:
        users = user_service.list_users(active_only=active_only, limit=limit, offset=offset)

        return [
            UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at.isoformat() if user.created_at else None,
                last_login=user.last_login.isoformat() if user.last_login else None,
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}"
        )


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: TokenData = Depends(get_current_user)
):
    """Get user by ID (users can get their own info, admins can get any user)"""
    # Check if user is trying to access their own info or is admin
    requesting_user = user_service.get_user_by_id(current_user.user_id)

    if current_user.user_id != user_id and not requesting_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users' information"
        )

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """Update user information"""
    # Check if user is trying to update their own info or is admin
    requesting_user = user_service.get_user_by_id(current_user.user_id)

    if current_user.user_id != user_id and not requesting_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other users' information"
        )

    # Non-admin users cannot change admin status or active status
    if not requesting_user.is_admin:
        if user_update.is_admin is not None or user_update.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change admin or active status"
            )

    try:
        # Build update dict from non-None values
        update_data = {}
        if user_update.email is not None:
            update_data['email'] = user_update.email
        if user_update.full_name is not None:
            update_data['full_name'] = user_update.full_name
        if user_update.is_active is not None:
            update_data['is_active'] = user_update.is_active
        if user_update.is_admin is not None:
            update_data['is_admin'] = user_update.is_admin

        updated_user = user_service.update_user(user_id, **update_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            is_active=updated_user.is_active,
            is_admin=updated_user.is_admin,
            created_at=updated_user.created_at.isoformat() if updated_user.created_at else None,
            last_login=updated_user.last_login.isoformat() if updated_user.last_login else None,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )


@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user = Depends(require_admin)
):
    """Delete (deactivate) a user (admin only)"""
    # Prevent admin from deleting themselves
    if admin_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    try:
        success = user_service.delete_user(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "status": "success",
            "message": "User deactivated successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )


@app.post("/api/users/change-password")
async def change_password(
    password_change: PasswordChange,
    user = Depends(get_current_user_full)
):
    """Change current user's password"""
    from src.auth import verify_password

    # Verify current password
    if not verify_password(password_change.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Ensure new password is different
    if password_change.current_password == password_change.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    try:
        success = user_service.change_password(user.id, password_change.new_password)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )

        return {
            "status": "success",
            "message": "Password changed successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )


# API Endpoints - Protected

@app.get("/api/config")
async def get_config(current_user: TokenData = Depends(get_current_user)):
    """Get current configuration"""
    return {
        "job_titles": config.JOB_TITLES,
        "locations": config.LOCATIONS,
        "platforms": config.PLATFORMS,
        "keywords": config.KEYWORDS,
        "exclude_keywords": config.EXCLUDE_KEYWORDS,
        "max_applications_per_day": config.MAX_APPLICATIONS_PER_DAY,
        "auto_submit": config.AUTO_SUBMIT,
        "headless": config.HEADLESS,
        "personal_info": config.PERSONAL_INFO,
    }


@app.post("/api/config")
async def update_config(
    updates: dict,
    current_user: TokenData = Depends(get_current_user)
):
    """Update configuration (in-memory only)"""
    try:
        for key, value in updates.items():
            if hasattr(config, key.upper()):
                setattr(config, key.upper(), value)
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/statistics")
async def get_statistics(current_user: TokenData = Depends(get_current_user)):
    """Get application statistics for current user"""
    try:
        # Run in thread pool to avoid blocking event loop
        def _get_stats():
            tracker = ApplicationTracker()
            return tracker.get_statistics(user_id=current_user.user_id)

        stats = await asyncio.to_thread(_get_stats)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications")
async def get_applications(
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_current_user)
):
    """Get list of applications for current user"""
    try:
        # Run in thread pool to avoid blocking event loop
        def _get_applications():
            tracker = ApplicationTracker()
            # Get applications from database
            from src.application_tracker import Application
            from sqlalchemy import desc, or_

            session = tracker.Session()
            try:
                # Filter by user_id OR applications without user_id (legacy data)
                applications = session.query(Application)\
                    .filter(
                        or_(
                            Application.user_id == current_user.user_id,
                            Application.user_id == None  # Include legacy applications
                        )
                    )\
                    .order_by(desc(Application.applied_at))\
                    .limit(limit)\
                    .offset(offset)\
                    .all()

                result = []
                for app in applications:
                    result.append({
                        "id": app.id,
                        "job_title": app.job_title,
                        "company": app.company,
                        "location": app.location,
                        "platform": app.platform,
                        "job_url": app.job_url,
                        "status": app.status,
                        "match_score": app.match_score,
                        "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                        "response_received": app.response_received,
                    })

                return result
            finally:
                session.close()

        result = await asyncio.to_thread(_get_applications)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
@limiter.limit("20/hour")  # 20 job searches per hour per IP
async def search_jobs(
    request: Request,
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user)
):
    """Search for jobs without applying"""
    global job_search_task

    if job_search_task and not job_search_task.done():
        raise HTTPException(status_code=400, detail="Job search already in progress")

    background_tasks.add_task(
        run_job_search,
        search_request.job_titles,
        search_request.locations,
        search_request.platforms,
        search_request.keywords,
        search_request.exclude_keywords
    )

    return {"status": "started", "message": "Job search started in background"}


@app.post("/api/apply")
@limiter.limit("10/hour")  # 10 application processes per hour per IP
async def start_application_process(
    request: Request,
    application_config: ApplicationConfig,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user)
):
    """Start the automated application process"""
    global application_process_running

    if application_process_running:
        raise HTTPException(status_code=400, detail="Application process already running")

    background_tasks.add_task(
        run_application_process,
        application_config.auto_submit,
        application_config.max_applications,
        application_config.application_delay
    )

    return {"status": "started", "message": "Application process started"}


@app.post("/api/stop")
async def stop_process(current_user: TokenData = Depends(get_current_user)):
    """Stop the current process"""
    global application_process_running
    application_process_running = False

    await send_update("process_stopped", {"message": "Process stopped by user"})
    return {"status": "stopped", "message": "Process stopped"}


@app.post("/api/upload-resume")
@limiter.limit("10/hour")  # 10 file uploads per hour per IP
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user)
):
    """Upload a resume file"""
    try:
        # Security: Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Security: Validate filename (prevent path traversal)
        safe_filename = Path(file.filename).name  # Get just the filename without path
        if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename"
            )

        # Security: Limit file size to 10MB
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        content = await file.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 10MB"
            )

        # Save the file
        resume_dir = Path(__file__).parent / "data" / "resumes"
        resume_dir.mkdir(parents=True, exist_ok=True)

        # Use safe filename
        file_path = resume_dir / safe_filename

        # Ensure file path is within resume directory (additional security check)
        if not str(file_path.resolve()).startswith(str(resume_dir.resolve())):
            raise HTTPException(
                status_code=400,
                detail="Invalid file path"
            )

        with open(file_path, "wb") as f:
            f.write(content)

        # Update config
        config.RESUME_PATH = str(file_path)

        # Parse the resume
        parser = CVParser(str(file_path))
        cv_data = parser.parse()

        return {
            "status": "success",
            "message": "Resume uploaded successfully",
            "file_path": str(file_path),
            "cv_data": cv_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")


@app.get("/api/export")
async def export_applications(
    format: str = "csv",
    current_user: TokenData = Depends(get_current_user)
):
    """Export applications to CSV"""
    try:
        # Validate format
        if format.lower() != "csv":
            raise HTTPException(
                status_code=400,
                detail="Only CSV format is currently supported"
            )

        # Run in thread pool to avoid blocking event loop
        def _export():
            tracker = ApplicationTracker()
            export_path = Path(__file__).parent / "data" / "exports"
            export_path.mkdir(parents=True, exist_ok=True)

            filename = f"applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = export_path / filename

            tracker.export_to_csv(str(file_path))
            return file_path, filename

        file_path, filename = await asyncio.to_thread(_export)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/csv"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting applications: {str(e)}")


# Background tasks

async def run_job_search(
    job_titles: List[str],
    locations: List[str],
    platforms: List[str],
    keywords: Optional[List[str]] = None,
    exclude_keywords: Optional[List[str]] = None
):
    """Background task to search for jobs"""
    try:
        await send_update("search_started", {
            "job_titles": job_titles,
            "locations": locations,
            "platforms": platforms
        })

        scraper = JobScraper()
        tracker = ApplicationTracker()

        all_jobs = []

        with scraper:
            for title in job_titles:
                for location in locations:
                    await send_update("search_progress", {
                        "message": f"Searching for {title} in {location}..."
                    })

                    jobs = scraper.search_jobs(
                        job_title=title,
                        location=location,
                        platforms=platforms
                    )

                    # Filter jobs
                    for job in jobs:
                        # Check if already applied
                        if tracker.has_applied(job['job_url']):
                            continue

                        # Check keywords
                        if keywords:
                            if not any(kw.lower() in job['description'].lower() for kw in keywords):
                                continue

                        if exclude_keywords:
                            if any(kw.lower() in job['description'].lower() for kw in exclude_keywords):
                                continue

                        all_jobs.append(job)

                        await send_update("job_found", {
                            "job": job,
                            "total_found": len(all_jobs)
                        })

        await send_update("search_completed", {
            "total_jobs": len(all_jobs),
            "message": f"Found {len(all_jobs)} jobs"
        })

    except Exception as e:
        error_message = f"Error during job search: {str(e)}"
        print(error_message)
        await send_update("error", {
            "message": error_message
        })

    finally:
        # Cleanup resources
        if 'tracker' in locals() and tracker:
            try:
                tracker.session.close()
            except Exception as e:
                print(f"Error closing tracker session: {str(e)}")


async def run_application_process(
    auto_submit: bool,
    max_applications: int,
    application_delay: int
):
    """Background task to run the application process"""
    global application_process_running
    application_process_running = True

    try:
        await send_update("application_started", {
            "auto_submit": auto_submit,
            "max_applications": max_applications
        })

        # Initialize components
        tracker = ApplicationTracker()
        scraper = JobScraper()
        ai_assistant = AIAssistant(api_key=config.ANTHROPIC_API_KEY)
        # Note: FormFiller requires page object from scraper context

        # Parse CV
        cv_parser = CVParser(config.RESUME_PATH)
        cv_data = cv_parser.parse()

        applications_today = tracker.get_applications_today()

        if applications_today >= max_applications:
            await send_update("application_completed", {
                "message": f"Daily limit of {max_applications} applications reached"
            })
            application_process_running = False
            return

        # Search for jobs
        with scraper:
            for title in config.JOB_TITLES:
                if not application_process_running:
                    break

                for location in config.LOCATIONS:
                    if not application_process_running:
                        break

                    await send_update("search_progress", {
                        "message": f"Searching for {title} in {location}..."
                    })

                    jobs = scraper.search_jobs(
                        job_title=title,
                        location=location,
                        platforms=config.PLATFORMS
                    )

                    # Process each job
                    for job in jobs:
                        if not application_process_running:
                            break

                        if applications_today >= max_applications:
                            break

                        # Check if already applied
                        if tracker.has_applied(job['job_url']):
                            continue

                        await send_update("job_evaluation", {
                            "job": job,
                            "message": "Evaluating job match..."
                        })

                        # Use AI to evaluate job
                        should_apply, score, reasoning = ai_assistant.should_apply_to_job(
                            job_description=job['description'],
                            cv_data=cv_data
                        )

                        await send_update("job_evaluated", {
                            "job": job,
                            "score": score,
                            "reasoning": reasoning,
                            "should_apply": should_apply
                        })

                        if should_apply:
                            if auto_submit:
                                # Apply automatically
                                await send_update("applying", {
                                    "job": job,
                                    "message": "Applying to job..."
                                })

                                # Apply using form filler
                                success = form_filler.fill_application(
                                    job_url=job['job_url'],
                                    cv_data=cv_data,
                                    ai_assistant=ai_assistant
                                )

                                if success:
                                    tracker.add_application(
                                        job_title=job['title'],
                                        company=job['company'],
                                        location=job['location'],
                                        job_url=job['job_url'],
                                        platform=job['platform'],
                                        status='applied',
                                        match_score=score
                                    )
                                    applications_today += 1

                                    await send_update("application_success", {
                                        "job": job,
                                        "applications_today": applications_today
                                    })
                                else:
                                    await send_update("application_failed", {
                                        "job": job,
                                        "message": "Failed to apply"
                                    })

                                # Delay between applications
                                await asyncio.sleep(application_delay)
                            else:
                                # Manual approval needed
                                await send_update("approval_needed", {
                                    "job": job,
                                    "score": score,
                                    "reasoning": reasoning
                                })

        await send_update("application_completed", {
            "total_applications": applications_today,
            "message": f"Applied to {applications_today} jobs"
        })

    except Exception as e:
        error_message = f"Error during application process: {str(e)}"
        print(error_message)
        await send_update("error", {
            "message": error_message
        })
    finally:
        application_process_running = False
        # Cleanup resources
        if 'tracker' in locals() and tracker:
            try:
                tracker.session.close()
            except Exception as e:
                print(f"Error closing tracker session: {str(e)}")
        if 'scraper' in locals() and scraper:
            try:
                # Scraper cleanup happens in context manager, but just in case
                pass
            except Exception as e:
                print(f"Error cleaning up scraper: {str(e)}")


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "application_running": application_process_running
    }


# Main entry point
if __name__ == "__main__":
    print("Starting AutoJobApplier Web Server...")
    print("Access the application at: http://localhost:8000")

    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
