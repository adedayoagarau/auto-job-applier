# Example Usage

## Basic Example

```python
from src.job_scraper import JobScraper
from src.cv_parser import CVParser
from src.ai_assistant import AIAssistant

# Parse your CV
cv_parser = CVParser("data/resume.pdf")
cv_data = cv_parser.parse()

print(f"Found {len(cv_data['skills'])} skills")
print(f"Skills: {', '.join(cv_data['skills'][:5])}")

# Search for jobs
with JobScraper() as scraper:
    jobs = scraper.search_jobs("indeed", "Software Engineer", "Remote")
    print(f"\nFound {len(jobs)} jobs")
    
    for job in jobs[:3]:
        print(f"\n{job['title']} at {job['company']}")
        print(f"Location: {job['location']}")

# Use AI to evaluate a job
ai = AIAssistant()
if jobs:
    evaluation = ai.should_apply_to_job(
        jobs[0].get('description', ''),
        jobs[0]['title'],
        cv_data,
        {'remote': True, 'salary_minimum': 100000}
    )
    
    print(f"\nJob Match Analysis:")
    print(f"Score: {evaluation['match_score']}/100")
    print(f"Should apply: {evaluation['should_apply']}")
    print(f"Reasoning: {evaluation['reasoning']}")
```

## Advanced Example: Custom Job Filter

```python
from src.job_scraper import JobScraper
from src.application_tracker import ApplicationTracker

def custom_job_filter(job, cv_data):
    """Custom logic to decide if you want to apply"""
    
    # Must be remote
    if 'remote' not in job.get('location', '').lower():
        return False
    
    # Must mention specific technologies
    description = job.get('description', '').lower()
    required_tech = ['python', 'react']
    
    if not any(tech in description for tech in required_tech):
        return False
    
    # Must not be a specific company
    blocked_companies = ['Company X', 'Company Y']
    if job.get('company') in blocked_companies:
        return False
    
    return True

# Use the filter
tracker = ApplicationTracker()

with JobScraper() as scraper:
    all_jobs = scraper.search_jobs("indeed", "Software Engineer", "Remote")
    
    filtered_jobs = [
        job for job in all_jobs 
        if custom_job_filter(job, {}) and not tracker.has_applied(job['url'])
    ]
    
    print(f"Filtered to {len(filtered_jobs)} jobs")
```

## Example: Generate Custom Cover Letters

```python
from src.ai_assistant import AIAssistant
from src.cv_parser import CVParser

ai = AIAssistant()
cv_parser = CVParser()
cv_data = cv_parser.parse()

job_description = """
We're looking for a Senior Python Developer to join our team...
[full job description]
"""

cover_letter = ai.generate_cover_letter(
    job_description=job_description,
    cv_data=cv_data,
    company_name="Amazing Tech Co",
    position="Senior Python Developer"
)

print(cover_letter)

# Save to file
with open('cover_letter.txt', 'w') as f:
    f.write(cover_letter)
```

## Example: Batch Process Multiple Resumes

```python
from pathlib import Path
from src.cv_parser import CVParser

resume_dir = Path("resumes")

for resume_file in resume_dir.glob("*.pdf"):
    print(f"\nProcessing: {resume_file.name}")
    
    parser = CVParser(str(resume_file))
    cv_data = parser.parse()
    
    print(f"  Skills: {len(cv_data['skills'])}")
    print(f"  Experience entries: {len(cv_data['experience'])}")
    print(f"  Education: {len(cv_data['education'])}")
```

## Example: Export and Analyze Application Data

```python
from src.application_tracker import ApplicationTracker
import pandas as pd

tracker = ApplicationTracker()

# Get all applications
apps = tracker.get_all_applications()

# Convert to DataFrame for analysis
data = [{
    'date': app.applied_date,
    'title': app.job_title,
    'company': app.company,
    'platform': app.platform,
    'submitted': app.submitted,
    'status': app.status,
    'match_score': app.match_score
} for app in apps]

df = pd.DataFrame(data)

# Analysis
print("\nApplications by Platform:")
print(df['platform'].value_counts())

print("\nApplications by Status:")
print(df['status'].value_counts())

print(f"\nAverage Match Score: {df['match_score'].mean():.2f}")

print("\nTop Companies:")
print(df['company'].value_counts().head())

# Export
df.to_csv('analysis.csv', index=False)
```

## Example: Schedule Daily Runs

### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Add this line to run every day at 9 AM
0 9 * * * cd /path/to/auto-job-applier && /path/to/venv/bin/python main.py --apply
```

### Windows (Task Scheduler)

Create a batch file `run_daily.bat`:
```batch
@echo off
cd C:\path\to\auto-job-applier
call venv\Scripts\activate.bat
python main.py --apply
```

Then schedule it in Task Scheduler to run daily.

## Example: Integration with Other Tools

### Send Slack Notification

```python
import requests
from src.application_tracker import ApplicationTracker

def send_slack_notification(message):
    webhook_url = "your-slack-webhook-url"
    requests.post(webhook_url, json={"text": message})

tracker = ApplicationTracker()
stats = tracker.get_statistics()

message = f"""
📊 Daily Application Report
Total: {stats['total']}
Today: {stats['today']}
Interviews: {stats['interviews']}
"""

send_slack_notification(message)
```

### Log to Google Sheets

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from src.application_tracker import ApplicationTracker

# Setup Google Sheets API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

sheet = client.open('Job Applications').sheet1

# Get applications
tracker = ApplicationTracker()
apps = tracker.get_all_applications(limit=10)

# Write to sheet
for app in apps:
    row = [
        app.applied_date.strftime('%Y-%m-%d'),
        app.job_title,
        app.company,
        app.status,
        app.match_score
    ]
    sheet.append_row(row)
```

## Tips and Best Practices

1. **Test thoroughly** with `--search-only` and `--manual-approve`
2. **Start small** with low daily limits
3. **Monitor logs** regularly for errors
4. **Review screenshots** to ensure forms are filled correctly
5. **Respect rate limits** to avoid being blocked
6. **Keep resume updated** for best results
7. **Refine search criteria** based on results
8. **Track your success rate** and adjust strategy
