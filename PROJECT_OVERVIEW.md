# Website Monitoring and Reporting System

A comprehensive solution for monitoring multiple websites with authentication support, custom reporting, notifications, and task scheduling.

## 🚀 Features

### ✅ Core Monitoring
- **Multi-website monitoring** - Monitor multiple websites simultaneously
- **Performance metrics** - Response time, status codes, content size tracking
- **Content validation** - Check for expected content on pages
- **Custom checks** - Extensible system for custom validation rules
- **Screenshot capture** - Automated website screenshots using Selenium

### ✅ Authentication System
- **Multi-auth support** - HTTP Basic, Bearer Token, Form-based login
- **Session management** - Intelligent session reuse and persistence
- **Secure storage** - Encrypted credential storage
- **Auto re-authentication** - Automatic session renewal

### ✅ File Management
- **File downloads** - Download files from specified URLs
- **Variable system** - Store and reuse downloaded files and screenshots
- **Automatic cleanup** - Configurable retention policies

### ✅ Reporting & Notifications
- **HTML reports** - Beautiful, responsive HTML reports
- **JSON exports** - Machine-readable data exports
- **Email notifications** - SMTP-based email alerts and reports
- **Webhook support** - HTTP webhook notifications (Slack, Discord, Teams)
- **Custom templates** - Customizable report templates

### ✅ Task Scheduling
- **Automated monitoring** - Schedule monitoring checks
- **Report generation** - Automated daily/weekly reports
- **File cleanup** - Scheduled cleanup of old files
- **Flexible scheduling** - Cron-like scheduling expressions

### ✅ Modern GUI Interface
- **PyQt5-based** - Modern, responsive graphical interface
- **Website management** - Easy website configuration
- **Real-time monitoring** - Live monitoring results display
- **Configuration dialogs** - User-friendly settings management

### ✅ Configuration & Security
- **YAML configuration** - Human-readable configuration files
- **Encryption** - Secure storage of sensitive data
- **Logging** - Comprehensive logging with rotation
- **Modular design** - Clean, extensible architecture

## 📁 Project Structure

```
monitor-webhtml/
├── main.py                    # Application entry point
├── demo.py                    # Demo/preview application
├── requirements.txt           # Python dependencies
├── config/                    # Configuration management
│   ├── config.yaml           # Default configuration
│   └── settings.py           # Configuration classes
├── core/                      # Core monitoring functionality
│   ├── monitor.py            # Main monitoring engine
│   ├── auth.py               # Authentication management
│   ├── screenshot.py         # Screenshot capture
│   ├── downloader.py         # File download functionality
│   └── variables.py          # Variable management system
├── gui/                       # PyQt5 GUI interface
│   ├── main_window.py        # Main application window
│   ├── dialogs/              # Configuration dialogs
│   │   ├── website_config.py # Website configuration
│   │   └── notification_config.py # Notification settings
│   └── widgets/              # Custom widgets
│       └── monitoring_widget.py # Monitoring display
├── reports/                   # Report generation
│   ├── generator.py          # Report generator
│   └── templates/            # Report templates
├── notifications/             # Notification system
│   ├── email.py              # Email notifications
│   └── webhook.py            # Webhook notifications
├── scheduling/                # Task scheduling
│   └── scheduler.py          # Task scheduler
├── utils/                     # Utility functions
│   ├── logger.py             # Logging utilities
│   ├── crypto.py             # Encryption utilities
│   └── helpers.py            # Helper functions
├── data/                      # Data storage
│   ├── screenshots/          # Screenshot storage
│   ├── downloads/            # Downloaded files
│   ├── reports/              # Generated reports
│   └── logs/                 # Log files
└── tests/                     # Test suite
    ├── test_basic.py         # Basic functionality tests
    └── test_simple.py        # Simplified tests
```

## 🛠 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd monitor-webhtml
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome/Chromium for screenshots:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install chromium-browser
   
   # Or download Chrome from https://www.google.com/chrome/
   ```

## 🚀 Quick Start

### 1. Run the Demo
```bash
python demo.py
```

### 2. Run the Full Application
```bash
python main.py
```

### 3. Configuration
Edit `config/config.yaml` to customize settings:

```yaml
monitoring:
  check_interval: 300        # Check every 5 minutes
  request_timeout: 30        # 30 second timeout
  screenshot:
    enabled: true
    width: 1920
    height: 1080

notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender_email: "your-email@gmail.com"
    sender_password: "your-password"
```

## 💻 Usage Examples

### Adding a Website for Monitoring

```python
from core.monitor import WebsiteMonitor, WebsiteConfig

monitor = WebsiteMonitor()

# Basic website monitoring
website_config = WebsiteConfig(
    name="My Website",
    url="https://example.com",
    check_interval=300,
    take_screenshot=True
)

