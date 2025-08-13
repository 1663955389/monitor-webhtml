# Website Monitoring and Reporting System

This project provides multiple solutions for website monitoring:

## Ansible-Based Proxy & Website Monitoring

A complete Ansible solution for monitoring multiple HTTP/HTTPS proxies by testing connectivity to various websites through each proxy. Features include:

- **Configuration-driven monitoring**: Easy YAML configuration for proxies and websites
- **Proxy support**: Tests HTTP and HTTPS connections through different proxies
- **Parallel execution**: Uses Ansible's built-in parallelism for efficient testing
- **Multiple output formats**: JSON logs and HTML reports
- **Local timezone support**: JSON filenames and timestamps use configured timezone
- **Per-proxy summary statistics**: Detailed metrics and success rates per proxy
- **Email notifications**: Optional email alerts with HTML reports
- **Comprehensive metrics**: Status codes, latency, retry counts, error messages

### New Features (Enhanced Version)

#### 1. Local Timezone JSON File Naming
- JSON files now use local timezone timestamps in the filename format: `proxy_monitor_YYYYMMDD_HHMMSS_local.json`
- Configurable timezone via `monitor.timezone` (defaults to Asia/Shanghai)
- Local timestamp included in JSON content as `generated_at_local`

#### 2. Per-Proxy Summary Statistics
- New proxy summary table in HTML reports showing:
  - Total checks per proxy
  - Number of failures per proxy
  - Number of slow responses per proxy
  - Average latency (ms) per proxy
  - Success rate percentage per proxy
- Color-coded rows: red for failures, amber for slow responses, green for 100% success
- Comprehensive proxy_summary data included in JSON output

### Quick Start

```bash
# Install Ansible
pip install ansible

# Run with default configuration
ansible-playbook -i inventory playbook.yml

# Run with custom configuration  
ansible-playbook -i inventory playbook.yml -e "@config.yml"

# Example with custom timezone
ansible-playbook -i inventory playbook.yml -e "monitor.timezone=Europe/London" -e "@config.yml"

# View results
open /tmp/proxy_monitor_YYYYMMDD_HHMMSS_local.json
open /tmp/monitoring_report.html
```

### Configuration

#### Timezone Configuration
```yaml
monitor:
  timezone: "Asia/Shanghai"  # Default timezone
```

#### Example Configuration with Proxies
```yaml
monitor_config:
  proxies:
    - name: "corporate_proxy"
      http: "http://proxy.company.com:8080"
      https: "https://proxy.company.com:8080"
      enabled: true
    - name: "backup_proxy"
      http: "http://backup-proxy.company.com:3128"
      enabled: true
      
  sites:
    - name: "Company Website"
      url: "https://www.company.com"
      validate_certs: true
      max_latency_ms: 3000
      allowed_status_codes: [200, 301, 302]
    - name: "External API"
      url: "https://api.external-service.com/health"
      validate_certs: true

monitor:
  timezone: "Asia/Shanghai"

monitor_settings:
  retries: 3
  timeout_seconds: 30
  max_latency_ms: 5000
  allowed_status_codes: [200, 201, 202, 301, 302]

output_settings:
  html_report_path: "/tmp/monitoring_report.html"
  json_log_path: "/tmp/monitoring_results.json"
  send_email: false
```

### Output Examples

#### JSON Structure (Enhanced)
```json
{
  "generated_at_local": "2025-08-13T21:56:48",
  "timezone": "Asia/Shanghai",
  "summary": {
    "total_tests": 6,
    "passed_tests": 4,
    "failed_tests": 2,
    "success_rate": 66.67,
    "duration_seconds": 15
  },
  "proxy_summary": [
    {
      "proxy": "corporate_proxy",
      "total": 4,
      "failures": 0,
      "slow": 1,
      "avg_latency_ms": 1250.5,
      "success_rate": 100.0
    }
  ],
  "results": [...]
}
```

#### HTML Report Features
- **Main Summary**: Overall statistics with color-coded success rates
- **代理汇总 (Proxy Summary)**: Per-proxy statistics table with:
  - Color-coded rows based on performance
  - Chinese headers for localization
  - Local timezone display
- **Detailed Results**: Individual test results with full metrics

### Testing Different Timezones

```bash
# Test with different timezones
ansible-playbook -i inventory playbook.yml -e "monitor.timezone=Europe/London"
ansible-playbook -i inventory playbook.yml -e "monitor.timezone=America/New_York" 
ansible-playbook -i inventory playbook.yml -e "monitor.timezone=UTC"
```

The JSON filename will reflect the configured timezone:
- Asia/Shanghai: `proxy_monitor_20250813_215648_local.json`
- Europe/London: `proxy_monitor_20250813_135648_local.json`
- UTC: `proxy_monitor_20250813_135648_local.json`

### File Structure

```
.
├── playbook.yml                    # Main Ansible playbook
├── inventory                       # Ansible inventory file
├── enhanced-test-config.yml        # Enhanced test configuration
├── roles/
│   └── monitor_proxies/
│       ├── defaults/main.yml       # Default variables (includes timezone)
│       ├── tasks/
│       │   ├── main.yml           # Main monitoring tasks (enhanced)
│       │   ├── monitor_single_test.yml  # Individual test logic
│       │   └── calculate_proxy_summary.yml  # Proxy summary calculations
│       └── templates/
│           └── report.html.j2     # HTML report template (enhanced)
└── README.md                      # This file
```

## Legacy PyQt5 Application (Original)

The original design included a PyQt5 GUI application with features such as:
- Multi-website monitoring with authentication
- Custom report generation (HTML/WORD)
- Screenshot capture and file download
- Scheduled monitoring and alerts
- Multi-language support (Chinese/English)
- PyQt5 modern GUI interface
- Async architecture with Python 3.12+

### Legacy Usage

Install dependencies and run:
```bash
pip install -r requirements.txt
python main.py
```

**Note**: The legacy GUI application files are not currently included in this repository. The Ansible solution above provides the core monitoring functionality in a more scalable, automation-friendly format.

## License

This project is licensed under the MIT License.