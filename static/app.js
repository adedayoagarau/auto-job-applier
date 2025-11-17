// AutoJobApplier - Frontend JavaScript

class AutoJobApplierApp {
    constructor() {
        this.ws = null;
        this.config = null;
        this.isConnected = false;
        this.currentTab = 'dashboard';

        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadConfig();
        this.loadStatistics();
        this.loadApplications();
    }

    // WebSocket Connection
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);

            // Reconnect after 3 seconds
            setTimeout(() => this.setupWebSocket(), 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('connectionStatus');
        const statusText = document.getElementById('connectionText');

        if (connected) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Disconnected';
        }
    }

    handleWebSocketMessage(message) {
        console.log('Received message:', message);

        const { type, data } = message;

        switch (type) {
            case 'connection':
                this.addActivityLog('Connected to server', 'success');
                break;

            case 'search_started':
                this.addActivityLog('Job search started...', 'info');
                this.showStopButton();
                break;

            case 'search_progress':
                this.addActivityLog(data.message, 'info');
                break;

            case 'job_found':
                this.addActivityLog(`Found job: ${data.job.title} at ${data.job.company}`, 'success');
                this.addJobToList(data.job);
                break;

            case 'search_completed':
                this.addActivityLog(data.message, 'success');
                this.hideStopButton();
                this.loadStatistics();
                break;

            case 'application_started':
                this.addActivityLog('Application process started...', 'info');
                this.showStopButton();
                break;

            case 'job_evaluation':
                this.addActivityLog(`Evaluating: ${data.job.title}`, 'info');
                break;

            case 'job_evaluated':
                const scoreColor = data.score >= 70 ? 'success' : 'warning';
                this.addActivityLog(
                    `Job scored ${data.score}/100 - ${data.reasoning}`,
                    scoreColor
                );
                break;

            case 'applying':
                this.addActivityLog(`Applying to: ${data.job.title}`, 'info');
                break;

            case 'application_success':
                this.addActivityLog(
                    `Successfully applied! Total today: ${data.applications_today}`,
                    'success'
                );
                this.loadStatistics();
                this.loadApplications();
                break;

            case 'application_failed':
                this.addActivityLog(`Failed to apply: ${data.message}`, 'error');
                break;

            case 'application_completed':
                this.addActivityLog(data.message, 'success');
                this.hideStopButton();
                this.loadStatistics();
                this.loadApplications();
                break;

            case 'approval_needed':
                this.addActivityLog(
                    `Manual approval needed for: ${data.job.title} (Score: ${data.score})`,
                    'warning'
                );
                break;

            case 'process_stopped':
                this.addActivityLog('Process stopped', 'warning');
                this.hideStopButton();
                break;

            case 'error':
                this.addActivityLog(`Error: ${data.message}`, 'error');
                this.hideStopButton();
                break;
        }
    }

    // Event Listeners
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Dashboard buttons
        document.getElementById('startSearch').addEventListener('click', () => {
            this.switchTab('search');
        });

        document.getElementById('startApply').addEventListener('click', () => {
            this.startApplicationProcess();
        });

        document.getElementById('stopProcess').addEventListener('click', () => {
            this.stopProcess();
        });

        document.getElementById('exportData').addEventListener('click', () => {
            this.exportData();
        });

        // Search form
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitSearch();
        });

        // Config form
        document.getElementById('configForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConfig();
        });

        // Resume upload
        document.getElementById('uploadResumeBtn').addEventListener('click', () => {
            this.uploadResume();
        });

        // Refresh applications
        document.getElementById('refreshApplications').addEventListener('click', () => {
            this.loadApplications();
        });

        // Status filter
        document.getElementById('statusFilter').addEventListener('change', () => {
            this.loadApplications();
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
            if (button.dataset.tab === tabName) {
                button.classList.add('active');
            }
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;

        // Load data for specific tabs
        if (tabName === 'applications') {
            this.loadApplications();
        } else if (tabName === 'config') {
            this.populateConfigForm();
        }
    }

    showStopButton() {
        document.getElementById('startSearch').style.display = 'none';
        document.getElementById('startApply').style.display = 'none';
        document.getElementById('stopProcess').style.display = 'inline-flex';
    }

    hideStopButton() {
        document.getElementById('startSearch').style.display = 'inline-flex';
        document.getElementById('startApply').style.display = 'inline-flex';
        document.getElementById('stopProcess').style.display = 'none';
    }

    // Activity Log
    addActivityLog(message, type = 'info') {
        const log = document.getElementById('activityLog');
        const item = document.createElement('div');
        item.className = `activity-item ${type}`;

        const time = new Date().toLocaleTimeString();
        item.innerHTML = `
            <div class="activity-time">${time}</div>
            <div class="activity-message">${message}</div>
        `;

        log.insertBefore(item, log.firstChild);

        // Keep only last 50 items
        while (log.children.length > 50) {
            log.removeChild(log.lastChild);
        }
    }

    // API Calls
    async apiCall(endpoint, method = 'GET', body = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.addActivityLog(`API error: ${error.message}`, 'error');
            throw error;
        }
    }

    async loadConfig() {
        try {
            this.config = await this.apiCall('/api/config');
            console.log('Config loaded:', this.config);
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    }

    async loadStatistics() {
        try {
            const stats = await this.apiCall('/api/statistics');

            document.getElementById('totalApplications').textContent =
                stats.total_applications || 0;
            document.getElementById('todayApplications').textContent =
                stats.applications_today || 0;
            document.getElementById('successRate').textContent =
                stats.success_rate ? `${stats.success_rate}%` : '0%';
            document.getElementById('avgMatchScore').textContent =
                stats.average_match_score ? stats.average_match_score.toFixed(1) : '0';
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }

    async loadApplications() {
        try {
            const statusFilter = document.getElementById('statusFilter').value;
            let applications = await this.apiCall('/api/applications?limit=100');

            // Filter by status if selected
            if (statusFilter) {
                applications = applications.filter(app => app.status === statusFilter);
            }

            const listContainer = document.getElementById('applicationsList');
            listContainer.innerHTML = '';

            if (applications.length === 0) {
                listContainer.innerHTML = '<p>No applications found.</p>';
                return;
            }

            applications.forEach(app => {
                const card = document.createElement('div');
                card.className = 'application-card';

                const date = app.applied_at ?
                    new Date(app.applied_at).toLocaleDateString() : 'N/A';

                card.innerHTML = `
                    <div class="application-header">
                        <div>
                            <div class="job-title">${app.job_title}</div>
                            <div class="job-company">${app.company}</div>
                            <div class="job-location">${app.location}</div>
                        </div>
                        <div>
                            <div class="application-status ${app.status}">${app.status}</div>
                            ${app.match_score ? `<div class="match-score">${app.match_score}/100</div>` : ''}
                        </div>
                    </div>
                    <div class="application-date">Applied: ${date}</div>
                    <div class="application-date">Platform: ${app.platform}</div>
                    ${app.job_url ? `<a href="${app.job_url}" target="_blank" class="btn btn-secondary" style="margin-top: 10px;">View Job</a>` : ''}
                `;

                listContainer.appendChild(card);
            });
        } catch (error) {
            console.error('Failed to load applications:', error);
        }
    }

    async submitSearch() {
        const jobTitles = document.getElementById('jobTitles').value
            .split(',').map(s => s.trim()).filter(s => s);
        const locations = document.getElementById('locations').value
            .split(',').map(s => s.trim()).filter(s => s);
        const platforms = Array.from(document.querySelectorAll('input[name="platform"]:checked'))
            .map(cb => cb.value);
        const includeKeywords = document.getElementById('includeKeywords').value
            .split(',').map(s => s.trim()).filter(s => s);
        const excludeKeywords = document.getElementById('excludeKeywords').value
            .split(',').map(s => s.trim()).filter(s => s);

        if (jobTitles.length === 0 || locations.length === 0 || platforms.length === 0) {
            alert('Please fill in job titles, locations, and select at least one platform.');
            return;
        }

        try {
            const result = await this.apiCall('/api/search', 'POST', {
                job_titles: jobTitles,
                locations: locations,
                platforms: platforms,
                keywords: includeKeywords.length > 0 ? includeKeywords : null,
                exclude_keywords: excludeKeywords.length > 0 ? excludeKeywords : null
            });

            this.addActivityLog('Job search started', 'success');
            this.switchTab('dashboard');

            // Show search results section
            document.getElementById('searchResults').style.display = 'block';
            document.getElementById('jobsList').innerHTML = '';
        } catch (error) {
            this.addActivityLog('Failed to start job search', 'error');
        }
    }

    addJobToList(job) {
        const jobsList = document.getElementById('jobsList');
        const card = document.createElement('div');
        card.className = 'job-card';

        card.innerHTML = `
            <div class="job-header">
                <div>
                    <div class="job-title">${job.title}</div>
                    <div class="job-company">${job.company}</div>
                    <div class="job-location">${job.location}</div>
                </div>
            </div>
            <div class="job-description">${job.description.substring(0, 200)}...</div>
            <div class="job-actions">
                <a href="${job.job_url}" target="_blank" class="btn btn-secondary">View Job</a>
            </div>
        `;

        jobsList.insertBefore(card, jobsList.firstChild);
    }

    async startApplicationProcess() {
        const maxApplications = parseInt(document.getElementById('maxApplications')?.value) || 20;
        const applicationDelay = parseInt(document.getElementById('applicationDelay')?.value) || 30;
        const autoSubmit = document.getElementById('autoSubmit')?.checked || false;

        if (!confirm(`Start automatic job applications?\n\nMax applications: ${maxApplications}\nAuto-submit: ${autoSubmit ? 'Yes' : 'No (manual approval)'}`)) {
            return;
        }

        try {
            await this.apiCall('/api/apply', 'POST', {
                auto_submit: autoSubmit,
                max_applications: maxApplications,
                application_delay: applicationDelay
            });

            this.addActivityLog('Application process started', 'success');
        } catch (error) {
            this.addActivityLog('Failed to start application process', 'error');
        }
    }

    async stopProcess() {
        try {
            await this.apiCall('/api/stop', 'POST');
            this.addActivityLog('Stop signal sent', 'warning');
        } catch (error) {
            this.addActivityLog('Failed to stop process', 'error');
        }
    }

    async exportData() {
        try {
            window.open('/api/export?format=csv', '_blank');
            this.addActivityLog('Exporting data...', 'success');
        } catch (error) {
            this.addActivityLog('Failed to export data', 'error');
        }
    }

    populateConfigForm() {
        if (!this.config) return;

        // Personal info
        if (this.config.personal_info) {
            document.getElementById('fullName').value = this.config.personal_info.name || '';
            document.getElementById('email').value = this.config.personal_info.email || '';
            document.getElementById('phone').value = this.config.personal_info.phone || '';
        }

        // Application settings
        document.getElementById('maxApplications').value = this.config.max_applications_per_day || 20;
        document.getElementById('autoSubmit').checked = this.config.auto_submit || false;
        document.getElementById('headless').checked = this.config.headless || false;
    }

    async saveConfig() {
        const updates = {
            personal_info: {
                name: document.getElementById('fullName').value,
                email: document.getElementById('email').value,
                phone: document.getElementById('phone').value,
            },
            max_applications_per_day: parseInt(document.getElementById('maxApplications').value),
            auto_submit: document.getElementById('autoSubmit').checked,
            headless: document.getElementById('headless').checked,
        };

        try {
            await this.apiCall('/api/config', 'POST', updates);
            this.addActivityLog('Configuration saved successfully', 'success');
            await this.loadConfig();
        } catch (error) {
            this.addActivityLog('Failed to save configuration', 'error');
        }
    }

    async uploadResume() {
        const fileInput = document.getElementById('resumeUpload');
        const file = fileInput.files[0];

        if (!file) {
            alert('Please select a resume file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload-resume', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const result = await response.json();
            document.getElementById('resumeStatus').textContent =
                `Resume uploaded successfully: ${result.file_path}`;
            this.addActivityLog('Resume uploaded and parsed', 'success');
        } catch (error) {
            document.getElementById('resumeStatus').textContent =
                `Failed to upload resume: ${error.message}`;
            this.addActivityLog('Failed to upload resume', 'error');
        }
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AutoJobApplierApp();
});
