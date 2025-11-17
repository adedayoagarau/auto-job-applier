# Quick Start Guide

## Prerequisites

1. **Python 3.9+** installed on your system
2. **Anthropic API Key** - Get one from [console.anthropic.com](https://console.anthropic.com/)
3. **Your Resume** in PDF or DOCX format

## Installation

### Option 1: Automatic Setup (Recommended)

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
setup.bat
```

### Option 2: Manual Setup

1. **Clone or download this repository**

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate.bat
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

5. **Configure the application:**
```bash
cp config.example.py config.py
# Edit config.py with your details
```

## Configuration

Edit `config.py` with your information:

### 1. API Key (Required)
```python
ANTHROPIC_API_KEY = "your-api-key-here"
```

### 2. Personal Information
```python
PERSONAL_INFO = {
    "first_name": "Your First Name",
    "last_name": "Your Last Name",
    "email": "your.email@example.com",
    "phone": "+1234567890",
    "linkedin": "https://linkedin.com/in/yourprofile",
    # ... etc
}
```

### 3. Job Search Criteria
```python
JOB_TITLES = [
    "Software Engineer",
    "Senior Developer",
]

LOCATIONS = [
    "Remote",
    "San Francisco, CA",
]

KEYWORDS = [
    "python",
    "react",
]
```

### 4. Add Your Resume
```bash
cp /path/to/your/resume.pdf data/resume.pdf
```

## Usage

### 1. Search for Jobs (Dry Run)

First, test the search functionality without applying:

```bash
python main.py --search-only
```

This will:
- Search configured job boards
- Display matching jobs
- NOT apply to anything

### 2. Apply with Manual Approval

Apply to jobs but approve each one manually:

```bash
python main.py --apply --manual-approve
```

For each job, you'll see:
- Job title and company
- Match score
- AI reasoning
- Prompt to approve/reject

### 3. Fully Automated

Apply automatically to all matching jobs:

```bash
python main.py --apply
```

⚠️ **Warning:** Make sure you've tested with `--manual-approve` first!

### 4. View Statistics

Check your application stats:

```bash
python main.py --stats
```

### 5. Export Applications

Export to CSV for tracking:

```bash
python main.py --export my_applications.csv
```

## Important Settings

### Daily Limits
```python
MAX_APPLICATIONS_PER_DAY = 20  # Don't exceed this
```

### Auto-Submit
```python
AUTO_SUBMIT = False  # Set True for full automation
```

When `False`, forms are filled but you must submit manually.

### Headless Mode
```python
HEADLESS = True  # Run browser in background
```

Set to `False` to watch the browser in action (useful for debugging).

## Workflow Recommendations

### First Time Using

1. **Day 1: Search Only**
   ```bash
   python main.py --search-only
   ```
   Review the jobs found. Adjust search criteria if needed.

2. **Day 2: Manual Approval**
   ```bash
   python main.py --apply --manual-approve
   ```
   Apply to 5-10 jobs manually to see how it works.

3. **Day 3: Monitor Results**
   Check if applications were received correctly.
   Review screenshots in `screenshots/` folder.

4. **Day 4+: Automate**
   Once comfortable, run without manual approval:
   ```bash
   python main.py --apply
   ```

### Daily Routine

```bash
# Morning: Run job search and applications
python main.py --apply

# Evening: Check statistics
python main.py --stats
```

## Troubleshooting

### Issue: "config.py not found"
**Solution:** Copy `config.example.py` to `config.py`

### Issue: "Resume file not found"
**Solution:** Place your resume at `data/resume.pdf`

### Issue: "API key invalid"
**Solution:** Check your Anthropic API key in config.py

### Issue: Browser automation detected
**Solution:** Enable stealth mode in config:
```python
STEALTH_MODE = True
```

### Issue: Forms not filling correctly
**Solution:** 
1. Set `HEADLESS = False` to watch what's happening
2. Check `logs/app.log` for errors
3. Review screenshots in `screenshots/` folder

### Issue: Rate limited
**Solution:** 
1. Reduce `MAX_APPLICATIONS_PER_DAY`
2. Increase `APPLICATION_DELAY`

## Cost Estimation

### Claude API Costs

Typical costs per application:
- Simple application: $0.01 - $0.02
- Complex application: $0.03 - $0.05

At 20 applications/day:
- Daily: ~$0.40 - $1.00
- Monthly: ~$12 - $30

Much cheaper than aiapply ($60/mo) or Sonara AI ($80/mo)!

## Safety Tips

1. **Start Slow**: Use manual approval for the first week
2. **Review Applications**: Check screenshots and logs regularly
3. **Monitor Email**: Watch for application confirmations
4. **Adjust Criteria**: Refine your job search criteria based on results
5. **Respect Rate Limits**: Don't set daily limits too high
6. **Terms of Service**: Review each platform's ToS

## Advanced Usage

### Custom Job Filters

Edit `config.py` to add exclude keywords:
```python
EXCLUDE_KEYWORDS = [
    "blockchain",
    "crypto",
    "on-site only",
]
```

### Platform-Specific Settings

Configure which platforms to search:
```python
PLATFORMS = [
    "indeed",
    # "linkedin",  # Uncomment to enable
]
```

### Notification Setup

Enable email notifications:
```python
SEND_EMAIL_NOTIFICATIONS = True
EMAIL_USERNAME = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"  # Use app password, not regular password
```

## Logs and Debugging

### View Logs
```bash
tail -f logs/app.log
```

### Log Levels
```python
LOG_LEVEL = "DEBUG"  # More detailed logs
LOG_LEVEL = "INFO"   # Normal logs (default)
LOG_LEVEL = "WARNING"  # Only warnings/errors
```

### Screenshots

Screenshots are saved to `screenshots/` folder:
- `before_application_*.png` - Before filling form
- `after_filling_*.png` - After filling form

## Database

Applications are tracked in `data/applications.db` (SQLite).

You can view it with any SQLite browser or:
```bash
sqlite3 data/applications.db
SELECT * FROM applications;
```

## Getting Help

If you encounter issues:

1. Check logs: `logs/app.log`
2. Review screenshots: `screenshots/`
3. Test with `--search-only` first
4. Use `--manual-approve` to see what's happening
5. Set `HEADLESS = False` to watch browser
6. Check GitHub issues or create a new one

## Next Steps

After getting comfortable:

1. Refine your job search criteria
2. Adjust match score thresholds
3. Customize cover letter generation
4. Set up email notifications
5. Schedule daily runs with cron/Task Scheduler

Happy job hunting! 🎯
