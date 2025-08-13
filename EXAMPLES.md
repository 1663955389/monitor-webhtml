# Sample Ansible Command Output

This file shows example commands and their expected outputs for the proxy monitoring system.

## Basic Monitoring Command
```bash
ansible-playbook playbooks/monitor-proxies.yml
```

## Expected Output Structure
```
PLAY [Monitor Proxy Status and Website Connectivity] *******************

TASK [Gathering Facts] ************************************************
ok: [localhost]

TASK [Display monitoring start information] **************************
ok: [localhost] => {
    "msg": [
        "Starting proxy monitoring at 2024-01-15T10:30:00Z",
        "Log directory: /home/runner/work/monitor-webhtml/monitor-webhtml/logs",
        "Alert thresholds: Response time < 5000ms, Success rate > 70%"
    ]
}

TASK [proxy-monitor : Test each proxy against all websites] **********
included: test_proxy.yml for localhost => (item=proxy1)
included: test_proxy.yml for localhost => (item=proxy2)

TASK [Display monitoring summary] ************************************
ok: [localhost] => {
    "msg": [
        "Monitoring completed at 2024-01-15T10:35:00Z",
        "Total tests performed: 8",
        "Successful tests: 6",
        "Overall success rate: 75.0%",
        "Failed proxies: 1"
    ]
}
```

## Generated Log File Example
The system generates logs in `/logs/proxy_monitor.log` with detailed results for each proxy and website test.

## HTML Email Alert
When failures are detected, an HTML email is generated and sent with:
- Visual status indicators
- Detailed test results table
- Response times and error messages
- Recommended actions

## Inventory Configuration Example
The `inventory/hosts.yml` contains proxy definitions:
```yaml
proxy_servers:
  hosts:
    proxy1:
      proxy_url: "http://proxy1.example.com:8080"
      proxy_username: "user1" 
      proxy_password: "pass1"
      enabled: true
```

## Customization Examples
- Modify alert thresholds in `group_vars/all.yml`
- Add/remove test websites in inventory
- Configure email settings for alerts
- Adjust log formats (text/JSON)