"""
Task scheduling system for automated monitoring
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from threading import Thread
from dataclasses import dataclass

from core.monitor import WebsiteMonitor, MonitorResult
from notifications.email import EmailNotifier
from notifications.webhook import WebhookNotifier
from reports.generator import ReportGenerator
from config.settings import config_manager


@dataclass
class ScheduledTask:
    """Represents a scheduled monitoring task"""
    name: str
    schedule_expression: str  # cron-like expression
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0


class TaskScheduler:
    """Manages scheduled monitoring tasks"""
    
    def __init__(self, monitor: WebsiteMonitor):
        self.logger = logging.getLogger(__name__)
        self.monitor = monitor
        self.config = config_manager.get_scheduling_config()
        
        # Notification systems
        self.email_notifier = EmailNotifier()
        self.webhook_notifier = WebhookNotifier()
        self.report_generator = ReportGenerator()
        
        # Scheduling state
        self.tasks: Dict[str, ScheduledTask] = {}
        self.is_running = False
        self.scheduler_thread: Optional[Thread] = None
        
        # Results tracking for scheduled reports
        self.scheduled_results: List[MonitorResult] = []
        
    def add_scheduled_task(self, name: str, schedule_expression: str, enabled: bool = True) -> None:
        """Add a new scheduled task"""
        task = ScheduledTask(
            name=name,
            schedule_expression=schedule_expression,
            enabled=enabled
        )
        
        self.tasks[name] = task
        
        # Setup the schedule
        if enabled:
            self._setup_schedule(task)
        
        self.logger.info(f"Added scheduled task: {name} with schedule: {schedule_expression}")
    
    def remove_scheduled_task(self, name: str) -> None:
        """Remove a scheduled task"""
        if name in self.tasks:
            # Clear the schedule
            schedule.clear(name)
            del self.tasks[name]
            self.logger.info(f"Removed scheduled task: {name}")
    
    def enable_task(self, name: str) -> None:
        """Enable a scheduled task"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            self._setup_schedule(self.tasks[name])
            self.logger.info(f"Enabled scheduled task: {name}")
    
    def disable_task(self, name: str) -> None:
        """Disable a scheduled task"""
        if name in self.tasks:
            self.tasks[name].enabled = False
            schedule.clear(name)
            self.logger.info(f"Disabled scheduled task: {name}")
    
    def start_scheduler(self) -> None:
        """Start the task scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        if not self.config.enabled:
            self.logger.info("Scheduling is disabled in configuration")
            return
        
        self.is_running = True
        
        # Setup default tasks if none exist
        if not self.tasks:
            self._setup_default_tasks()
        
        # Start scheduler thread
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Task scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the task scheduler"""
        self.is_running = False
        
        # Clear all scheduled jobs
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Task scheduler stopped")
    
    def _setup_default_tasks(self) -> None:
        """Setup default scheduled tasks"""
        # Default monitoring task (every 5 minutes)
        self.add_scheduled_task(
            "monitoring_check",
            "*/5 * * * *",  # Every 5 minutes
            enabled=True
        )
        
        # Daily summary report (at 9 AM)
        self.add_scheduled_task(
            "daily_report",
            "0 9 * * *",  # 9:00 AM daily
            enabled=True
        )
        
        # Weekly comprehensive report (Monday at 8 AM)
        self.add_scheduled_task(
            "weekly_report",
            "0 8 * * 1",  # 8:00 AM on Mondays
            enabled=True
        )
        
        # Cleanup old files (daily at 2 AM)
        self.add_scheduled_task(
            "cleanup",
            "0 2 * * *",  # 2:00 AM daily
            enabled=True
        )
    
    def _setup_schedule(self, task: ScheduledTask) -> None:
        """Setup schedule for a specific task"""
        try:
            # Parse cron-like expression and setup schedule
            # For simplicity, we'll use predefined common schedules
            # In a full implementation, you'd use a proper cron parser
            
            if task.schedule_expression == "*/5 * * * *":  # Every 5 minutes
                schedule.every(5).minutes.do(self._execute_task, task.name).tag(task.name)
            elif task.schedule_expression == "*/10 * * * *":  # Every 10 minutes
                schedule.every(10).minutes.do(self._execute_task, task.name).tag(task.name)
            elif task.schedule_expression == "*/30 * * * *":  # Every 30 minutes
                schedule.every(30).minutes.do(self._execute_task, task.name).tag(task.name)
            elif task.schedule_expression == "0 * * * *":  # Every hour
                schedule.every().hour.do(self._execute_task, task.name).tag(task.name)
            elif task.schedule_expression == "0 9 * * *":  # Daily at 9 AM
                schedule.every().day.at("09:00").do(self._execute_task, task.name).tag(task.name)
            elif task.schedule_expression == "0 8 * * 1":  # Weekly on Monday at 8 AM
                schedule.every().monday.at("08:00").do(self._execute_task, task.name).tag(task.name)
            elif task.schedule_expression == "0 2 * * *":  # Daily at 2 AM
                schedule.every().day.at("02:00").do(self._execute_task, task.name).tag(task.name)
            else:
                # Default to the configured interval
                schedule.every(5).minutes.do(self._execute_task, task.name).tag(task.name)
                self.logger.warning(f"Unknown schedule expression: {task.schedule_expression}, using 5-minute default")
            
        except Exception as e:
            self.logger.error(f"Failed to setup schedule for task {task.name}: {e}")
    
    def _run_scheduler(self) -> None:
        """Main scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)
    
    def _execute_task(self, task_name: str) -> None:
        """Execute a scheduled task"""
        if task_name not in self.tasks:
            return
        
        task = self.tasks[task_name]
        
        if not task.enabled:
            return
        
        try:
            self.logger.info(f"Executing scheduled task: {task_name}")
            
            task.last_run = datetime.now()
            task.run_count += 1
            
            # Execute different types of tasks
            if task_name == "monitoring_check":
                asyncio.run(self._run_monitoring_check())
            elif task_name == "daily_report":
                asyncio.run(self._generate_daily_report())
            elif task_name == "weekly_report":
                asyncio.run(self._generate_weekly_report())
            elif task_name == "cleanup":
                self._run_cleanup()
            else:
                self.logger.warning(f"Unknown task type: {task_name}")
            
            self.logger.info(f"Completed scheduled task: {task_name}")
            
        except Exception as e:
            task.failure_count += 1
            self.logger.error(f"Failed to execute scheduled task {task_name}: {e}")
    
    async def _run_monitoring_check(self) -> None:
        """Run scheduled monitoring check"""
        if not self.monitor.websites:
            self.logger.info("No websites configured for monitoring")
            return
        
        results = []
        
        # Check each website
        for website_config in self.monitor.websites.values():
            if website_config.enabled:
                try:
                    result = await self.monitor.check_website_once(website_config)
                    results.append(result)
                    
                    # Store for scheduled reports
                    self.scheduled_results.append(result)
                    
                    # Send notifications if needed
                    await self._handle_notifications(result)
                    
                except Exception as e:
                    self.logger.error(f"Error checking website {website_config.name}: {e}")
        
        # Keep only recent results (last 1000)
        if len(self.scheduled_results) > 1000:
            self.scheduled_results = self.scheduled_results[-1000:]
        
        self.logger.info(f"Completed monitoring check for {len(results)} websites")
    
    async def _handle_notifications(self, result: MonitorResult) -> None:
        """Handle notifications for monitoring result"""
        try:
            # Get notification config
            notifications_config = config_manager.get_notifications_config()
            
            # Send webhook notification
            if notifications_config.webhook.enabled:
                await self.webhook_notifier.send_notification(result)
            
            # Send email notification for failures
            if notifications_config.email.enabled and not result.success:
                # You would configure recipients in the configuration
                recipients = ["admin@example.com"]  # This should come from config
                self.email_notifier.send_alert(result, recipients)
                
        except Exception as e:
            self.logger.error(f"Error handling notifications: {e}")
    
    async def _generate_daily_report(self) -> None:
        """Generate and send daily monitoring report"""
        try:
            # Get results from the last 24 hours
            cutoff_time = datetime.now() - timedelta(days=1)
            daily_results = [
                result for result in self.scheduled_results
                if result.timestamp >= cutoff_time
            ]
            
            if not daily_results:
                self.logger.info("No monitoring data for daily report")
                return
            
            # Generate HTML report
            report_path = self.report_generator.generate_html_report(
                daily_results, 
                template_name="default"
            )
            
            # Send email report if configured
            notifications_config = config_manager.get_notifications_config()
            if notifications_config.email.enabled:
                recipients = ["admin@example.com"]  # This should come from config
                self.email_notifier.send_report(
                    recipients, 
                    report_path, 
                    subject=f"Daily Monitoring Report - {datetime.now().strftime('%Y-%m-%d')}"
                )
            
            self.logger.info(f"Generated daily report: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
    
    async def _generate_weekly_report(self) -> None:
        """Generate and send weekly monitoring report"""
        try:
            # Get results from the last 7 days
            cutoff_time = datetime.now() - timedelta(days=7)
            weekly_results = [
                result for result in self.scheduled_results
                if result.timestamp >= cutoff_time
            ]
            
            if not weekly_results:
                self.logger.info("No monitoring data for weekly report")
                return
            
            # Generate HTML report
            report_path = self.report_generator.generate_html_report(
                weekly_results, 
                template_name="default"
            )
            
            # Generate JSON report as well
            json_report_path = self.report_generator.generate_json_report(
                weekly_results, 
                include_summary=True
            )
            
            # Send email report if configured
            notifications_config = config_manager.get_notifications_config()
            if notifications_config.email.enabled:
                recipients = ["admin@example.com"]  # This should come from config
                self.email_notifier.send_report(
                    recipients, 
                    report_path, 
                    subject=f"Weekly Monitoring Report - Week of {datetime.now().strftime('%Y-%m-%d')}"
                )
            
            self.logger.info(f"Generated weekly reports: {report_path}, {json_report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating weekly report: {e}")
    
    def _run_cleanup(self) -> None:
        """Run cleanup of old files"""
        try:
            # Cleanup old reports (30 days)
            self.report_generator.cleanup_old_reports(days=30)
            
            # Cleanup old screenshots (30 days)
            from core.screenshot import ScreenshotCapture
            screenshot_capture = ScreenshotCapture()
            screenshot_capture.cleanup_old_screenshots(days=30)
            
            # Cleanup old downloads (30 days)
            from core.downloader import FileDownloader
            file_downloader = FileDownloader()
            file_downloader.cleanup_old_downloads(days=30)
            
            # Cleanup old logs (30 days)
            from utils.logger import LogCleaner
            log_cleaner = LogCleaner()
            log_cleaner.cleanup_old_logs()
            
            self.logger.info("Completed cleanup of old files")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_task_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all scheduled tasks"""
        status = {}
        
        for name, task in self.tasks.items():
            # Get next run time from schedule
            next_run = None
            for job in schedule.jobs:
                if name in job.tags:
                    next_run = job.next_run
                    break
            
            status[name] = {
                "name": task.name,
                "schedule": task.schedule_expression,
                "enabled": task.enabled,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": next_run.isoformat() if next_run else None,
                "run_count": task.run_count,
                "failure_count": task.failure_count
            }
        
        return status
    
    def get_scheduler_status(self) -> Dict[str, any]:
        """Get overall scheduler status"""
        return {
            "running": self.is_running,
            "enabled": self.config.enabled,
            "total_tasks": len(self.tasks),
            "enabled_tasks": sum(1 for task in self.tasks.values() if task.enabled),
            "scheduled_results_count": len(self.scheduled_results)
        }