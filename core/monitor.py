"""
Website monitoring core functionality
"""

import asyncio
import aiohttp
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

from .auth import AuthenticationManager
from .screenshot import ScreenshotCapture
from .downloader import FileDownloader
from .variables import VariableManager
from config.settings import config_manager


@dataclass
class CustomCheck:
    """Custom check configuration"""
    name: str
    type: str  # 'xpath', 'css_selector', 'text_contains', 'regex'
    target: str  # XPath, CSS selector, or text pattern
    expected_value: Optional[str] = None
    variable_name: Optional[str] = None  # Store result in variable


@dataclass
class WebsiteConfig:
    """Website monitoring configuration"""
    name: str
    url: str
    enabled: bool = True
    check_interval: int = 300  # seconds
    timeout: int = 30
    
    # Authentication
    auth_type: Optional[str] = None  # 'form', 'basic', 'bearer'
    auth_config: Optional[Dict[str, Any]] = None
    
    # Content validation
    expected_status_codes: List[int] = field(default_factory=lambda: [200])
    content_checks: List[str] = field(default_factory=list)
    
    # Custom checks
    custom_checks: List[CustomCheck] = field(default_factory=list)
    
    # Features
    take_screenshot: bool = True
    download_files: List[str] = field(default_factory=list)  # URLs to download
    
    # Headers
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class MonitorResult:
    """Result of a monitoring check"""
    website_name: str
    url: str
    timestamp: datetime
    success: bool
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    content_size: Optional[int] = None
    screenshot_path: Optional[str] = None
    custom_check_results: Dict[str, Any] = field(default_factory=dict)
    downloaded_files: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)


