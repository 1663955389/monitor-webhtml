# Website Monitoring and Reporting System

This project provides multiple solutions for website monitoring:

## Ansible-Based Proxy & Website Monitoring (NEW!)

A complete Ansible solution for monitoring multiple HTTP/HTTPS proxies by testing connectivity to various websites through each proxy. Features include:

- **Configuration-driven monitoring**: Easy YAML configuration for proxies and websites
- **Proxy support**: Tests HTTP and HTTPS connections through different proxies
- **Parallel execution**: Uses Ansible's built-in parallelism for efficient testing
- **Multiple output formats**: JSON logs and HTML reports
- **Email notifications**: Optional email alerts with HTML reports
- **Comprehensive metrics**: Status codes, latency, retry counts, error messages

### Quick Start

```bash
# Install Ansible
pip install ansible

# Run with default configuration
ansible-playbook -i inventory playbook.yml

# Run with custom configuration  
ansible-playbook -i inventory playbook.yml -e "@config.yml"

# View results
open /tmp/monitoring_report.html
```

See [README-ansible.md](README-ansible.md) for complete documentation.

## Legacy PyQt5 Application (Original)

The original design included a PyQt5 GUI application with features such as:
- Multi-website monitoring with authentication
- Custom report generation (HTML/WORD)
- Screenshot capture and file download
- Email/Webhook notifications
- Task scheduling
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
