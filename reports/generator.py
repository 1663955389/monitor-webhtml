"""
Report generation system for monitoring results
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Template, Environment, FileSystemLoader

from core.monitor import MonitorResult
from core.variables import VariableManager
from config.settings import config_manager
from utils.helpers import ensure_directory, format_size


class ReportGenerator:
    """Generates monitoring reports in various formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_reports_config()
        self.directories_config = config_manager.get_directories_config()
        
        # Setup reports directory
        self.reports_dir = ensure_directory(self.directories_config.reports)
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        
        # Create default templates if they don't exist
        self.create_default_templates()
    
    def create_default_templates(self):
        """Create default report templates"""
        # HTML template
        html_template_path = self.templates_dir / "default.html"
        if not html_template_path.exists():
            self.create_default_html_template(html_template_path)
        
        # Email template
        email_template_path = self.templates_dir / "email.html"
        if not email_template_path.exists():
            self.create_default_email_template(email_template_path)
    
    def create_default_html_template(self, template_path: Path):
        """Create default HTML report template"""
        template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Monitoring Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header .subtitle {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background-color: #f8f9fa;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 1.1em;
        }
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .danger { color: #dc3545; }
        .info { color: #17a2b8; }
        
        .results {
            padding: 30px;
        }
        .results h2 {
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .result-item {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .result-header {
            padding: 15px 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .result-header.success {
            background-color: #d4edda;
            border-color: #c3e6cb;
        }
        .result-header.failed {
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        .result-body {
            padding: 20px;
        }
        .result-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        .detail-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .detail-label {
            font-weight: bold;
            color: #666;
        }
        .screenshot {
            text-align: center;
            margin-top: 20px;
        }
        .screenshot img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .variables {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        .variables h4 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .variable-item {
            margin: 5px 0;
            padding: 5px 10px;
            background: white;
            border-radius: 3px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .footer {
            background-color: #333;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Website Monitoring Report</h1>
            <div class="subtitle">Generated on {{ report_date }}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Checks</h3>
                <div class="value info">{{ summary.total_checks }}</div>
            </div>
            <div class="summary-card">
                <h3>Successful</h3>
                <div class="value success">{{ summary.successful_checks }}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="value danger">{{ summary.failed_checks }}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value {% if summary.success_rate > 95 %}success{% elif summary.success_rate > 80 %}warning{% else %}danger{% endif %}">
                    {{ "%.1f"|format(summary.success_rate) }}%
                </div>
            </div>
        </div>
        
        <div class="results">
            <h2>Detailed Results</h2>
            {% for result in results %}
            <div class="result-item">
                <div class="result-header {% if result.success %}success{% else %}failed{% endif %}">
                    <div>
                        <strong>{{ result.website_name }}</strong>
                        <span style="margin-left: 10px; font-size: 0.9em; color: #666;">
                            {{ result.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}
                        </span>
                    </div>
                    <div>
                        {% if result.success %}
                            <span class="success">✓ SUCCESS</span>
                        {% else %}
                            <span class="danger">✗ FAILED</span>
                        {% endif %}
                    </div>
                </div>
                <div class="result-body">
                    <div class="result-details">
                        <div class="detail-item">
                            <span class="detail-label">URL:</span>
                            <span>{{ result.url }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Status Code:</span>
                            <span>{{ result.status_code or 'N/A' }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Response Time:</span>
                            <span>{{ "%.2f"|format(result.response_time or 0) }}s</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Content Size:</span>
                            <span>{{ format_size(result.content_size or 0) }}</span>
                        </div>
                    </div>
                    
                    {% if result.error_message %}
                    <div style="color: #dc3545; margin: 10px 0; padding: 10px; background-color: #f8d7da; border-radius: 4px;">
                        <strong>Error:</strong> {{ result.error_message }}
                    </div>
                    {% endif %}
                    
                    {% if result.screenshot_path %}
                    <div class="screenshot">
                        <h4>Screenshot</h4>
                        <img src="{{ result.screenshot_path }}" alt="Website Screenshot" />
                    </div>
                    {% endif %}
                    
                    {% if result.variables %}
                    <div class="variables">
                        <h4>Variables</h4>
                        {% for var_name, var_value in result.variables.items() %}
                        <div class="variable-item">
                            <strong>{{ var_name }}:</strong> {{ var_value|string|truncate(100) }}
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>Generated by Website Monitoring and Reporting System</p>
            <p>Total execution time: {{ summary.total_execution_time }}s</p>
        </div>
    </div>
</body>
</html>'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        self.logger.info(f"Created default HTML template: {template_path}")
    
    def create_default_email_template(self, template_path: Path):
        """Create default email template"""
        template_content = '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">Monitoring Alert</h1>
        <p style="margin: 10px 0 0 0;">{{ alert_type }} - {{ timestamp }}</p>
    </div>
    
    <div style="padding: 20px; background-color: #f9f9f9;">
        <h2 style="color: #333; margin-top: 0;">Summary</h2>
        <p><strong>Website:</strong> {{ website_name }}</p>
        <p><strong>URL:</strong> {{ url }}</p>
        <p><strong>Status:</strong> 
            <span style="color: {% if success %}#28a745{% else %}#dc3545{% endif %};">
                {% if success %}✓ SUCCESS{% else %}✗ FAILED{% endif %}
            </span>
        </p>
        
        {% if error_message %}
        <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; margin: 10px 0;">
            <strong>Error:</strong> {{ error_message }}
        </div>
        {% endif %}
        
        <h3 style="color: #333;">Details</h3>
        <ul style="list-style: none; padding: 0;">
            <li style="margin: 5px 0;"><strong>Response Time:</strong> {{ "%.2f"|format(response_time or 0) }}s</li>
            <li style="margin: 5px 0;"><strong>Status Code:</strong> {{ status_code or 'N/A' }}</li>
            <li style="margin: 5px 0;"><strong>Timestamp:</strong> {{ timestamp }}</li>
        </ul>
    </div>
    
    <div style="background-color: #333; color: white; text-align: center; padding: 15px; font-size: 0.9em;">
        <p style="margin: 0;">Website Monitoring and Reporting System</p>
    </div>
</div>'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        self.logger.info(f"Created default email template: {template_path}")
    
    def generate_html_report(self, results: List[MonitorResult], template_name: str = "default", 
                           variables: Optional[Dict[str, Any]] = None) -> str:
        """Generate HTML report from monitoring results"""
        try:
            # Calculate summary statistics
            summary = self._calculate_summary(results)
            
            # Prepare template variables
            template_vars = {
                'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'results': results,
                'summary': summary,
                'variables': variables or {},
                'format_size': format_size
            }
            
            # Load and render template
            template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = template.render(**template_vars)
            
            # Generate filename and save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_report_{timestamp}.html"
            report_path = self.reports_dir / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Generated HTML report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            raise
    
    def generate_json_report(self, results: List[MonitorResult], include_summary: bool = True) -> str:
        """Generate JSON report from monitoring results"""
        try:
            # Prepare data
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'results': []
            }
            
            # Add summary if requested
            if include_summary:
                report_data['summary'] = self._calculate_summary(results)
            
            # Convert results to dict format
            for result in results:
                result_dict = {
                    'website_name': result.website_name,
                    'url': result.url,
                    'timestamp': result.timestamp.isoformat(),
                    'success': result.success,
                    'status_code': result.status_code,
                    'response_time': result.response_time,
                    'error_message': result.error_message,
                    'content_size': result.content_size,
                    'screenshot_path': result.screenshot_path,
                    'custom_check_results': result.custom_check_results,
                    'downloaded_files': result.downloaded_files,
                    'variables': result.variables
                }
                report_data['results'].append(result_dict)
            
            # Generate filename and save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_report_{timestamp}.json"
            report_path = self.reports_dir / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Generated JSON report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate JSON report: {e}")
            raise
    
    def generate_email_content(self, result: MonitorResult, alert_type: str = "Monitoring Alert") -> str:
        """Generate email content for a monitoring result"""
        try:
            template_vars = {
                'alert_type': alert_type,
                'website_name': result.website_name,
                'url': result.url,
                'success': result.success,
                'status_code': result.status_code,
                'response_time': result.response_time,
                'error_message': result.error_message,
                'timestamp': result.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            template = self.jinja_env.get_template("email.html")
            return template.render(**template_vars)
            
        except Exception as e:
            self.logger.error(f"Failed to generate email content: {e}")
            raise
    
    def _calculate_summary(self, results: List[MonitorResult]) -> Dict[str, Any]:
        """Calculate summary statistics from results"""
        if not results:
            return {
                'total_checks': 0,
                'successful_checks': 0,
                'failed_checks': 0,
                'success_rate': 0.0,
                'average_response_time': 0.0,
                'total_execution_time': 0.0
            }
        
        total_checks = len(results)
        successful_checks = sum(1 for r in results if r.success)
        failed_checks = total_checks - successful_checks
        success_rate = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Calculate average response time (excluding None values)
        response_times = [r.response_time for r in results if r.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate total execution time
        total_execution_time = sum(response_times) if response_times else 0
        
        return {
            'total_checks': total_checks,
            'successful_checks': successful_checks,
            'failed_checks': failed_checks,
            'success_rate': success_rate,
            'average_response_time': avg_response_time,
            'total_execution_time': total_execution_time
        }
    
    def cleanup_old_reports(self, days: int = 30) -> None:
        """Remove old report files"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 3600)
        
        for report_file in self.reports_dir.glob("*"):
            if report_file.is_file():
                file_time = report_file.stat().st_mtime
                if file_time < cutoff_time:
                    try:
                        report_file.unlink()
                        self.logger.info(f"Deleted old report: {report_file}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete report {report_file}: {e}")
    
    def get_available_templates(self) -> List[str]:
        """Get list of available report templates"""
        templates = []
        for template_file in self.templates_dir.glob("*.html"):
            if template_file.name != "email.html":  # Exclude email template
                templates.append(template_file.stem)
        return templates