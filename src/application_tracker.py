"""
Application Tracker module for tracking job applications in a database
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
import json

try:
    import config
except ImportError:
    logger.error("config.py not found.")
    raise

Base = declarative_base()


class Application(Base):
    """Application model for database"""
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Nullable for backward compatibility
    job_url = Column(String, unique=True, nullable=False)
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    platform = Column(String)
    
    # Application details
    applied_at = Column(DateTime, default=datetime.now)
    status = Column(String, default='pending')  # pending, submitted, rejected, interview, offer
    
    # Job details
    job_description = Column(Text)
    salary = Column(String)
    match_score = Column(Float)
    
    # Application process
    submitted = Column(Boolean, default=False)
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    
    # Additional info
    notes = Column(Text)
    cover_letter = Column(Text)
    application_data = Column(Text)  # JSON string with form data
    
    # Tracking
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ApplicationTracker:
    """
    Track job applications in SQLite database
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        logger.info(f"Application tracker initialized: {self.db_path}")
    
    def add_application(self, job: Dict, submitted: bool = False, 
                       match_score: float = 0) -> Application:
        """
        Add a new application to the database
        
        Args:
            job: Job dictionary with details
            submitted: Whether the application was submitted
            match_score: AI match score for the job
            
        Returns:
            Application object
        """
        try:
            # Check if already exists
            existing = self.session.query(Application).filter_by(
                job_url=job['url']
            ).first()
            
            if existing:
                logger.info(f"Application already exists: {job['title']}")
                return existing
            
            app = Application(
                job_url=job['url'],
                job_title=job.get('title', 'Unknown'),
                company=job.get('company', 'Unknown'),
                location=job.get('location', ''),
                platform=job.get('platform', ''),
                job_description=job.get('description', ''),
                salary=job.get('salary', ''),
                submitted=submitted,
                match_score=match_score,
                status='submitted' if submitted else 'pending'
            )
            
            self.session.add(app)
            self.session.commit()
            
            logger.info(f"Added application: {job['title']} at {job['company']}")
            return app
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding application: {e}")
            raise
    
    def update_application(self, job_url: str, **kwargs) -> bool:
        """
        Update an existing application
        
        Args:
            job_url: URL of the job
            **kwargs: Fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            app = self.session.query(Application).filter_by(job_url=job_url).first()
            
            if not app:
                logger.warning(f"Application not found: {job_url}")
                return False
            
            for key, value in kwargs.items():
                if hasattr(app, key):
                    setattr(app, key, value)
            
            app.updated_at = datetime.now()
            self.session.commit()
            
            logger.info(f"Updated application: {app.job_title}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating application: {e}")
            return False
    
    def get_application(self, job_url: str) -> Optional[Application]:
        """Get an application by job URL"""
        return self.session.query(Application).filter_by(job_url=job_url).first()
    
    def has_applied(self, job_url: str) -> bool:
        """Check if already applied to this job"""
        app = self.get_application(job_url)
        return app is not None
    
    def get_applications_today(self, user_id: Optional[int] = None) -> int:
        """Get count of applications submitted today for a specific user"""
        from sqlalchemy import or_

        today = datetime.now().date()
        query = self.session.query(Application).filter(
            Application.applied_at >= today
        )

        if user_id:
            query = query.filter(
                or_(
                    Application.user_id == user_id,
                    Application.user_id == None  # Include legacy applications
                )
            )

        return query.count()
    
    def get_all_applications(self, status: str = None, 
                           limit: int = None) -> List[Application]:
        """
        Get all applications, optionally filtered by status
        
        Args:
            status: Filter by status (pending, submitted, etc.)
            limit: Maximum number of results
            
        Returns:
            List of Application objects
        """
        query = self.session.query(Application)
        
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(Application.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_statistics(self, user_id: Optional[int] = None) -> Dict:
        """
        Get application statistics for a specific user

        Args:
            user_id: Optional user ID to filter by

        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import or_

        # Build base query with user filter
        base_query = self.session.query(Application)
        if user_id:
            base_query = base_query.filter(
                or_(
                    Application.user_id == user_id,
                    Application.user_id == None  # Include legacy applications
                )
            )

        total = base_query.count()
        submitted = base_query.filter_by(submitted=True).count()
        pending = base_query.filter_by(status='pending').count()
        interviews = base_query.filter_by(status='interview').count()
        offers = base_query.filter_by(status='offer').count()
        rejected = base_query.filter_by(status='rejected').count()

        # Today's applications
        today_count = self.get_applications_today(user_id=user_id)

        # Average match score
        avg_score = base_query.with_entities(
            Application.match_score
        ).filter(Application.match_score > 0).all()

        if avg_score:
            avg_match = sum(s[0] for s in avg_score) / len(avg_score)
        else:
            avg_match = 0

        success_rate = (submitted / total * 100) if total > 0 else 0

        return {
            'total_applications': total,
            'applications_today': today_count,
            'success_rate': round(success_rate, 2),
            'average_match_score': round(avg_match, 2),
            'submitted': submitted,
            'pending': pending,
            'interviews': interviews,
            'offers': offers,
            'rejected': rejected,
        }
    
    def export_to_csv(self, filename: str = 'applications.csv') -> str:
        """
        Export applications to CSV file
        
        Args:
            filename: Output filename
            
        Returns:
            Path to created file
        """
        import csv
        from pathlib import Path
        
        try:
            applications = self.get_all_applications()
            
            output_path = Path(filename)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Date', 'Job Title', 'Company', 'Location', 'Platform',
                    'Status', 'Submitted', 'Match Score', 'URL'
                ])
                
                # Data
                for app in applications:
                    writer.writerow([
                        app.applied_at.strftime('%Y-%m-%d') if app.applied_at else 'N/A',
                        app.job_title,
                        app.company,
                        app.location,
                        app.platform,
                        app.status,
                        'Yes' if app.submitted else 'No',
                        app.match_score or 'N/A',
                        app.job_url
                    ])
            
            logger.info(f"Exported {len(applications)} applications to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def cleanup_old_pending(self, days: int = 7):
        """
        Remove old pending applications that were never submitted
        
        Args:
            days: Remove pending applications older than this many days
        """
        from datetime import timedelta
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted = self.session.query(Application).filter(
                Application.status == 'pending',
                Application.submitted == False,
                Application.created_at < cutoff_date
            ).delete()
            
            self.session.commit()
            logger.info(f"Cleaned up {deleted} old pending applications")
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error cleaning up applications: {e}")
    
    def close(self):
        """Close database session"""
        self.session.close()