monitor.add_website(website_config)
```

### Authentication Examples

```python
# HTTP Basic Authentication
auth_config = {
    'username': 'admin',
    'password': 'secret123'
}

website_config = WebsiteConfig(
    name="Protected Site",
    url="https://protected.example.com",
    auth_type="basic",
    auth_config=auth_config
)

# Form-based Authentication
form_auth_config = {
    'login_url': 'https://example.com/login',
    'username': 'admin',
    'password': 'secret123',
    'username_field': 'email',
    'password_field': 'password'
}

website_config = WebsiteConfig(
    name="Form Login Site",
    url="https://example.com/dashboard",
    auth_type="form",
    auth_config=form_auth_config
)
```

### Custom Checks

```python
from core.monitor import CustomCheck

# Check for specific text content
content_check = CustomCheck(
    name="Welcome Message",
    type="text_contains",
    target="Welcome to our website",
    variable_name="welcome_found"
)

website_config.custom_checks.append(content_check)
```

### Report Generation

```python
from reports.generator import ReportGenerator

generator = ReportGenerator()

# Generate HTML report
report_path = generator.generate_html_report(
    results=monitoring_results,
    template_name="default"
)

# Generate JSON report
json_path = generator.generate_json_report(
    results=monitoring_results,
    include_summary=True
)
```

### Email Notifications

```python
from notifications.email import EmailNotifier

notifier = EmailNotifier()

# Send alert for failed monitoring
notifier.send_alert(
    result=failed_result,
    recipients=["admin@example.com"]
)

# Send recovery notification
notifier.send_recovery_notification(
    result=success_result,
    recipients=["admin@example.com"]
)
```

## 🔧 Configuration Options

### Monitoring Settings
- `check_interval`: How often to check websites (seconds)
- `request_timeout`: HTTP request timeout (seconds)
- `max_concurrent`: Maximum concurrent monitoring tasks
- `screenshot`: Screenshot configuration

### Authentication Settings
- `session_timeout`: Session validity period (seconds)
- `auto_relogin`: Automatically re-authenticate on session expiry
- `encryption_key`: Key for encrypting stored credentials

### Report Settings
- `output_dir`: Directory for generated reports
- `default_template`: Default report template name
- `formats`: Supported report formats (html, docx)

### Notification Settings
- `email`: SMTP email configuration
- `webhook`: HTTP webhook configuration

## 📊 Monitoring Features

### Website Health Checks
- **HTTP Status Monitoring** - Track response codes
- **Performance Monitoring** - Measure response times
- **Content Validation** - Verify expected content
- **SSL Certificate Monitoring** - Check certificate expiry
- **Availability Tracking** - Monitor uptime/downtime

### Custom Monitoring Rules
- **XPath Selectors** - Extract specific page elements
- **CSS Selectors** - Query page structure
- **Regular Expressions** - Pattern matching in content
- **Custom Variables** - Store extracted values

### Data Collection
- **Screenshots** - Visual monitoring of pages
- **File Downloads** - Download and monitor files
- **Performance Metrics** - Response time, content size
- **Historical Data** - Track changes over time

## 🔔 Notification Types

### Email Notifications
- **Failure Alerts** - Immediate notifications for failures
- **Recovery Notifications** - Alerts when services recover
- **Scheduled Reports** - Daily/weekly summary reports
- **Custom Templates** - Customizable email templates

### Webhook Notifications
- **Real-time Alerts** - HTTP POST notifications
- **Slack Integration** - Formatted Slack messages
- **Discord Integration** - Discord webhook support
- **Teams Integration** - Microsoft Teams notifications

## 📅 Scheduling

### Automated Tasks
- **Monitoring Checks** - Regular website monitoring
- **Report Generation** - Scheduled report creation
- **File Cleanup** - Automatic cleanup of old files
- **Health Checks** - System health monitoring

### Schedule Expressions
- `*/5 * * * *` - Every 5 minutes
- `0 9 * * *` - Daily at 9 AM
- `0 8 * * 1` - Weekly on Monday at 8 AM
- `0 2 * * *` - Daily at 2 AM

## 🧪 Testing

Run the test suite:

```bash
# Run simplified tests (no heavy dependencies)
python tests/test_simple.py

# Run full test suite (requires all dependencies)
python tests/test_basic.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` directory
- Review the example configurations in `config/`

## 🔮 Future Enhancements

- **Database Integration** - PostgreSQL/MySQL support
- **REST API** - Web API for external integrations
- **Docker Support** - Containerized deployment
- **Grafana Integration** - Advanced dashboards
- **Mobile App** - Mobile monitoring interface
- **Advanced Analytics** - Trend analysis and predictions

---

**Website Monitoring and Reporting System** - A comprehensive, modern solution for website monitoring with powerful reporting and notification capabilities.