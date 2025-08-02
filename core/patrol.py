"""
Website content patrol/inspection system (网站内容巡检系统)
Content-focused inspection rather than continuous monitoring
"""

import asyncio
import aiohttp
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

from .auth import AuthenticationManager
from .screenshot import ScreenshotCapture
from .downloader import FileDownloader
from .variables import VariableManager
from config.settings import config_manager


class PatrolFrequency(Enum):
    """Patrol frequency options"""
    DAILY = "daily"
    MULTIPLE_DAILY = "multiple_daily"  # Multiple times per day
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class PatrolType(Enum):
    """Types of patrol checks"""
    CONTENT_CHECK = "content_check"
    VISUAL_CHECK = "visual_check"
    DOWNLOAD_CHECK = "download_check"
    FORM_CHECK = "form_check"
    API_CHECK = "api_check"


@dataclass
class PatrolCheck:
    """Individual patrol check configuration"""
    name: str
    type: PatrolType
    target: str  # XPath, CSS selector, URL, etc.
    expected_value: Optional[str] = None
    tolerance: Optional[str] = None  # For visual/numeric comparisons
    description: str = ""
    enabled: bool = True


@dataclass
class PatrolTask:
    """Scheduled patrol task configuration"""
    name: str
    description: str
    websites: List[str]  # Website URLs to patrol
    checks: List[PatrolCheck] = field(default_factory=list)
    
    # Scheduling
    frequency: PatrolFrequency = PatrolFrequency.DAILY
    custom_schedule: Optional[str] = None  # Cron expression for custom frequency
    start_time: str = "09:00"  # Start time for daily/weekly patrols
    multiple_times: List[str] = field(default_factory=list)  # Multiple daily execution times ["09:00", "14:00", "18:00"]
    
    # Authentication and access
    auth_config: Optional[Dict[str, Any]] = None
    
    # Report settings
    generate_report: bool = True
    report_format: str = "word"  # "word", "html", "json"
    custom_template: Optional[str] = None
    
    # Notification settings
    notify_on_failure: bool = True
    notify_on_success: bool = False
    notification_recipients: List[str] = field(default_factory=list)
    
    # Execution settings
    timeout: int = 30
    retry_count: int = 2
    enabled: bool = True
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0


@dataclass
class PatrolResult:
    """Result of a patrol task execution"""
    task_name: str
    website_url: str
    timestamp: datetime
    success: bool
    
    # Performance metrics
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    content_size: Optional[int] = None
    
    # Check results
    check_results: Dict[str, Any] = field(default_factory=dict)
    
    # Error information
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    # Captured data
    screenshot_path: Optional[str] = None
    downloaded_files: List[str] = field(default_factory=list)
    extracted_data: Dict[str, Any] = field(default_factory=dict)


