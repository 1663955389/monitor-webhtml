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
    associated_url: Optional[str] = None  # Specific URL this check should run against (if None, runs against all task URLs)


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
        
        # Generate patrol execution time variable
        patrol_time = datetime.now()
        safe_task_name = task.name.replace(' ', '_').replace('-', '_')
        
        # Generate multiple time format variables for flexibility in Word reports
        time_var_name = f"patrol_time_{safe_task_name}"
        time_formatted_var_name = f"patrol_time_formatted_{safe_task_name}"
        date_var_name = f"patrol_date_{safe_task_name}"
        datetime_var_name = f"patrol_datetime_{safe_task_name}"
        
        # Set time variables with different formats
        self.variable_manager.set_variable(
            time_var_name,
            patrol_time.strftime("%H:%M:%S"),
            "text",
            f"巡检执行时间 (任务: {task.name})"
        )
        
        self.variable_manager.set_variable(
            time_formatted_var_name,
            patrol_time.strftime("%Y年%m月%d日 %H:%M:%S"),
            "text",
            f"巡检执行时间-完整格式 (任务: {task.name})"
        )
        
        self.variable_manager.set_variable(
            date_var_name,
            patrol_time.strftime("%Y-%m-%d"),
            "text",
            f"巡检执行日期 (任务: {task.name})"
        )
        
        self.variable_manager.set_variable(
            datetime_var_name,
            patrol_time.strftime("%Y-%m-%d %H:%M:%S"),
            "text",
            f"巡检执行日期时间 (任务: {task.name})"
        )
        
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
        task.last_run = patrol_time
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
                        # Skip this check if it has an associated URL that doesn't match
                        if check.associated_url and check.associated_url != website_url:
                            continue
                            
                        check_result = await self._execute_patrol_check(
                            check, task, website_url, content, response, headers, cookies
                        )
                        result.check_results[check.name] = check_result
                        
                        # If any check fails, mark overall result as failed
                        if not check_result.get('success', True):
                            result.success = False
                
                # Take screenshot if configured or if visual checks are needed
                if any(check.type == PatrolType.VISUAL_CHECK for check in task.checks) or task.generate_report:
                    try:
                        safe_url = website_url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_').replace('.', '_')
                        website_name = f"{task.name}_{safe_url}"
                        screenshot_path = await self.screenshot_capture.capture_screenshot(
                            website_url, website_name
                        )
                        result.screenshot_path = screenshot_path
                        self.logger.info(f"Screenshot captured: {screenshot_path}")
                        
                        # Generate screenshot variable
                        safe_task_name = task.name.replace(' ', '_').replace('-', '_')
                        screenshot_var_name = f"screenshot_{safe_url}_{safe_task_name}"
                        self.variable_manager.set_variable(
                            screenshot_var_name, 
                            screenshot_path, 
                            "image", 
                            f"截图来自 {website_url} (任务: {task.name})"
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to capture screenshot: {e}")
                
                # Generate common variables for this website
                safe_url = website_url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_').replace('.', '_')
                safe_task_name = task.name.replace(' ', '_').replace('-', '_')
                
                # Status variable
                status_var_name = f"status_{safe_url}_{safe_task_name}"
                self.variable_manager.set_variable(
                    status_var_name,
                    "成功" if result.success else "失败",
                    "text",
                    f"巡检状态 {website_url} (任务: {task.name})"
                )
                
                # Response time variable
                response_time_var_name = f"response_time_{safe_url}_{safe_task_name}"
                self.variable_manager.set_variable(
                    response_time_var_name,
                    f"{result.response_time:.2f}秒",
                    "text",
                    f"响应时间 {website_url} (任务: {task.name})"
                )
                
                # Content size variable
                content_size_var_name = f"content_size_{safe_url}_{safe_task_name}"
                self.variable_manager.set_variable(
                    content_size_var_name,
                    f"{result.content_size} 字节",
                    "text",
                    f"内容大小 {website_url} (任务: {task.name})"
                )
                
        except asyncio.TimeoutError:
            result.error_message = f"请求超时 ({task.timeout}秒)"
            result.response_time = task.timeout
        except Exception as e:
            result.error_message = str(e)
            result.response_time = time.time() - start_time
            self.logger.error(f"Patrol error for {website_url}: {e}")
        
        return result
    
    async def _execute_patrol_check(self, check: PatrolCheck, task: PatrolTask, url: str, 
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
                # Enhanced content check: extract values first, then validate if expected value is provided
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                extracted_value = None
                
                if check.target.startswith('//') or check.target.startswith('/'):
                    # XPath support using lxml
                    try:
                        from lxml import html, etree
                        tree = html.fromstring(content)
                        elements = tree.xpath(check.target)
                        
                        if elements:
                            # Extract text content from first element
                            if hasattr(elements[0], 'text'):
                                extracted_value = elements[0].text
                            elif isinstance(elements[0], str):
                                extracted_value = elements[0]
                            else:
                                extracted_value = str(elements[0])
                            
                            check_result['extracted_value'] = extracted_value
                            check_result['value'] = len(elements)
                            check_result['message'] = f"XPath找到 {len(elements)} 个元素，提取值: {extracted_value[:100]}"
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
                        # Extract text content from first element
                        extracted_value = elements[0].get_text(strip=True)
                        check_result['extracted_value'] = extracted_value
                        check_result['value'] = len(elements)
                        check_result['message'] = f"CSS选择器找到 {len(elements)} 个元素，提取值: {extracted_value[:100]}"
                    else:
                        check_result['message'] = f"CSS选择器未找到匹配元素: {check.target}"
                
                # Always try to extract value first, then validate if expected value is provided
                if extracted_value is not None:
                    check_result['success'] = True  # Value extraction successful
                    
                    # If expected value is provided, validate against it
                    if check.expected_value:
                        if check.tolerance == "exact":
                            validation_success = extracted_value == check.expected_value
                        elif check.tolerance == "regex":
                            import re
                            try:
                                validation_success = bool(re.search(check.expected_value, extracted_value))
                            except Exception as e:
                                validation_success = False
                                check_result['message'] += f", 正则表达式错误: {str(e)}"
                        else:  # contains (default)
                            validation_success = check.expected_value in extracted_value
                        
                        check_result['validation_success'] = validation_success
                        check_result['message'] += f", 验证: {'通过' if validation_success else '失败'}"
                        
                        # Overall success depends on validation if expected value is provided
                        check_result['success'] = validation_success
                elif check.expected_value:
                    # If no value extracted but expected value provided, do simple text search
                    found = check.expected_value in content
                    check_result['success'] = found
                    check_result['value'] = found
                    check_result['message'] = f"文本搜索: {'找到' if found else '未找到'} '{check.expected_value}'"
            
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
                # Enhanced visual check with screenshot capture
                try:
                    screenshot_path = None
                    safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_').replace('.', '_')
                    website_name = f"{task.name}_{check.name}_{safe_url}"
                    
                    if check.target and check.target.lower() not in ['full', 'fullpage', '全页', 'viewport', '视口']:
                        # Element-specific screenshot using CSS selector
                        screenshot_path = await self.screenshot_capture.capture_element_screenshot(
                            url, website_name, check.target
                        )
                        check_result['message'] = f"元素截图 ({check.target}): {'成功' if screenshot_path else '失败'}"
                    else:
                        # Full page screenshot
                        if check.target and ('full' in check.target.lower() or '全页' in check.target):
                            screenshot_path = await self.screenshot_capture.capture_full_page_screenshot(
                                url, website_name
                            )
                            check_result['message'] = f"全页截图: {'成功' if screenshot_path else '失败'}"
                        else:
                            # Standard viewport screenshot
                            screenshot_path = await self.screenshot_capture.capture_screenshot(
                                url, website_name
                            )
                            check_result['message'] = f"页面截图: {'成功' if screenshot_path else '失败'}"
                    
                    if screenshot_path:
                        check_result['success'] = True
                        check_result['value'] = screenshot_path
                        check_result['screenshot_path'] = screenshot_path
                        
                        # Generate visual check variable
                        safe_check_name = check.name.replace(' ', '_').replace('-', '_')
                        safe_task_name = task.name.replace(' ', '_').replace('-', '_')
                        visual_var_name = f"visual_{safe_check_name}_{safe_task_name}"
                        self.variable_manager.set_variable(
                            visual_var_name,
                            screenshot_path,
                            "image",
                            f"视觉检查 '{check.name}' 截图 (任务: {task.name})"
                        )
                    else:
                        check_result['message'] += " - 截图失败"
                        
                except Exception as e:
                    check_result['message'] = f"视觉检查错误: {str(e)}"
            
            elif check.type == PatrolType.DOWNLOAD_CHECK:
                # Enhanced file download check with metadata
                try:
                    safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_').replace('.', '_')
                    website_name = f"{task.name}_{check.name}_{safe_url}"
                    download_path = await self.file_downloader.download_file(
                        check.target, website_name
                    )
                    
                    if download_path:
                        check_result['success'] = True
                        check_result['value'] = download_path
                        
                        # Get file information
                        file_info = self.file_downloader.get_download_info(download_path)
                        check_result['file_info'] = file_info
                        
                        if file_info.get('exists'):
                            check_result['message'] = f"文件下载成功: {file_info.get('filename')} ({file_info.get('size')} 字节)"
                        else:
                            check_result['message'] = "文件下载成功但无法获取文件信息"
                        
                        # Generate download variables
                        safe_check_name = check.name.replace(' ', '_').replace('-', '_')
                        safe_task_name = task.name.replace(' ', '_').replace('-', '_')
                        
                        # File path variable
                        download_path_var = f"download_path_{safe_check_name}_{safe_task_name}"
                        self.variable_manager.set_variable(
                            download_path_var,
                            download_path,
                            "file",
                            f"下载检查 '{check.name}' 文件路径 (任务: {task.name})"
                        )
                        
                        # File size variable
                        if file_info.get('size'):
                            download_size_var = f"download_size_{safe_check_name}_{safe_task_name}"
                            self.variable_manager.set_variable(
                                download_size_var,
                                f"{file_info['size']} 字节",
                                "text",
                                f"下载检查 '{check.name}' 文件大小 (任务: {task.name})"
                            )
                        
                        # File name variable
                        if file_info.get('filename'):
                            download_name_var = f"download_name_{safe_check_name}_{safe_task_name}"
                            self.variable_manager.set_variable(
                                download_name_var,
                                file_info['filename'],
                                "text",
                                f"下载检查 '{check.name}' 文件名 (任务: {task.name})"
                            )
                    else:
                        check_result['message'] = "文件下载失败"
                        
                except Exception as e:
                    check_result['message'] = f"下载失败: {str(e)}"
            
            elif check.type == PatrolType.FORM_CHECK:
                # Form submission check
                check_result['message'] = "表单检查功能待实现"
            
        except Exception as e:
            check_result['message'] = f"检查执行错误: {str(e)}"
            self.logger.error(f"Error executing check {check.name}: {e}")
        
        # Generate variables for this check result
        safe_check_name = check.name.replace(' ', '_').replace('-', '_')
        safe_task_name = task.name.replace(' ', '_').replace('-', '_')
        
        # Status variable for this check
        check_status_var = f"status_{safe_check_name}_{safe_task_name}"
        self.variable_manager.set_variable(
            check_status_var,
            "成功" if check_result['success'] else "失败",
            "text",
            f"检查项 '{check.name}' 状态 (任务: {task.name})"
        )
        
        # Timestamp variable
        timestamp_var = f"timestamp_{safe_check_name}_{safe_task_name}"
        self.variable_manager.set_variable(
            timestamp_var,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text",
            f"检查项 '{check.name}' 执行时间 (任务: {task.name})"
        )
        
        # Type-specific variables
        if check.type == PatrolType.CONTENT_CHECK and check_result.get('extracted_value'):
            extracted_var = f"extracted_{safe_check_name}_{safe_task_name}"
            self.variable_manager.set_variable(
                extracted_var,
                check_result['extracted_value'],
                "text",
                f"从检查项 '{check.name}' 提取的内容 (任务: {task.name})"
            )
            
            # Add validation result if available
            if 'validation_success' in check_result:
                validation_var = f"validation_{safe_check_name}_{safe_task_name}"
                self.variable_manager.set_variable(
                    validation_var,
                    "通过" if check_result['validation_success'] else "失败",
                    "text",
                    f"检查项 '{check.name}' 验证结果 (任务: {task.name})"
                )
        
        elif check.type == PatrolType.API_CHECK:
            api_status_var = f"api_status_{safe_check_name}_{safe_task_name}"
            self.variable_manager.set_variable(
                api_status_var,
                str(check_result.get('value', '')),
                "number",
                f"API检查 '{check.name}' 状态码 (任务: {task.name})"
            )
            
            if check_result.get('extracted_value'):
                api_response_var = f"api_response_{safe_check_name}_{safe_task_name}"
                self.variable_manager.set_variable(
                    api_response_var,
                    check_result['extracted_value'],
                    "text",
                    f"API检查 '{check.name}' 响应内容 (任务: {task.name})"
                )
        
        elif check.type == PatrolType.VISUAL_CHECK and check_result.get('screenshot_path'):
            # Visual check variable already generated in the execution section
            pass
        
        elif check.type == PatrolType.DOWNLOAD_CHECK:
            # Download check variables already generated in the execution section
            pass
        
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