# Ansible Proxy Monitoring System

A comprehensive Ansible project for monitoring proxy server status and website connectivity through proxies. This system provides automated testing, detailed logging, and HTML email alerts for proxy health monitoring.

## Features

- **Multi-Proxy Monitoring**: Monitor multiple proxy servers simultaneously
- **Website Connectivity Testing**: Test proxy connectivity by accessing multiple websites
- **Health Status Assessment**: Determine proxy health based on HTTP status codes and response times
- **Detailed Logging**: Generate structured logs in multiple formats (text, JSON)
- **HTML Email Alerts**: Send formatted email notifications for proxy failures
- **Configurable Thresholds**: Set custom alert thresholds for response time and success rates
- **Flexible Configuration**: Easy-to-modify inventory and variables files

## Project Structure

```
monitor-webhtml/
├── README.md                          # This documentation
├── ansible.cfg                        # Ansible configuration
├── inventory/
│   └── hosts.yml                      # Proxy servers and test websites
├── group_vars/
│   └── all.yml                        # Global configuration variables
├── playbooks/
│   └── monitor-proxies.yml            # Main monitoring playbook
├── roles/
│   └── proxy-monitor/
│       ├── tasks/
│       │   ├── main.yml               # Main monitoring tasks
│       │   ├── test_proxy.yml         # Individual proxy testing
│       │   └── send_alerts.yml        # Email alert functionality
│       ├── templates/
│       │   ├── email-alert.html.j2   # HTML email template
│       │   └── log-format.j2         # Log format template
│       └── vars/
│           └── main.yml               # Role-specific variables
└── logs/                              # Log output directory
    └── .gitkeep
```

## Quick Start

### Prerequisites

- Ansible 2.9+ installed
- Python 3.6+ with required modules:
  - ansible
  - requests
  - email (for SMTP functionality)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd monitor-webhtml
```

2. Configure your proxy servers and test websites in `inventory/hosts.yml`

3. Update monitoring settings in `group_vars/all.yml`

4. Run the monitoring playbook:
```bash
ansible-playbook playbooks/monitor-proxies.yml
```

## Configuration

### 1. Proxy Configuration (`inventory/hosts.yml`)

Define your proxy servers in the `proxy_servers` group:

```yaml
proxy_servers:
  hosts:
    proxy1:
      ansible_host: localhost
      proxy_url: "http://proxy1.example.com:8080"
      proxy_username: "user1"
      proxy_password: "pass1"
      enabled: true
```

**Parameters:**
- `proxy_url`: The proxy server URL and port
- `proxy_username`: Authentication username (optional)
- `proxy_password`: Authentication password (optional)
- `enabled`: Whether to include this proxy in monitoring

### 2. Test Websites (`inventory/hosts.yml`)

Define test websites in the `test_websites` group:

```yaml
test_websites:
  hosts:
    google:
      test_url: "https://www.google.com"
      expected_status: 200
      timeout: 10
```

**Parameters:**
- `test_url`: The website URL to test
- `expected_status`: Expected HTTP status code
- `timeout`: Request timeout in seconds

### 3. Monitoring Configuration (`group_vars/all.yml`)

#### Alert Thresholds
```yaml
monitoring:
  thresholds:
    max_response_time: 5000  # milliseconds
    max_failure_rate: 30     # percentage
    min_success_rate: 70     # percentage
```

#### Email Configuration
```yaml
email_config:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  smtp_use_tls: true
  smtp_username: "monitor@example.com"
  smtp_password: "your_email_password"
  from_email: "monitor@example.com"
  to_emails:
    - "admin@example.com"
    - "ops@example.com"
```

#### Logging Configuration
```yaml
monitoring:
  logging:
    log_dir: "/path/to/logs"
    log_file: "proxy_monitor.log"
    log_level: "INFO"
    log_format: "detailed"  # options: simple, detailed, json
