# Website Monitoring and Reporting System

A comprehensive, modern solution for monitoring multiple websites with advanced features including authentication, custom reporting, notifications, task scheduling, and a PyQt5 graphical interface.

## 🌟 Key Features

- ✅ **Multi-website monitoring** with performance metrics and content validation
- ✅ **Multiple authentication methods** (HTTP Basic, Bearer Token, Form Login)
- ✅ **Screenshot capture** and file download capabilities
- ✅ **Custom report generation** (HTML/JSON) with templating system
- ✅ **Email and webhook notifications** (Slack, Discord, Teams support)
- ✅ **Task scheduling** with automated cleanup and reporting
- ✅ **Modern PyQt5 GUI** with real-time monitoring displays
- ✅ **Variable management system** for dynamic data handling
- ✅ **Secure configuration** with encrypted credential storage
- ✅ **Comprehensive logging** with automatic rotation and cleanup

## 🚀 Quick Start

### Demo Mode (No Dependencies Required)
```bash
python demo.py
```

### Full Application
```bash
pip install -r requirements.txt
python main.py
```

## 📊 Architecture

The system follows a modular architecture with clear separation of concerns:

- **Core Engine** - Website monitoring, authentication, and data collection
- **GUI Interface** - PyQt5-based modern user interface
- **Report System** - Flexible report generation with custom templates
- **Notification System** - Multi-channel notifications (email, webhooks)
- **Scheduling System** - Automated task execution and cleanup
- **Configuration Management** - YAML-based configuration with encryption

## 🛠 Technology Stack

- **Python 3.12+** - Main development language
- **PyQt5** - Modern GUI framework
- **aiohttp** - Async HTTP client for monitoring
- **Selenium** - Web automation for screenshots
- **Jinja2** - Template engine for reports
- **Cryptography** - Secure credential storage
- **YAML** - Human-readable configuration

## 📁 Project Structure

```
monitor-webhtml/
├── main.py                    # Application entry point
├── demo.py                    # Demo application
├── config/                    # Configuration management
├── core/                      # Core monitoring functionality
├── gui/                       # PyQt5 GUI interface
├── reports/                   # Report generation system
├── notifications/             # Email & webhook notifications
├── scheduling/                # Task scheduling system
├── utils/                     # Utility functions and helpers
├── data/                      # Runtime data storage
└── tests/                     # Test suite
```

## 🔧 Configuration

The system uses YAML configuration files for easy customization:

```yaml
monitoring:
  check_interval: 300          # 5 minutes
  request_timeout: 30
  screenshot:
    enabled: true
    width: 1920
    height: 1080

notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    sender_email: "admin@example.com"
  webhook:
    enabled: true
    url: "https://hooks.slack.com/..."

scheduling:
  enabled: true
  default_schedule: "0 */6 * * *"  # Every 6 hours
```

## 📈 Monitoring Capabilities

- **HTTP Status Monitoring** - Track response codes and errors
- **Performance Metrics** - Response time, content size analysis
- **Content Validation** - Verify expected text and elements
- **Screenshot Capture** - Visual monitoring with Selenium
- **File Downloads** - Monitor and download specific files
- **Custom Checks** - Extensible validation system
- **Authentication Support** - Handle protected websites
- **Variable System** - Store and reuse dynamic data

## 📧 Notification Features

### Email Notifications
- Immediate failure alerts
- Recovery notifications
- Scheduled reports with attachments
- HTML templates with customization

### Webhook Support
- Real-time HTTP notifications
- Slack integration with rich formatting
- Discord webhook support
- Microsoft Teams integration
- Custom payload formatting

## 📊 Reporting System

- **HTML Reports** - Beautiful, responsive reports with charts
- **JSON Exports** - Machine-readable data for integrations
- **Custom Templates** - Jinja2-based template system
- **Variable Substitution** - Dynamic content generation
- **Automated Generation** - Scheduled daily/weekly reports

## 🗓 Task Scheduling

- **Monitoring Checks** - Automated website monitoring
- **Report Generation** - Scheduled report creation and delivery
- **File Cleanup** - Automatic cleanup of old files and logs
- **Health Monitoring** - System health checks and maintenance

## 🔒 Security Features

- **Credential Encryption** - Secure storage of passwords and tokens
- **Session Management** - Intelligent session reuse and renewal
- **Secure Configuration** - Encrypted sensitive settings
- **Access Control** - Authentication and authorization support

## 🧪 Testing

The project includes comprehensive tests:

```bash
# Basic functionality tests
python tests/test_simple.py

# Full test suite (requires dependencies)
python tests/test_basic.py
```

## 📖 Documentation

- See `PROJECT_OVERVIEW.md` for detailed technical documentation
- Configuration examples in `config/config.yaml`
- API documentation in code comments
- Usage examples in the GUI and demo applications

## 🎯 Use Cases

- **Website Uptime Monitoring** - Monitor business-critical websites
- **Performance Tracking** - Track website performance over time
- **Content Monitoring** - Verify specific content is present
- **API Monitoring** - Monitor REST APIs and web services
- **Compliance Checking** - Automated compliance verification
- **Change Detection** - Monitor for unexpected changes

## 🚧 Development Status

This is a complete implementation featuring:

- ✅ Full modular architecture
- ✅ Configuration management system
- ✅ Core monitoring engine with authentication
- ✅ Screenshot and file download capabilities
- ✅ Variable management system
- ✅ PyQt5 GUI framework with dialogs and widgets
- ✅ Report generation system with templates
- ✅ Email and webhook notification systems
- ✅ Task scheduling with automated cleanup
- ✅ Comprehensive logging and utilities
- ✅ Security features and encryption
- ✅ Test suite and documentation

The system is ready for production use with proper dependency installation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for reliable website monitoring**
