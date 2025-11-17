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
)
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our existing modules
from src.job_scraper import JobScraper
from src.cv_parser import CVParser
from src.form_filler import FormFiller
from src.ai_assistant import AIAssistant
from src.application_tracker import ApplicationTracker
import config

# Initialize FastAPI app
app = FastAPI(
    title="AutoJobApplier",
    description="Automated job application system with AI assistance",
    version="1.0.0"
)

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


class ApplicationConfig(BaseModel):
    auto_submit: bool = False
    max_applications: int = 20
    application_delay: int = 30


class JobApplication(BaseModel):
    job_id: str
    manual_approve: bool = False


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


# API Endpoints

@app.get("/api/config")
async def get_config():
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
async def update_config(updates: dict):
    """Update configuration (in-memory only)"""
    try:
        for key, value in updates.items():
            if hasattr(config, key.upper()):
                setattr(config, key.upper(), value)
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/statistics")
async def get_statistics():
    """Get application statistics"""
    try:
        tracker = ApplicationTracker()
        stats = tracker.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications")
async def get_applications(limit: int = 50, offset: int = 0):
    """Get list of applications"""
    try:
        tracker = ApplicationTracker()
        # Get applications from database
        from src.application_tracker import Application
        from sqlalchemy import desc

        session = tracker.Session()
        applications = session.query(Application)\
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

        session.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search_jobs(search_request: JobSearchRequest, background_tasks: BackgroundTasks):
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
async def start_application_process(
    application_config: ApplicationConfig,
    background_tasks: BackgroundTasks
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
async def stop_process():
    """Stop the current process"""
    global application_process_running
    application_process_running = False

    await send_update("process_stopped", {"message": "Process stopped by user"})
    return {"status": "stopped", "message": "Process stopped"}


@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume file"""
    try:
        # Save the file
        resume_dir = Path(__file__).parent / "data" / "resumes"
        resume_dir.mkdir(parents=True, exist_ok=True)

        file_path = resume_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export")
async def export_applications(format: str = "csv"):
    """Export applications to CSV"""
    try:
        tracker = ApplicationTracker()
        export_path = Path(__file__).parent / "data" / "exports"
        export_path.mkdir(parents=True, exist_ok=True)

        filename = f"applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = export_path / filename

        tracker.export_to_csv(str(file_path))

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        await send_update("error", {
            "message": f"Error during job search: {str(e)}"
        })


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
        await send_update("error", {
            "message": f"Error during application process: {str(e)}"
        })
    finally:
        application_process_running = False


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
