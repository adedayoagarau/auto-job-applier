"""
Job Scraper module for finding job postings on various platforms
"""

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup
import time
from typing import List, Dict
from urllib.parse import quote_plus
from loguru import logger
import random

try:
    import config
except ImportError:
    logger.error("config.py not found.")
    raise


class JobScraper:
    """
    Scrape job postings from various job boards
    """
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        
    def __enter__(self):
        """Context manager entry"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=config.HEADLESS,
            args=['--disable-blink-features=AutomationControlled'] if config.STEALTH_MODE else []
        )
        
        # Create context with user agent
        context = self.browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = context.new_page()
        self.page.set_default_timeout(config.BROWSER_TIMEOUT)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def search_jobs(self, platform: str, job_title: str, location: str) -> List[Dict]:
        """
        Search for jobs on a specific platform
        
        Args:
            platform: Platform name (indeed, linkedin, etc.)
            job_title: Job title to search for
            location: Location to search in
            
        Returns:
            List of job dictionaries
        """
        if platform.lower() == 'indeed':
            return self._search_indeed(job_title, location)
        elif platform.lower() == 'linkedin':
            return self._search_linkedin(job_title, location)
        else:
            logger.warning(f"Platform {platform} not supported yet")
            return []
    
    def _search_indeed(self, job_title: str, location: str) -> List[Dict]:
        """Search Indeed for jobs"""
        jobs = []
        
        try:
            # Construct Indeed search URL
            base_url = "https://www.indeed.com/jobs"
            query = f"?q={quote_plus(job_title)}&l={quote_plus(location)}"
            url = base_url + query
            
            logger.info(f"Searching Indeed: {job_title} in {location}")
            self.page.goto(url, wait_until='domcontentloaded')
            
            # Wait for job listings to load
            time.sleep(config.PAGE_LOAD_DELAY)
            
            # Get page content
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find job cards (Indeed's structure may change)
            job_cards = soup.find_all('div', class_=lambda x: x and 'job_seen_beacon' in x)
            
            if not job_cards:
                # Try alternative selector
                job_cards = soup.find_all('div', {'data-testid': 'job-card'})
            
            logger.info(f"Found {len(job_cards)} job listings")
            
            for card in job_cards[:20]:  # Limit to 20 per search
                try:
                    job = self._parse_indeed_job_card(card, self.page.url)
                    if job and self._should_include_job(job):
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error parsing job card: {e}")
                    
        except Exception as e:
            logger.error(f"Error searching Indeed: {e}")
        
        return jobs
    
    def _parse_indeed_job_card(self, card, page_url: str) -> Dict:
        """Parse an Indeed job card element"""
        job = {
            'platform': 'indeed',
            'source_url': page_url
        }
        
        # Extract job title
        title_elem = card.find('h2', class_=lambda x: x and 'jobTitle' in str(x))
        if title_elem:
            link = title_elem.find('a')
            if link:
                job['title'] = link.get_text(strip=True)
                job['url'] = 'https://www.indeed.com' + link.get('href', '')
        
        # Extract company name
        company_elem = card.find('span', {'data-testid': 'company-name'})
        if not company_elem:
            company_elem = card.find('span', class_=lambda x: x and 'companyName' in str(x))
        if company_elem:
            job['company'] = company_elem.get_text(strip=True)
        
        # Extract location
        location_elem = card.find('div', {'data-testid': 'text-location'})
        if not location_elem:
            location_elem = card.find('div', class_=lambda x: x and 'companyLocation' in str(x))
        if location_elem:
            job['location'] = location_elem.get_text(strip=True)
        
        # Extract salary (if available)
        salary_elem = card.find('div', class_=lambda x: x and 'salary' in str(x).lower())
        if salary_elem:
            job['salary'] = salary_elem.get_text(strip=True)
        
        # Extract job snippet/description
        snippet_elem = card.find('div', class_=lambda x: x and 'jobsnippet' in str(x).lower())
        if snippet_elem:
            job['description_snippet'] = snippet_elem.get_text(strip=True)
        
        # Check if we have minimum required fields
        if 'title' in job and 'company' in job:
            return job
        
        return None
    
    def _search_linkedin(self, job_title: str, location: str) -> List[Dict]:
        """
        Search LinkedIn for jobs
        Note: LinkedIn requires authentication for most features
        """
        jobs = []
        
        try:
            base_url = "https://www.linkedin.com/jobs/search"
            query = f"?keywords={quote_plus(job_title)}&location={quote_plus(location)}"
            url = base_url + query
            
            logger.info(f"Searching LinkedIn: {job_title} in {location}")
            self.page.goto(url, wait_until='domcontentloaded')
            
            time.sleep(config.PAGE_LOAD_DELAY)
            
            # LinkedIn may require login for detailed views
            if 'authwall' in self.page.url or 'login' in self.page.url:
                logger.warning("LinkedIn requires authentication. Skipping.")
                return []
            
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Parse LinkedIn job cards (structure may vary)
            job_cards = soup.find_all('div', class_=lambda x: x and 'job-search-card' in str(x))
            
            logger.info(f"Found {len(job_cards)} LinkedIn job listings")
            
            for card in job_cards[:20]:
                try:
                    job = self._parse_linkedin_job_card(card)
                    if job and self._should_include_job(job):
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error parsing LinkedIn job card: {e}")
                    
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
        
        return jobs
    
    def _parse_linkedin_job_card(self, card) -> Dict:
        """Parse a LinkedIn job card element"""
        job = {
            'platform': 'linkedin'
        }
        
        # Extract title
        title_elem = card.find('h3', class_=lambda x: x and 'job-search-card__title' in str(x))
        if title_elem:
            job['title'] = title_elem.get_text(strip=True)
        
        # Extract company
        company_elem = card.find('h4', class_=lambda x: x and 'job-search-card__company' in str(x))
        if company_elem:
            job['company'] = company_elem.get_text(strip=True)
        
        # Extract location
        location_elem = card.find('span', class_=lambda x: x and 'job-search-card__location' in str(x))
        if location_elem:
            job['location'] = location_elem.get_text(strip=True)
        
        # Extract URL
        link = card.find('a', class_=lambda x: x and 'job-search-card' in str(x))
        if link:
            job['url'] = link.get('href', '')
        
        if 'title' in job and 'company' in job:
            return job
        
        return None
    
    def _should_include_job(self, job: Dict) -> bool:
        """
        Check if job should be included based on exclude keywords
        """
        title = job.get('title', '').lower()
        description = job.get('description_snippet', '').lower()
        
        # Check exclude keywords
        for keyword in config.EXCLUDE_KEYWORDS:
            if keyword.lower() in title or keyword.lower() in description:
                logger.debug(f"Excluding job due to keyword '{keyword}': {job.get('title')}")
                return False
        
        return True
    
    def get_job_details(self, job_url: str) -> Dict:
        """
        Get full details for a specific job posting
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Dictionary with full job details
        """
        try:
            logger.info(f"Fetching job details: {job_url}")
            self.page.goto(job_url, wait_until='domcontentloaded')
            time.sleep(config.PAGE_LOAD_DELAY)
            
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract full job description
            # This varies by platform - implement specific parsers
            if 'indeed.com' in job_url:
                return self._parse_indeed_job_details(soup, job_url)
            elif 'linkedin.com' in job_url:
                return self._parse_linkedin_job_details(soup, job_url)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching job details: {e}")
            return {}
    
    def _parse_indeed_job_details(self, soup: BeautifulSoup, url: str) -> Dict:
        """Parse full Indeed job details"""
        details = {'url': url, 'platform': 'indeed'}
        
        # Job title
        title_elem = soup.find('h1', class_=lambda x: x and 'jobsearch-JobInfoHeader-title' in str(x))
        if title_elem:
            details['title'] = title_elem.get_text(strip=True)
        
        # Company
        company_elem = soup.find('div', {'data-testid': 'inlineHeader-companyName'})
        if company_elem:
            details['company'] = company_elem.get_text(strip=True)
        
        # Full description
        desc_elem = soup.find('div', id='jobDescriptionText')
        if desc_elem:
            details['description'] = desc_elem.get_text(separator='\n', strip=True)
        
        return details
    
    def _parse_linkedin_job_details(self, soup: BeautifulSoup, url: str) -> Dict:
        """Parse full LinkedIn job details"""
        details = {'url': url, 'platform': 'linkedin'}
        
        # Implementation depends on LinkedIn's current structure
        # May require authentication
        
        return details
