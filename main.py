"""
AutoJobApplier - Main application entry point
"""

import argparse
import sys
from pathlib import Path
from loguru import logger
import time
from typing import List, Dict

# Setup logging
try:
    import config
    
    logger.remove()
    logger.add(
        sys.stderr,
        level=config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    logger.add(
        config.LOG_FILE,
        rotation=config.LOG_ROTATION,
        level=config.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )
except ImportError:
    logger.error("config.py not found. Copy config.example.py to config.py and configure it.")
    sys.exit(1)

from src.job_scraper import JobScraper
from src.cv_parser import CVParser
from src.ai_assistant import AIAssistant
from src.form_filler import FormFiller
from src.application_tracker import ApplicationTracker


class AutoJobApplier:
    """
    Main application class
    """
    
    def __init__(self):
        self.cv_parser = CVParser()
        self.ai_assistant = AIAssistant()
        self.tracker = ApplicationTracker()
        self.cv_data = None
        
    def run(self, search_only: bool = False, apply: bool = False, 
            manual_approve: bool = False):
        """
        Main application loop
        
        Args:
            search_only: Only search for jobs, don't apply
            apply: Apply to jobs
            manual_approve: Require manual approval before applying
        """
        logger.info("=== AutoJobApplier Started ===")
        
        # Parse CV
        logger.info("Parsing resume...")
        self.cv_data = self.cv_parser.parse()
        
        if not self.cv_data:
            logger.error("Failed to parse resume. Check your resume file.")
            return
        
        logger.info(f"Resume parsed successfully. Found {len(self.cv_data.get('skills', []))} skills.")
        
        # Check daily limit
        applications_today = self.tracker.get_applications_today()
        if applications_today >= config.MAX_APPLICATIONS_PER_DAY:
            logger.warning(f"Daily application limit reached ({applications_today}/{config.MAX_APPLICATIONS_PER_DAY})")
            return
        
        logger.info(f"Applications today: {applications_today}/{config.MAX_APPLICATIONS_PER_DAY}")
        
        # Search for jobs
        all_jobs = self._search_jobs()
        
        if not all_jobs:
            logger.info("No jobs found matching criteria")
            return
        
        logger.info(f"Found {len(all_jobs)} total jobs")
        
        # Filter out already applied
        new_jobs = [job for job in all_jobs if not self.tracker.has_applied(job['url'])]
        logger.info(f"{len(new_jobs)} jobs are new (not yet applied)")
        
        if search_only:
            self._display_jobs(new_jobs)
            return
        
        if not apply:
            logger.info("Use --apply flag to start applying to jobs")
            return
        
        # Apply to jobs
        self._apply_to_jobs(new_jobs, manual_approve)
        
        # Show statistics
        self._show_statistics()
        
        logger.info("=== AutoJobApplier Finished ===")
    
    def _search_jobs(self) -> List[Dict]:
        """Search for jobs across all configured platforms"""
        all_jobs = []
        
        with JobScraper() as scraper:
            for platform in config.PLATFORMS:
                for job_title in config.JOB_TITLES:
                    for location in config.LOCATIONS:
                        logger.info(f"Searching {platform}: {job_title} in {location}")
                        
                        try:
                            jobs = scraper.search_jobs(platform, job_title, location)
                            all_jobs.extend(jobs)
                            
                            # Rate limiting
                            time.sleep(config.APPLICATION_DELAY)
                            
                        except Exception as e:
                            logger.error(f"Error searching {platform}: {e}")
        
        # Remove duplicates based on URL
        unique_jobs = []
        seen_urls = set()
        
        for job in all_jobs:
            if job['url'] not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job['url'])
        
        return unique_jobs
    
    def _apply_to_jobs(self, jobs: List[Dict], manual_approve: bool):
        """Apply to a list of jobs"""
        applied_count = 0
        applications_today = self.tracker.get_applications_today()
        
        with JobScraper() as scraper:
            form_filler = FormFiller(scraper.page, self.ai_assistant)
            
            for i, job in enumerate(jobs):
                # Check daily limit
                if applications_today + applied_count >= config.MAX_APPLICATIONS_PER_DAY:
                    logger.warning("Daily application limit reached")
                    break
                
                logger.info(f"\n[{i+1}/{len(jobs)}] Processing: {job['title']} at {job['company']}")
                
                # Get full job details
                try:
                    full_job = scraper.get_job_details(job['url'])
                    if full_job:
                        job.update(full_job)
                except Exception as e:
                    logger.error(f"Error getting job details: {e}")
                
                # AI evaluation
                evaluation = self.ai_assistant.should_apply_to_job(
                    job.get('description', ''),
                    job['title'],
                    self.cv_data,
                    config.JOB_PREFERENCES
                )
                
                match_score = evaluation.get('match_score', 0)
                should_apply = evaluation.get('should_apply', False)
                
                logger.info(f"Match score: {match_score}/100")
                logger.info(f"AI recommendation: {'APPLY' if should_apply else 'SKIP'}")
                logger.info(f"Reasoning: {evaluation.get('reasoning', 'N/A')}")
                
                # Manual approval
                if manual_approve and should_apply:
                    print(f"\nJob: {job['title']} at {job['company']}")
                    print(f"Location: {job.get('location', 'N/A')}")
                    print(f"Match Score: {match_score}/100")
                    print(f"Reasoning: {evaluation.get('reasoning')}")
                    
                    response = input("\nApply to this job? (y/n): ").strip().lower()
                    should_apply = response == 'y'
                
                if not should_apply:
                    logger.info("Skipping this job")
                    # Still track it so we don't see it again
                    self.tracker.add_application(job, submitted=False, match_score=match_score)
                    continue
                
                # Apply to the job
                try:
                    result = form_filler.fill_application(job, self.cv_data)
                    
                    # Track application
                    self.tracker.add_application(
                        job,
                        submitted=result.get('submitted', False),
                        match_score=match_score
                    )
                    
                    if result.get('submitted'):
                        applied_count += 1
                        logger.info(f"✓ Application submitted successfully!")
                    else:
                        logger.info(f"Application prepared: {result.get('message')}")
                    
                    # Delay between applications
                    time.sleep(config.APPLICATION_DELAY)
                    
                except Exception as e:
                    logger.error(f"Error applying to job: {e}")
                    self.tracker.add_application(job, submitted=False, match_score=match_score)
        
        logger.info(f"\nSuccessfully applied to {applied_count} jobs")
    
    def _display_jobs(self, jobs: List[Dict]):
        """Display job list"""
        print("\n" + "="*80)
        print(f"Found {len(jobs)} jobs:")
        print("="*80 + "\n")
        
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Platform: {job.get('platform', 'N/A')}")
            print(f"   URL: {job['url']}")
            print()
    
    def _show_statistics(self):
        """Display application statistics"""
        stats = self.tracker.get_statistics()
        
        print("\n" + "="*80)
        print("APPLICATION STATISTICS")
        print("="*80)
        print(f"Total Applications: {stats['total']}")
        print(f"Submitted: {stats['submitted']}")
        print(f"Pending: {stats['pending']}")
        print(f"Interviews: {stats['interviews']}")
        print(f"Offers: {stats['offers']}")
        print(f"Rejected: {stats['rejected']}")
        print(f"Today: {stats['today']}")
        print(f"Average Match Score: {stats['average_match_score']}/100")
        print("="*80 + "\n")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AutoJobApplier - Automated job application tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --search-only              Search for jobs without applying
  python main.py --apply                    Apply to jobs automatically
  python main.py --apply --manual-approve   Apply with manual approval
  python main.py --stats                    Show application statistics
  python main.py --export apps.csv          Export applications to CSV
        """
    )
    
    parser.add_argument('--search-only', action='store_true',
                       help='Only search for jobs, don\'t apply')
    parser.add_argument('--apply', action='store_true',
                       help='Apply to jobs')
    parser.add_argument('--manual-approve', action='store_true',
                       help='Require manual approval before each application')
    parser.add_argument('--stats', action='store_true',
                       help='Show application statistics')
    parser.add_argument('--export', type=str, metavar='FILE',
                       help='Export applications to CSV file')
    
    args = parser.parse_args()
    
    # Handle stats
    if args.stats:
        tracker = ApplicationTracker()
        stats = tracker.get_statistics()
        
        print("\nApplication Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Submitted: {stats['submitted']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Interviews: {stats['interviews']}")
        print(f"  Offers: {stats['offers']}")
        print(f"  Today: {stats['today']}")
        print(f"  Avg Match: {stats['average_match_score']}/100\n")
        return
    
    # Handle export
    if args.export:
        tracker = ApplicationTracker()
        filepath = tracker.export_to_csv(args.export)
        print(f"\nExported applications to: {filepath}\n")
        return
    
    # Run main application
    app = AutoJobApplier()
    app.run(
        search_only=args.search_only,
        apply=args.apply,
        manual_approve=args.manual_approve
    )


if __name__ == '__main__':
    main()
