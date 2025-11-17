# AutoJobApplier - Web Interface

Welcome to the web-based version of AutoJobApplier! This document explains how to use the web interface for automated job applications.

## 🚀 Quick Start

### Starting the Web Server

#### On Linux/Mac:
```bash
./start_web.sh
```

#### On Windows:
```bash
start_web.bat
```

#### Or manually:
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

# Start the server
python web_app.py
```

The web interface will be available at: **http://localhost:8000**

## 📋 Features

### 1. Dashboard
The main dashboard provides:
- **Real-time statistics**: Total applications, today's applications, success rate, and average match score
- **Quick actions**: Start job search, begin applying, stop process, export data
- **Activity log**: Live feed of all activities with real-time updates via WebSocket

### 2. Job Search
Search for jobs without automatically applying:
- Enter job titles (comma-separated): e.g., "Software Engineer, Full Stack Developer"
- Specify locations (comma-separated): e.g., "New York, Remote, San Francisco"
- Select platforms: Indeed, LinkedIn
- Optional filters:
  - Include keywords: Jobs must contain these terms
  - Exclude keywords: Jobs containing these terms will be skipped
- View found jobs in real-time as they're discovered

### 3. Applications
View and manage your application history:
- See all applications with details: job title, company, location, status
- Filter by status: Applied, Pending, Rejected, Interview
- View match scores for each application
- Click to view original job postings
- Refresh to see latest updates

### 4. Configuration
Manage all settings through the web interface:

#### Personal Information
- Full name
- Email address
- Phone number

#### Application Settings
- **Max applications per day**: Limit daily applications (default: 20)
- **Application delay**: Seconds to wait between applications (default: 30)
- **Auto-submit**: Enable/disable automatic submission without manual approval
- **Headless mode**: Run browser invisibly in the background

#### Resume Upload
- Upload your resume (PDF or DOCX format)
- Automatically parsed to extract skills, experience, and education
- Used for intelligent form filling and job matching

## 🔄 Real-Time Updates

The web interface uses WebSocket connections to provide live updates:
- Connection status indicator in the header
- Live activity log showing all actions as they happen
- Real-time statistics updates
- Instant notifications for job discoveries and applications

## 🎯 How to Use

### Basic Workflow

1. **Initial Setup**
   - Go to Configuration tab
   - Fill in your personal information
   - Upload your resume
   - Configure application settings
   - Save configuration

2. **Search for Jobs**
   - Go to Search tab
   - Enter job titles and locations
   - Select platforms (Indeed, LinkedIn)
   - Add optional keyword filters
   - Click "Search Jobs"
   - View results in real-time on the Dashboard

3. **Start Applying**
   - From Dashboard, click "Start Applying"
   - Confirm settings (auto-submit on/off, max applications)
   - Watch the activity log for real-time progress
   - View applications in the Applications tab

4. **Monitor Progress**
   - Dashboard shows live statistics
   - Activity log displays all actions
   - Applications tab shows complete history
   - Export data anytime as CSV

### Manual Approval Mode

If auto-submit is disabled:
- System will evaluate each job using AI
- Jobs with high match scores (70+) will be flagged for approval
- You'll see "Manual approval needed" in the activity log
- Currently, approval must be done via CLI (web approval coming soon)

### Stopping the Process

Click the "Stop Process" button to gracefully stop:
- Current job search
- Application process
- System will finish current action then stop

## 📊 Statistics Explained

- **Total Applications**: All-time application count
- **Today's Applications**: Applications submitted today
- **Success Rate**: Percentage of applications that received responses
- **Avg. Match Score**: Average AI-generated match score (0-100)

## 🔧 API Endpoints

The web interface uses these REST API endpoints:

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/statistics` - Get application statistics
- `GET /api/applications` - List all applications
- `POST /api/search` - Start job search
- `POST /api/apply` - Start application process
- `POST /api/stop` - Stop current process
- `POST /api/upload-resume` - Upload resume file
- `GET /api/export` - Export applications to CSV
- `WS /ws` - WebSocket for real-time updates

## 🛠️ Advanced Configuration

### Running on Different Port

Edit `web_app.py` and change the port in the last line:
```python
uvicorn.run(
    "web_app:app",
    host="0.0.0.0",
    port=8080,  # Change this
    reload=True,
    log_level="info"
)
```

### Enabling Remote Access

By default, the server binds to `0.0.0.0`, allowing remote access.
To restrict to local only, change `host` to `"127.0.0.1"`.

**Security Warning**: If allowing remote access, consider:
- Using HTTPS (configure reverse proxy like nginx)
- Adding authentication (implement in FastAPI)
- Firewall rules to restrict access

### Production Deployment

For production use:

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn web_app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🐛 Troubleshooting

### WebSocket Connection Failed
- Check if firewall is blocking WebSocket connections
- Ensure the server is running
- Try refreshing the page

### Resume Upload Failed
- Check file format (must be PDF or DOCX)
- Ensure file is not corrupted
- Check file size (should be < 10MB)

### Application Process Not Starting
- Verify config.py exists with valid API keys
- Check activity log for error messages
- Ensure daily application limit not reached

### Configuration Not Saving
- Check write permissions for config.py
- View browser console for API errors
- Verify all required fields are filled

## 📱 Browser Compatibility

Tested and working on:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera

Required browser features:
- WebSocket support
- ES6 JavaScript
- CSS Grid/Flexbox

## 🔐 Security Considerations

- **API Keys**: Never expose your config.py file publicly
- **Local Storage**: All data stored locally in SQLite database
- **No External Tracking**: No analytics or external connections
- **Resume Privacy**: Resumes stored locally in `data/resumes/`

## 💡 Tips

1. **Start Small**: Begin with 5-10 applications per day to test
2. **Monitor Activity**: Keep the dashboard open to watch progress
3. **Review Match Scores**: Check which jobs score highest
4. **Export Regularly**: Download your application data periodically
5. **Update Resume**: Keep your resume updated for best results

## 🆚 Web vs CLI

### Web Interface Advantages:
- User-friendly GUI
- Real-time visual feedback
- Easy configuration management
- No command-line knowledge needed
- Visual statistics and charts

### CLI Advantages:
- Faster for experienced users
- Scriptable and automatable
- Lower resource usage
- Better for remote servers

Both interfaces use the same backend, so you can switch between them!

## 📞 Support

If you encounter issues:
1. Check the activity log for error messages
2. Review this documentation
3. Check the main README.md for general troubleshooting
4. Open an issue on GitHub with details

## 🔄 Updates

To update the web interface:
```bash
git pull
pip install -r requirements.txt --upgrade
```

## 🎉 Enjoy!

The web interface makes automated job applications easier than ever. Happy job hunting!

---

**Note**: The web interface is actively developed. Features may be added or changed. Check for updates regularly!
