"""
Configuration management for the monitoring system
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MonitoringConfig:
    check_interval: int = 300
    request_timeout: int = 30
    max_concurrent: int = 10
    screenshot_enabled: bool = True
    screenshot_width: int = 1920
    screenshot_height: int = 1080
    screenshot_quality: int = 85


@dataclass
class AuthenticationConfig:
    session_timeout: int = 3600
    auto_relogin: bool = True
    encryption_key: str = "default_key_change_me"


@dataclass
class ReportsConfig:
    output_dir: str = "data/reports"
    default_template: str = "default"
    formats: list = None
    
    def __post_init__(self):
        if self.formats is None:
            self.formats = ["html", "docx"]


@dataclass
class EmailConfig:
    enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    use_tls: bool = True
    sender_email: str = ""
    sender_password: str = ""


@dataclass
class WebhookConfig:
    enabled: bool = False
    url: str = ""
    timeout: int = 10


@dataclass
class NotificationsConfig:
    email: EmailConfig = None
    webhook: WebhookConfig = None
    
    def __post_init__(self):
        if self.email is None:
            self.email = EmailConfig()
        if self.webhook is None:
            self.webhook = WebhookConfig()


@dataclass
class SchedulingConfig:
    enabled: bool = False
    default_schedule: str = "0 */6 * * *"


@dataclass
class LoggingConfig:
    level: str = "INFO"
    max_file_size: str = "10MB"
    backup_count: int = 5
    auto_cleanup_days: int = 30


@dataclass
class DownloadsConfig:
    output_dir: str = "data/downloads"
    max_file_size: str = "100MB"
    timeout: int = 60


@dataclass
class DirectoriesConfig:
    screenshots: str = "data/screenshots"
    downloads: str = "data/downloads"
    reports: str = "data/reports"
    logs: str = "data/logs"


class ConfigManager:
    """Configuration manager for the monitoring system"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/config.yaml"
        self.base_path = Path(__file__).parent.parent
        self.config_path = self.base_path / self.config_file
        self._config_data = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or {}
            else:
                logging.warning(f"Config file not found: {self.config_path}")
                self._config_data = {}
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self._config_data = {}
    
    def save_config(self) -> None:
        """Save current configuration to YAML file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._config_data, f, default_flow_style=False)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        config_data = self._config_data.get('monitoring', {})
        screenshot_data = config_data.get('screenshot', {})
        
        return MonitoringConfig(
            check_interval=config_data.get('check_interval', 300),
            request_timeout=config_data.get('request_timeout', 30),
            max_concurrent=config_data.get('max_concurrent', 10),
            screenshot_enabled=screenshot_data.get('enabled', True),
            screenshot_width=screenshot_data.get('width', 1920),
            screenshot_height=screenshot_data.get('height', 1080),
            screenshot_quality=screenshot_data.get('quality', 85)
        )
    
    def get_authentication_config(self) -> AuthenticationConfig:
        """Get authentication configuration"""
        config_data = self._config_data.get('authentication', {})
        return AuthenticationConfig(
            session_timeout=config_data.get('session_timeout', 3600),
            auto_relogin=config_data.get('auto_relogin', True),
            encryption_key=config_data.get('encryption_key', 'default_key_change_me')
        )
    
    def get_reports_config(self) -> ReportsConfig:
        """Get reports configuration"""
        config_data = self._config_data.get('reports', {})
        return ReportsConfig(
            output_dir=config_data.get('output_dir', 'data/reports'),
            default_template=config_data.get('default_template', 'default'),
            formats=config_data.get('formats', ['html', 'docx'])
        )
    
    def get_notifications_config(self) -> NotificationsConfig:
        """Get notifications configuration"""
        config_data = self._config_data.get('notifications', {})
        
        email_data = config_data.get('email', {})
        email_config = EmailConfig(
            enabled=email_data.get('enabled', False),
            smtp_server=email_data.get('smtp_server', 'smtp.gmail.com'),
            smtp_port=email_data.get('smtp_port', 587),
            use_tls=email_data.get('use_tls', True),
            sender_email=email_data.get('sender_email', ''),
            sender_password=email_data.get('sender_password', '')
        )
        
        webhook_data = config_data.get('webhook', {})
        webhook_config = WebhookConfig(
            enabled=webhook_data.get('enabled', False),
            url=webhook_data.get('url', ''),
            timeout=webhook_data.get('timeout', 10)
        )
        
        return NotificationsConfig(email=email_config, webhook=webhook_config)
    
    def get_scheduling_config(self) -> SchedulingConfig:
        """Get scheduling configuration"""
        config_data = self._config_data.get('scheduling', {})
        return SchedulingConfig(
            enabled=config_data.get('enabled', False),
            default_schedule=config_data.get('default_schedule', '0 */6 * * *')
        )
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        config_data = self._config_data.get('logging', {})
        return LoggingConfig(
            level=config_data.get('level', 'INFO'),
            max_file_size=config_data.get('max_file_size', '10MB'),
            backup_count=config_data.get('backup_count', 5),
            auto_cleanup_days=config_data.get('auto_cleanup_days', 30)
        )
    
    def get_downloads_config(self) -> DownloadsConfig:
        """Get downloads configuration"""
        config_data = self._config_data.get('downloads', {})
        return DownloadsConfig(
            output_dir=config_data.get('output_dir', 'data/downloads'),
            max_file_size=config_data.get('max_file_size', '100MB'),
            timeout=config_data.get('timeout', 60)
        )
    
    def get_directories_config(self) -> DirectoriesConfig:
        """Get directories configuration"""
        config_data = self._config_data.get('directories', {})
        return DirectoriesConfig(
            screenshots=config_data.get('screenshots', 'data/screenshots'),
            downloads=config_data.get('downloads', 'data/downloads'),
            reports=config_data.get('reports', 'data/reports'),
            logs=config_data.get('logs', 'data/logs')
        )
    
    def update_config(self, section: str, data: Dict[str, Any]) -> None:
        """Update configuration section"""
        self._config_data[section] = data
        self.save_config()
    
    def get_config_data(self) -> Dict[str, Any]:
        """Get raw configuration data"""
        return self._config_data.copy()


# Global config manager instance
config_manager = ConfigManager()