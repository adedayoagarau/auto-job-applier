# AutoJobApplier 🚀

An intelligent job application automation tool that finds relevant jobs, fills out applications, and tracks your submissions - all automatically.

## 🎯 Why AutoJobApplier?

Competitors like aiapply and Sonara AI charge premium prices. AutoJobApplier gives you the same power at a fraction of the cost (just API usage + your time).

## ✨ Features

- **Smart Job Discovery**: Automatically searches job boards (Indeed, LinkedIn, etc.)
- **Intelligent Form Filling**: Uses AI to understand and fill application forms
- **Auto-Submission**: Submits applications with your approval (or fully automated)
- **Application Tracking**: Keeps track of all applications in a local database
- **Resume Parsing**: Extracts information from your CV to fill forms accurately
- **Customizable**: Configure which platforms, job titles, and criteria to use
- **🌐 Web Interface**: Modern web-based UI with real-time updates (NEW!)

## 🌐 Web Interface

AutoJobApplier now includes a beautiful web-based interface! No command-line experience needed.

### Quick Start (Web Version)

```bash
# Linux/Mac
./start_web.sh

# Windows
start_web.bat
```

Then open your browser to **http://localhost:8000**

### Web Features
- 📊 Real-time dashboard with live statistics
- 🔍 Interactive job search interface
- 📝 Visual application history and tracking
- ⚙️ Easy configuration management through the UI
- 📤 Resume upload with automatic parsing
- 🔄 Live activity feed with WebSocket updates
- 📥 Export data to CSV with one click

See [WEB_INTERFACE.md](WEB_INTERFACE.md) for detailed documentation.

## 🛠️ Tech Stack

- **Python 3.9+**
- **Playwright**: Browser automation
- **Claude API**: Intelligent form understanding and filling
- **SQLite**: Application tracking database
- **Beautiful Soup**: HTML parsing
- **FastAPI**: Modern web framework for the web interface
- **WebSockets**: Real-time updates in the web UI

## 📋 Prerequisites

- Python 3.9 or higher
- Claude API key (from Anthropic)
- Your resume/CV in PDF or DOCX format

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/auto-job-applier.git
cd auto-job-applier
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure your settings

```bash
cp config.example.py config.py
# Edit config.py with your details
```

### 4. Add your resume

```bash
# Place your resume in the data folder
cp /path/to/your/resume.pdf data/resume.pdf
```

### 5. Run the application

```bash
# Search for jobs (dry run - no applications)
python main.py --search-only

# Start applying to jobs
python main.py --apply

# Run with approval mode (you approve each application)
python main.py --apply --manual-approve
```

## 📁 Project Structure

```
auto-job-applier/
├── main.py                 # Main entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── src/
│   ├── job_scraper.py    # Job board scrapers
│   ├── form_filler.py    # AI-powered form filling
│   ├── cv_parser.py      # Parse resume data
│   ├── application_tracker.py  # Track applications
│   └── ai_assistant.py   # Claude API integration
│
├── data/
│   ├── resume.pdf        # Your resume
│   └── applications.db   # SQLite database
│
├── logs/
│   └── app.log          # Application logs
│
└── utils/
    ├── browser.py       # Browser automation helpers
    └── helpers.py       # Utility functions
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Job search criteria
JOB_TITLES = ["Software Engineer", "Senior Developer"]
LOCATIONS = ["Remote", "San Francisco, CA"]
PLATFORMS = ["indeed", "linkedin"]

# AI settings
ANTHROPIC_API_KEY = "your-api-key-here"
MODEL = "claude-sonnet-4-5-20250929"

# Application settings
AUTO_SUBMIT = False  # Set to True for full automation
MAX_APPLICATIONS_PER_DAY = 20
```

## 📊 Tracking Applications

View your applications:

```bash
python main.py --stats
```

Export to CSV:

```bash
python main.py --export applications.csv
```

## 🤝 Supported Platforms

- [x] Indeed
- [x] LinkedIn (partially - requires login)
- [ ] Glassdoor (coming soon)
- [ ] ZipRecruiter (coming soon)
- [ ] Company career pages (coming soon)

## ⚠️ Important Notes

1. **Rate Limiting**: The tool respects rate limits to avoid being blocked
2. **Terms of Service**: Review each platform's ToS before using
3. **Manual Review**: Use `--manual-approve` mode to review applications before submission
4. **API Costs**: Claude API usage incurs costs (typically $0.01-0.05 per application)

## 🔒 Privacy & Security

- All data stored locally
- No data sent to third parties (except Claude API for form filling)
- Your resume and personal info never leave your machine except during application submission
- API keys stored in config.py (add to .gitignore)

## 🐛 Troubleshooting

**Issue**: Browser automation detected
- Solution: Use stealth mode in config (`STEALTH_MODE = True`)

**Issue**: Forms not filling correctly
- Solution: Check logs for AI responses, may need to adjust prompts

**Issue**: Rate limited by job board
- Solution: Reduce `MAX_APPLICATIONS_PER_DAY` and add delays

## 📈 Roadmap

- [ ] Support for more job platforms
- [x] Cover letter generation (AI-powered)
- [ ] Interview scheduling assistance
- [ ] Chrome extension for easy job saving
- [x] Web dashboard for tracking
- [ ] Email notification system

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

## 📄 License

MIT License - feel free to use and modify for personal use.

## ⚡ Disclaimer

This tool is for personal use only. Always review applications before submission and comply with all platform Terms of Service. The authors are not responsible for any consequences of using this tool.

---

Built with ❤️ to make job hunting less painful