```

## Usage

### Basic Monitoring

Run a single monitoring cycle:
```bash
ansible-playbook playbooks/monitor-proxies.yml
```

### Verbose Output

Run with verbose output for debugging:
```bash
ansible-playbook playbooks/monitor-proxies.yml -v
```

### Check Only Specific Proxies

Use Ansible limits to test specific proxies:
```bash
ansible-playbook playbooks/monitor-proxies.yml --limit proxy1
```

### Dry Run

Test the configuration without making changes:
```bash
ansible-playbook playbooks/monitor-proxies.yml --check
```

## Monitoring Results

### Log Files

The system generates detailed logs in the specified log directory:

- **Text Format**: Human-readable detailed report
- **JSON Format**: Machine-readable structured data

Example text log output:
```
===============================================================================
PROXY MONITORING REPORT
===============================================================================
Timestamp: 2024-01-15T10:30:00Z

SUMMARY:
--------
Total Proxies Monitored: 3
Healthy Proxies: 2
Unhealthy Proxies: 1
Overall Success Rate: 75.5%
```

### Email Alerts

HTML email alerts are sent when:
- Any proxy fails health checks
- Overall success rate falls below threshold
- Individual proxy success rate falls below threshold

The HTML email includes:
- Monitoring summary with visual indicators
- Detailed proxy status with test results
- Recommended actions for failed proxies
- Response time and status code information

### Console Output

Real-time monitoring information is displayed during execution:
- Proxy test progress
- Success/failure status for each test
- Summary statistics
- Alert notifications

## Advanced Configuration

### Custom Test Patterns

Modify `roles/proxy-monitor/vars/main.yml` to customize:

```yaml
status_codes:
  success: [200, 201, 202, 204, 301, 302, 304]
  warning: [400, 401, 403, 404]
  error: [500, 502, 503, 504, 505]

http_config:
  user_agent: "Ansible-Proxy-Monitor/1.0"
  follow_redirects: true
  validate_certs: false
  max_redirects: 3
```

### Scheduled Monitoring

Set up cron job for automated monitoring:
```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/monitor-webhtml && ansible-playbook playbooks/monitor-proxies.yml >> /var/log/proxy-monitor-cron.log 2>&1
```

### Integration with Monitoring Systems

The JSON log format can be integrated with:
- Prometheus/Grafana for metrics visualization
- ELK Stack for log analysis
- Nagios/Zabbix for alerting
- SIEM systems for security monitoring

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Increase timeout values in inventory
   - Check proxy server accessibility
   - Verify network connectivity

2. **Authentication Failures**
   - Verify proxy credentials
   - Check authentication method compatibility
   - Test proxy access manually

3. **Email Delivery Issues**
   - Verify SMTP server settings
   - Check authentication credentials
   - Test SMTP connectivity
   - Review firewall settings

4. **Permission Errors**
   - Ensure log directory is writable
   - Check file permissions
   - Verify Ansible execution user permissions

### Debug Mode

Enable debug output:
```bash
ansible-playbook playbooks/monitor-proxies.yml -vvv
```

### Log Analysis

Check detailed logs for specific issues:
```bash
tail -f logs/proxy_monitor.log
tail -f logs/ansible.log
```

## Security Considerations

1. **Credential Management**
   - Use Ansible Vault for sensitive data
   - Avoid storing passwords in plain text
   - Consider using environment variables

2. **Network Security**
   - Use secure SMTP connections (TLS/SSL)
   - Validate SSL certificates when appropriate
   - Implement proper firewall rules

3. **Log Security**
   - Secure log file permissions
   - Consider log rotation and retention
   - Avoid logging sensitive information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Review this documentation
- Check the issue tracker
- Submit bug reports with detailed information
- Include log files and configuration (without sensitive data)

## Version History

- **v1.0.0**: Initial release with core monitoring functionality
  - Multi-proxy monitoring
  - Website connectivity testing
  - HTML email alerts
  - Configurable thresholds
  - Multiple log formats