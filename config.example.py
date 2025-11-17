"""
Configuration file for AutoJobApplier
Copy this to config.py and fill in your details
"""

# ==================== API KEYS ====================
# Get your key from: https://console.anthropic.com/
ANTHROPIC_API_KEY = "your-api-key-here"

# Claude model to use
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# ==================== JOB SEARCH CRITERIA ====================
# Job titles to search for
JOB_TITLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Full Stack Developer",
    "Backend Engineer",
]

# Locations to search (use "Remote" for remote jobs)
LOCATIONS = [
    "Remote",
    "San Francisco, CA",
    "New York, NY",
]

# Experience levels (adjust based on platform)
EXPERIENCE_LEVELS = [
    "Mid-Level",
    "Senior",
]

# Job platforms to search
PLATFORMS = [
    "indeed",
    # "linkedin",  # Uncomment when ready
]

# Keywords to include in search
KEYWORDS = [
    "python",
    "react",
    "full-stack",
]

# Keywords to exclude (jobs with these won't be applied to)
EXCLUDE_KEYWORDS = [
    "blockchain",
    "crypto",
    "web3",
    "on-site only",
]

# ==================== APPLICATION SETTINGS ====================
# Maximum applications per day (to avoid rate limiting)
MAX_APPLICATIONS_PER_DAY = 20

# Maximum applications per platform per day
MAX_APPLICATIONS_PER_PLATFORM = 10

# Auto-submit applications (True) or require manual approval (False)
AUTO_SUBMIT = False

# Delay between applications (seconds)
APPLICATION_DELAY = 30

# Delay between page loads (seconds)
PAGE_LOAD_DELAY = 2

# ==================== BROWSER SETTINGS ====================
# Run browser in headless mode
HEADLESS = True

# Use stealth mode to avoid detection
STEALTH_MODE = True

# Browser timeout (seconds)
BROWSER_TIMEOUT = 30000

# Take screenshots of applications
TAKE_SCREENSHOTS = True

# ==================== RESUME/CV SETTINGS ====================
# Path to your resume file
RESUME_PATH = "data/resume.pdf"

# Path to your cover letter template (optional)
COVER_LETTER_PATH = "data/cover_letter.txt"

# ==================== PERSONAL INFORMATION ====================
# This will be used to fill forms
PERSONAL_INFO = {
    "first_name": "Your First Name",
    "last_name": "Your Last Name",
    "email": "your.email@example.com",
    "phone": "+1234567890",
    "linkedin": "https://linkedin.com/in/yourprofile",
    "github": "https://github.com/yourusername",
    "portfolio": "https://yourportfolio.com",
    "city": "Your City",
    "state": "Your State",
    "country": "Your Country",
    "zip_code": "12345",
}

# ==================== WORK AUTHORIZATION ====================
WORK_AUTHORIZATION = {
    "us_citizen": False,
    "require_sponsorship": True,
    "authorized_to_work": True,
    "clearance": None,  # "Secret", "Top Secret", etc.
}

# ==================== JOB PREFERENCES ====================
JOB_PREFERENCES = {
    "remote": True,
    "willing_to_relocate": False,
    "salary_minimum": 100000,  # USD
    "job_types": ["Full-time"],  # Full-time, Part-time, Contract, Internship
    "notice_period": "2 weeks",
}

# ==================== DATABASE SETTINGS ====================
DATABASE_PATH = "data/applications.db"

# ==================== LOGGING SETTINGS ====================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "logs/app.log"
LOG_ROTATION = "10 MB"

# ==================== NOTIFICATION SETTINGS ====================
# Email notifications (optional)
SEND_EMAIL_NOTIFICATIONS = False
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_TO = "your-email@gmail.com"

# ==================== ADVANCED SETTINGS ====================
# Maximum retries for failed operations
MAX_RETRIES = 3

# Timeout for API calls (seconds)
API_TIMEOUT = 60

# Save HTML of application pages
SAVE_HTML = False

# User agent string
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
