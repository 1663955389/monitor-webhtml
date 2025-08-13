#!/bin/bash

# Example script demonstrating Ansible proxy monitoring usage
# This script shows how to use the monitoring solution in different scenarios

echo "=== Ansible Proxy & Website Monitoring Demo ==="
echo

# Check if Ansible is installed
if ! command -v ansible-playbook &> /dev/null; then
    echo "Error: Ansible is not installed. Please install it first:"
    echo "pip install ansible"
    exit 1
fi

echo "✓ Ansible is available"

# Create a custom configuration for demonstration
cat > demo-run.yml << 'EOF'
---
monitor_config:
  proxies:
    - name: "direct_connection"
      http: ""  # Direct connection (no proxy)
      enabled: true
    - name: "example_proxy"
      http: "http://proxy.example.com:8080"
      enabled: false  # Disabled for demo
      
  sites:
    - name: "Local Apache Test"
      url: "http://localhost:80"
      validate_certs: false
      max_latency_ms: 5000
      allowed_status_codes: [200, 301, 302, 403, 404, 500, 502, 503]

monitor_settings:
  retries: 2
  timeout_seconds: 10
  max_latency_ms: 10000
  allowed_status_codes: [200, 301, 302, 403, 404, 500, 502, 503]

output_settings:
  html_report_path: "/tmp/demo_report.html"
  json_log_path: "/tmp/demo_results.json"
  send_email: false
EOF

echo "✓ Created demo configuration"

# Run the monitoring
echo
echo "Running Ansible proxy monitoring..."
ansible-playbook -i inventory playbook.yml -e "@demo-run.yml"

# Show results
echo
echo "=== Results ==="
if [ -f "/tmp/demo_results.json" ]; then
    echo "✓ JSON results generated:"
    echo "  File: /tmp/demo_results.json"
    echo "  Summary:"
    python3 -c "
import json
with open('/tmp/demo_results.json', 'r') as f:
    data = json.load(f)
    summary = data['summary']
    print(f'  Total Tests: {summary[\"total_tests\"]}')
    print(f'  Passed: {summary[\"passed_tests\"]}')
    print(f'  Failed: {summary[\"failed_tests\"]}')
    print(f'  Success Rate: {summary[\"success_rate\"]}%')
"
else
    echo "✗ JSON results not found"
fi

if [ -f "/tmp/demo_report.html" ]; then
    echo "✓ HTML report generated: /tmp/demo_report.html"
    echo "  Open the HTML file in your browser to view the detailed report"
else
    echo "✗ HTML report not found"
fi

echo
echo "=== Available Configuration Files ==="
echo "• config.yml - Example production configuration"
echo "• test-config.yml - Basic test configuration"
echo "• demo-config.yml - Demo configuration with examples"
echo "• comprehensive-test.yml - Comprehensive test scenarios"

echo
echo "=== Usage Examples ==="
echo "# Run with default configuration:"
echo "ansible-playbook -i inventory playbook.yml"
echo
echo "# Run with custom configuration:"
echo "ansible-playbook -i inventory playbook.yml -e \"@config.yml\""
echo
echo "# Run with verbose output for debugging:"
echo "ansible-playbook -i inventory playbook.yml -e \"@config.yml\" -vvv"

echo
echo "For complete documentation, see README-ansible.md"

# Cleanup
rm -f demo-run.yml