class PatrolEngine:
    """Core engine for website content patrol/inspection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_monitoring_config()
        
        # Component managers
        self.auth_manager = AuthenticationManager()
        self.screenshot_capture = ScreenshotCapture()
        self.file_downloader = FileDownloader()
        self.variable_manager = VariableManager()
        
        # Patrol state
        self.tasks: Dict[str, PatrolTask] = {}
        self.is_running = False
        self.result_callbacks: List[Callable[[PatrolResult], None]] = []
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def add_patrol_task(self, task: PatrolTask) -> None:
        """Add a new patrol task"""
        self.tasks[task.name] = task
        self.logger.info(f"Added patrol task: {task.name}")
    
    def remove_patrol_task(self, task_name: str) -> None:
        """Remove a patrol task"""
        if task_name in self.tasks:
            del self.tasks[task_name]
            self.logger.info(f"Removed patrol task: {task_name}")
    
    def get_patrol_task(self, task_name: str) -> Optional[PatrolTask]:
        """Get a patrol task by name"""
        return self.tasks.get(task_name)
    
    def list_patrol_tasks(self) -> List[PatrolTask]:
        """Get list of all patrol tasks"""
        return list(self.tasks.values())
    
    def add_result_callback(self, callback: Callable[[PatrolResult], None]) -> None:
        """Add callback for patrol results"""
        self.result_callbacks.append(callback)
    
    async def execute_patrol_task(self, task_name: str) -> List[PatrolResult]:
        """Execute a single patrol task"""
        task = self.tasks.get(task_name)
        if not task:
            raise ValueError(f"Patrol task not found: {task_name}")
        
        if not task.enabled:
            self.logger.info(f"Patrol task disabled: {task_name}")
            return []
        
        self.logger.info(f"Executing patrol task: {task_name}")
        results = []
        
        async with self as patrol_engine:
            for website_url in task.websites:
                result = await self._patrol_website(task, website_url)
                results.append(result)
                
                # Notify callbacks
                for callback in self.result_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        self.logger.error(f"Error in result callback: {e}")
        
        # Update task metadata
        task.last_run = datetime.now()
        task.run_count += 1
        
        self.logger.info(f"Completed patrol task: {task_name}, {len(results)} websites checked")
        return results
    
    async def _patrol_website(self, task: PatrolTask, website_url: str) -> PatrolResult:
        """Patrol a single website"""
        start_time = time.time()
        
        result = PatrolResult(
            task_name=task.name,
            website_url=website_url,
            timestamp=datetime.now(),
            success=False
        )
        
        try:
            # Setup authentication if needed
            headers = {}
            cookies = {}
            
            if task.auth_config:
                auth_type = task.auth_config.get('type', 'none')
                if auth_type != 'none':
                    authenticated_session = await self.auth_manager.get_authenticated_session(
                        auth_type, task.auth_config
                    )
                    # Extract headers and cookies from the authenticated session
                    if hasattr(authenticated_session, '_default_headers'):
                        headers.update(dict(authenticated_session._default_headers))
                    if hasattr(authenticated_session, '_cookie_jar'):
                        for cookie in authenticated_session._cookie_jar:
                            cookies[cookie.key] = cookie.value
            
            # Make HTTP request
            async with self.session.get(
                website_url, 
                headers=headers, 
                cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=task.timeout)
            ) as response:
                result.status_code = response.status
                result.response_time = time.time() - start_time
                
                # Get content
                content = await response.text()
                result.content_size = len(content.encode('utf-8'))
                
                # Basic success check
                if response.status in [200, 201, 202]:
                    result.success = True
                
                # Execute patrol checks
                for check in task.checks:
                    if check.enabled:
                        check_result = await self._execute_patrol_check(
                            check, website_url, content, response, headers, cookies
                        )
                        result.check_results[check.name] = check_result
                        
                        # If any check fails, mark overall result as failed
                        if not check_result.get('success', True):
                            result.success = False
                
                # Take screenshot if configured or if visual checks are needed
                if any(check.type == PatrolType.VISUAL_CHECK for check in task.checks) or task.generate_report:
                    try:
                        screenshot_path = await self.screenshot_capture.capture_screenshot(
                            website_url, headers, cookies
                        )
                        result.screenshot_path = screenshot_path
                        self.logger.info(f"Screenshot captured: {screenshot_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to capture screenshot: {e}")
                
        except asyncio.TimeoutError:
            result.error_message = f"请求超时 ({task.timeout}秒)"
            result.response_time = task.timeout
        except Exception as e:
            result.error_message = str(e)
            result.response_time = time.time() - start_time
            self.logger.error(f"Patrol error for {website_url}: {e}")
        
        return result
    
    async def _execute_patrol_check(self, check: PatrolCheck, url: str, 
                                  content: str, response: aiohttp.ClientResponse,
                                  headers: dict = None, cookies: dict = None) -> Dict[str, Any]:
        """Execute a specific patrol check"""
        check_result = {
            'name': check.name,
            'type': check.type.value,
            'success': False,
            'value': None,
            'extracted_value': None,
            'message': ''
        }
        
        try:
            if check.type == PatrolType.CONTENT_CHECK:
                # Enhanced content check with XPath and CSS selector support
                if check.expected_value:
                    # Simple text content check
                    found = check.expected_value in content
                    check_result['success'] = found
                    check_result['value'] = found
                    check_result['message'] = f"内容检查: {'找到' if found else '未找到'} '{check.expected_value}'"
                else:
                    # XPath or CSS selector check with value extraction
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    if check.target.startswith('//') or check.target.startswith('/'):
                        # XPath support using lxml
                        try:
                            from lxml import html, etree
                            tree = html.fromstring(content)
                            elements = tree.xpath(check.target)
                            
                            if elements:
                                check_result['success'] = True
                                check_result['value'] = len(elements)
                                
                                # Extract text content from first element
                                if hasattr(elements[0], 'text'):
                                    extracted_text = elements[0].text
                                elif isinstance(elements[0], str):
                                    extracted_text = elements[0]
                                else:
                                    extracted_text = str(elements[0])
                                
                                check_result['extracted_value'] = extracted_text
                                check_result['message'] = f"XPath找到 {len(elements)} 个元素，提取值: {extracted_text[:100]}"
                            else:
                                check_result['message'] = "XPath未找到匹配元素"
                                
                        except ImportError:
                            check_result['message'] = "XPath支持需要安装lxml库: pip install lxml"
                        except Exception as e:
                            check_result['message'] = f"XPath执行错误: {str(e)}"
                    else:
                        # CSS selector with value extraction
                        elements = soup.select(check.target)
                        if elements:
                            check_result['success'] = True
                            check_result['value'] = len(elements)
                            
                            # Extract text content from first element
                            extracted_text = elements[0].get_text(strip=True)
                            check_result['extracted_value'] = extracted_text
                            check_result['message'] = f"CSS选择器找到 {len(elements)} 个元素，提取值: {extracted_text[:100]}"
                        else:
                            check_result['message'] = f"CSS选择器未找到匹配元素: {check.target}"
            
            elif check.type == PatrolType.API_CHECK:
                # API response check
                check_result['success'] = response.status == 200
                check_result['value'] = response.status
                check_result['message'] = f"API状态码: {response.status}"
                
                # Try to extract JSON response value if target is specified
                if check.target and response.content_type and 'json' in response.content_type:
                    try:
                        import json
                        json_data = json.loads(content)
                        
                        # Simple key extraction
                        if '.' in check.target:
                            # Support nested keys like "data.user.name"
                            keys = check.target.split('.')
                            value = json_data
                            for key in keys:
                                value = value[key]
                        else:
                            value = json_data.get(check.target)
                        
                        check_result['extracted_value'] = str(value)
                        check_result['message'] += f", 提取值: {str(value)[:100]}"
                    except Exception as e:
                        check_result['message'] += f", JSON提取失败: {str(e)}"
            
            elif check.type == PatrolType.VISUAL_CHECK:
                # Visual check would require screenshot comparison
                check_result['message'] = "视觉检查需要截图对比功能"
            
            elif check.type == PatrolType.DOWNLOAD_CHECK:
                # File download check
                try:
                    download_path = await self.file_downloader.download_file(
                        check.target, url
                    )
                    check_result['success'] = bool(download_path)
                    check_result['value'] = download_path
                    check_result['message'] = f"文件下载: {'成功' if download_path else '失败'}"
                except Exception as e:
                    check_result['message'] = f"下载失败: {str(e)}"
            
            elif check.type == PatrolType.FORM_CHECK:
                # Form submission check
                check_result['message'] = "表单检查功能待实现"
            
        except Exception as e:
            check_result['message'] = f"检查执行错误: {str(e)}"
            self.logger.error(f"Error executing check {check.name}: {e}")
        
        return check_result
    
    def calculate_next_run_time(self, task: PatrolTask) -> datetime:
        """Calculate next run time for a patrol task"""
        now = datetime.now()
        
        if task.frequency == PatrolFrequency.DAILY:
            # Parse start time
            hour, minute = map(int, task.start_time.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed today, schedule for tomorrow
            if next_run <= now:
                next_run += timedelta(days=1)
                
        elif task.frequency == PatrolFrequency.MULTIPLE_DAILY:
            # Find next execution time from multiple daily times
            if not task.multiple_times:
                # Fallback to single daily execution
                hour, minute = map(int, task.start_time.split(':'))
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
            else:
                # Find the next scheduled time today or tomorrow
                next_run = None
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                
                for time_str in sorted(task.multiple_times):
                    hour, minute = map(int, time_str.split(':'))
                    scheduled_time = today.replace(hour=hour, minute=minute)
                    
                    if scheduled_time > now:
                        next_run = scheduled_time
                        break
                
                # If no time found today, use first time tomorrow
                if next_run is None:
                    hour, minute = map(int, sorted(task.multiple_times)[0].split(':'))
                    next_run = today + timedelta(days=1)
                    next_run = next_run.replace(hour=hour, minute=minute)
                
        elif task.frequency == PatrolFrequency.WEEKLY:
            # Schedule for next Monday at start time
            hour, minute = map(int, task.start_time.split(':'))
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
        elif task.frequency == PatrolFrequency.MONTHLY:
            # Schedule for first day of next month
            hour, minute = map(int, task.start_time.split(':'))
            if now.month == 12:
                next_run = now.replace(year=now.year+1, month=1, day=1, 
                                     hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month+1, day=1, 
                                     hour=hour, minute=minute, second=0, microsecond=0)
                
        elif task.frequency == PatrolFrequency.CUSTOM and task.custom_schedule:
            # For custom cron schedules, would need croniter library
            # For now, default to daily
            hour, minute = map(int, task.start_time.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        else:
            # Default to daily
            hour, minute = map(int, task.start_time.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        return next_run