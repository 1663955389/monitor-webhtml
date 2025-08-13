# Ansible Proxy & Website Monitoring

An Ansible-based solution for monitoring multiple HTTP/HTTPS proxies by testing connectivity to various websites through each proxy. The system captures metrics, generates reports, and supports email notifications.

## Features

- **Configuration-driven monitoring**: Easy YAML configuration for proxies and websites
- **Proxy support**: Tests HTTP and HTTPS connections through different proxies
- **Parallel execution**: Uses Ansible's built-in parallelism for efficient testing
- **Multiple output formats**: 
  - JSON logs for programmatic consumption
  - HTML reports for human-readable results
  - Email notifications (optional)
- **Comprehensive metrics**: Status codes, latency, retry counts, error messages
- **Flexible thresholds**: Per-site latency and status code overrides

## Quick Start

1. **Install Ansible** (if not already installed):
   ```bash
   pip install ansible
   ```

2. **Run with default configuration**:
   ```bash
   ansible-playbook -i inventory playbook.yml
   ```

3. **Run with custom configuration**:
   ```bash
   ansible-playbook -i inventory playbook.yml -e "@config.yml"
   ```

4. **View results**:
   - HTML Report: `/tmp/monitoring_report.html`
   - JSON Log: `/tmp/monitoring_results.json`

## Configuration

### Basic Configuration Structure

```yaml
monitor_config:
  proxies:
    - name: "corporate_proxy"
      http: "http://proxy.company.com:8080"
      https: "https://proxy.company.com:8080"  # Optional
      enabled: true
    - name: "backup_proxy"
      http: "http://backup-proxy.company.com:3128"
      enabled: false  # Disabled for testing
      
  sites:
    - name: "Company Website"
      url: "https://www.company.com"
      validate_certs: true
      max_latency_ms: 3000  # Optional override
      allowed_status_codes: [200, 301, 302]  # Optional override
    - name: "Internal API"
      url: "http://internal.company.com/api/health"
      validate_certs: false
      retries: 5  # Optional override

monitor_settings:
  retries: 3
  timeout_seconds: 30
  max_latency_ms: 5000
  allowed_status_codes: [200, 201, 202, 301, 302]
  parallel_limit: 10

output_settings:
  html_report_path: "/tmp/monitoring_report.html"
  json_log_path: "/tmp/monitoring_results.json"
  send_email: false
  email_settings:
    smtp_server: "mail.company.com"
    smtp_port: 587
    from_email: "monitoring@company.com"
    to_emails: ["admin@company.com"]
    subject: "Proxy Monitoring Report"
```

### Proxy Configuration

- **name**: Descriptive name for the proxy
- **http**: HTTP proxy URL (required)
- **https**: HTTPS proxy URL (optional, defaults to http value)
- **enabled**: Boolean flag to enable/disable proxy testing

### Site Configuration

- **name**: Descriptive name for the website
- **url**: Target URL to test
- **validate_certs**: Whether to validate SSL certificates (default: true)
- **max_latency_ms**: Maximum acceptable latency in milliseconds (optional override)
- **allowed_status_codes**: List of acceptable HTTP status codes (optional override)
- **retries**: Number of retry attempts (optional override)
- **timeout_seconds**: Request timeout (optional override)

## Running Tests

### Test with Direct Connections (No Proxy)

```bash
# Create a test configuration
cat > direct-test.yml << EOF
monitor_config:
  proxies:
    - name: "direct_connection"
      http: ""  # Empty for direct connection
      enabled: true
  sites:
    - name: "Google"
      url: "https://www.google.com"
      validate_certs: true
EOF

# Run the test
ansible-playbook -i inventory playbook.yml -e "@direct-test.yml"
```

### Test with Real Proxies

```bash
# Create a proxy test configuration
cat > proxy-test.yml << EOF
monitor_config:
  proxies:
    - name: "company_proxy"
      http: "http://your-proxy.company.com:8080"
      https: "https://your-proxy.company.com:8080"
      enabled: true
  sites:
    - name: "External Site"
      url: "https://www.google.com"
      max_latency_ms: 5000
EOF

# Run the test
ansible-playbook -i inventory playbook.yml -e "@proxy-test.yml"
```

## Output Formats

### JSON Log Format

```json
{
  "summary": {
    "total_tests": 4,
    "passed_tests": 2,
    "failed_tests": 2,
    "success_rate": 50.0,
    "duration_seconds": 15,
    "start_time": "1234567890",
    "end_time": "1234567905"
  },
  "results": [
    {
      "proxy": {
        "name": "corporate_proxy",
        "http": "http://proxy.company.com:8080",
        "https": "https://proxy.company.com:8080"
      },
      "site": {
        "name": "Company Website",
        "url": "https://www.company.com"
      },
      "test_info": {
        "timestamp": "2023-12-01T10:30:00Z",
        "duration_ms": 1250.5,
        "retries_attempted": 1
      },
      "results": {
        "status_code": "200",
        "status_ok": true,
        "latency_ok": true,
        "overall_success": true,
        "error_message": ""
      },
      "thresholds": {
        "max_latency_ms": "3000",
        "allowed_status_codes": [200, 301, 302],
        "timeout_seconds": "30"
      }
    }
  ],
  "generated_at": "2023-12-01T10:30:15Z"
}
```

### HTML Report

The HTML report provides a visual dashboard with:
- Summary statistics with color-coded success rates
- Detailed results table with status indicators
- Error messages and performance metrics
- Responsive design for different screen sizes

## Email Notifications

Enable email notifications by setting:

```yaml
output_settings:
  send_email: true
  email_settings:
    smtp_server: "your-smtp-server.com"
    smtp_port: 587
    from_email: "monitoring@yourcompany.com"
    to_emails:
      - "admin@yourcompany.com"
      - "ops-team@yourcompany.com"
    subject: "Proxy Monitoring Report - {{ ansible_date_time.date }}"
```

## Advanced Usage

### Custom Ansible Inventory

```ini
[monitoring_servers]
server1 ansible_host=192.168.1.10
server2 ansible_host=192.168.1.11

[monitoring_servers:vars]
ansible_user=monitoring
ansible_ssh_private_key_file=/path/to/key
```

### Running on Multiple Hosts

```bash
ansible-playbook -i production_inventory playbook.yml -e "@config.yml"
```

### Scheduled Monitoring with Cron

```bash
# Add to crontab for hourly monitoring
0 * * * * cd /path/to/monitor-webhtml && ansible-playbook -i inventory playbook.yml -e "@config.yml"
```

## Troubleshooting

### Common Issues

1. **DNS Resolution Failures**: Check network connectivity and DNS settings
2. **Proxy Authentication**: Ensure proxy credentials are included in URL (http://user:pass@proxy:port)
3. **SSL Certificate Issues**: Set `validate_certs: false` for sites with self-signed certificates
4. **Timeout Issues**: Increase `timeout_seconds` and `max_latency_ms` for slow connections

### Debug Mode

Run with verbose output for troubleshooting:

```bash
ansible-playbook -i inventory playbook.yml -e "@config.yml" -vvv
```

## File Structure

```
.
├── playbook.yml                    # Main Ansible playbook
├── inventory                       # Ansible inventory file
├── ansible.cfg                     # Ansible configuration
├── config.yml                      # Example configuration
├── roles/
│   └── monitor_proxies/
│       ├── defaults/main.yml       # Default variables
│       ├── tasks/main.yml          # Main monitoring tasks
│       ├── tasks/monitor_single_test.yml  # Individual test logic
│       └── templates/report.html.j2  # HTML report template
└── README.md                       # This file
```

## License

MIT License - See original repository for details.