class WebsiteMonitor:
    """Main website monitoring class"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_monitoring_config()
        self.auth_manager = AuthenticationManager()
        self.screenshot_capture = ScreenshotCapture()
        self.file_downloader = FileDownloader()
        self.variable_manager = VariableManager()
        
        # Monitoring state
        self.websites: Dict[str, WebsiteConfig] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.results_history: List[MonitorResult] = []
        self.is_monitoring = False
        
        # Callbacks
        self.result_callbacks: List[Callable[[MonitorResult], None]] = []
    
    def add_website(self, website_config: WebsiteConfig) -> None:
        """Add a website to monitor"""
        self.websites[website_config.name] = website_config
        self.logger.info(f"Added website for monitoring: {website_config.name}")
    
    def remove_website(self, website_name: str) -> None:
        """Remove a website from monitoring"""
        if website_name in self.websites:
            # Stop monitoring task if running
            if website_name in self.monitoring_tasks:
                self.monitoring_tasks[website_name].cancel()
                del self.monitoring_tasks[website_name]
            
            del self.websites[website_name]
            self.logger.info(f"Removed website from monitoring: {website_name}")
    
    def add_result_callback(self, callback: Callable[[MonitorResult], None]) -> None:
        """Add callback to be called when a monitoring result is available"""
        self.result_callbacks.append(callback)
    
    async def start_monitoring(self) -> None:
        """Start monitoring all configured websites"""
        if self.is_monitoring:
            self.logger.warning("Monitoring is already running")
            return
        
        self.is_monitoring = True
        self.logger.info("Starting website monitoring")
        
        # Start monitoring tasks for each enabled website
        for website_name, website_config in self.websites.items():
            if website_config.enabled:
                task = asyncio.create_task(
                    self._monitor_website_loop(website_config)
                )
                self.monitoring_tasks[website_name] = task
    
    async def stop_monitoring(self) -> None:
        """Stop all monitoring tasks"""
        self.is_monitoring = False
        self.logger.info("Stopping website monitoring")
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        
        self.monitoring_tasks.clear()
    
    async def check_website_once(self, website_config: WebsiteConfig) -> MonitorResult:
        """Perform a single check of a website"""
        start_time = time.time()
        result = MonitorResult(
            website_name=website_config.name,
            url=website_config.url,
            timestamp=datetime.now(),
            success=False
        )
        
        try:
            # Setup session with authentication
            session = await self.auth_manager.get_authenticated_session(
                website_config.auth_type,
                website_config.auth_config or {}
            )
            
            # Make HTTP request
            timeout = aiohttp.ClientTimeout(total=website_config.timeout)
            async with session.get(
                website_config.url,
                headers=website_config.headers,
                timeout=timeout
            ) as response:
                result.status_code = response.status
                result.response_time = time.time() - start_time
                
                # Check status code
                if response.status not in website_config.expected_status_codes:
                    result.error_message = f"Unexpected status code: {response.status}"
                    return result
                
                # Get content
                content = await response.text()
                result.content_size = len(content.encode('utf-8'))
                
                # Content validation
                for check_text in website_config.content_checks:
                    if check_text not in content:
                        result.error_message = f"Expected content not found: {check_text}"
                        return result
                
                # Take screenshot if enabled
                if website_config.take_screenshot:
                    screenshot_path = await self.screenshot_capture.capture_screenshot(
                        website_config.url,
                        website_config.name
                    )
                    if screenshot_path:
                        result.screenshot_path = screenshot_path
                        # Store screenshot in variables
                        self.variable_manager.set_variable(
                            f"{website_config.name}_screenshot",
                            screenshot_path
                        )
                
                # Perform custom checks
                await self._perform_custom_checks(website_config, result)
                
                # Download files
                for file_url in website_config.download_files:
                    try:
                        file_path = await self.file_downloader.download_file(
                            file_url,
                            website_config.name
                        )
                        if file_path:
                            result.downloaded_files.append(file_path)
                            # Store file path in variables
                            file_var_name = f"{website_config.name}_download_{len(result.downloaded_files)}"
                            self.variable_manager.set_variable(file_var_name, file_path)
                    except Exception as e:
                        self.logger.error(f"Failed to download {file_url}: {e}")
                
                # Get all variables for this check
                result.variables = self.variable_manager.get_all_variables()
                
                result.success = True
                
        except asyncio.TimeoutError:
            result.error_message = "Request timeout"
            result.response_time = time.time() - start_time
        except Exception as e:
            result.error_message = str(e)
            result.response_time = time.time() - start_time
            self.logger.error(f"Error checking {website_config.name}: {e}")
        
        return result
    
    async def _monitor_website_loop(self, website_config: WebsiteConfig) -> None:
        """Continuous monitoring loop for a single website"""
        while self.is_monitoring and website_config.enabled:
            try:
                result = await self.check_website_once(website_config)
                
                # Store result
                self.results_history.append(result)
                
                # Keep only recent results (last 1000)
                if len(self.results_history) > 1000:
                    self.results_history = self.results_history[-1000:]
                
                # Notify callbacks
                for callback in self.result_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        self.logger.error(f"Error in result callback: {e}")
                
                # Log result
                status = "SUCCESS" if result.success else "FAILED"
                self.logger.info(
                    f"[{status}] {website_config.name} - "
                    f"Status: {result.status_code}, "
                    f"Time: {result.response_time:.2f}s"
                )
                
                # Wait for next check
                await asyncio.sleep(website_config.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in monitoring loop for {website_config.name}: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _perform_custom_checks(self, website_config: WebsiteConfig, result: MonitorResult) -> None:
        """Perform custom checks on the website"""
        if not website_config.custom_checks:
            return
        
        try:
            # This would integrate with Selenium for DOM-based checks
            # For now, we'll just store the configuration
            for check in website_config.custom_checks:
                # Placeholder for custom check implementation
                check_result = f"Custom check '{check.name}' completed"
                result.custom_check_results[check.name] = check_result
                
                # Store in variables if specified
                if check.variable_name:
                    self.variable_manager.set_variable(check.variable_name, check_result)
                    
        except Exception as e:
            self.logger.error(f"Error performing custom checks: {e}")
    
    def get_recent_results(self, website_name: Optional[str] = None, limit: int = 100) -> List[MonitorResult]:
        """Get recent monitoring results"""
        results = self.results_history
        
        if website_name:
            results = [r for r in results if r.website_name == website_name]
        
        return results[-limit:]
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        stats = {
            'total_websites': len(self.websites),
            'enabled_websites': sum(1 for w in self.websites.values() if w.enabled),
            'monitoring_active': self.is_monitoring,
            'total_checks': len(self.results_history),
            'recent_success_rate': 0.0
        }
        
        # Calculate recent success rate (last 100 results)
        recent_results = self.results_history[-100:]
        if recent_results:
            successful = sum(1 for r in recent_results if r.success)
            stats['recent_success_rate'] = successful / len(recent_results) * 100
        
        return stats