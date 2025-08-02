"""
Email notification system
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Optional

from config.settings import config_manager
from core.monitor import MonitorResult


class EmailNotifier:
    """Handles email notifications for monitoring results"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_notifications_config().email
    
    def send_notification(self, result: MonitorResult, recipients: List[str], 
                         subject: Optional[str] = None, html_content: Optional[str] = None,
                         attachments: Optional[List[str]] = None) -> bool:
        """Send email notification for monitoring result"""
        try:
            if not self.config.enabled:
                self.logger.info("Email notifications are disabled")
                return False
            
            if not recipients:
                self.logger.warning("No recipients specified for email notification")
                return False
            
            # Generate subject if not provided
            if subject is None:
                status = "SUCCESS" if result.success else "FAILED"
                subject = f"[Monitor] {result.website_name} - {status}"
            
            # Generate content if not provided
            if html_content is None:
                html_content = self._generate_default_content(result)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = ', '.join(recipients)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add plain text alternative
            text_content = self._html_to_text(html_content)
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)
            
            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    self._add_attachment(msg, attachment_path)
            
            # Send email
            self._send_email(msg, recipients)
            
            self.logger.info(f"Email notification sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def send_alert(self, result: MonitorResult, recipients: List[str]) -> bool:
        """Send alert email for failed monitoring"""
        if result.success:
            return False  # Don't send alerts for successful checks
        
        subject = f"🚨 ALERT: {result.website_name} is DOWN"
        html_content = self._generate_alert_content(result)
        
        return self.send_notification(result, recipients, subject, html_content)
    
    def send_recovery_notification(self, result: MonitorResult, recipients: List[str]) -> bool:
        """Send recovery notification when service comes back up"""
        if not result.success:
            return False  # Don't send recovery for failed checks
        
        subject = f"✅ RECOVERED: {result.website_name} is back online"
        html_content = self._generate_recovery_content(result)
        
        return self.send_notification(result, recipients, subject, html_content)
    
    def send_report(self, recipients: List[str], report_path: str, 
                   subject: Optional[str] = None) -> bool:
        """Send monitoring report as email attachment"""
        try:
            if not self.config.enabled:
                self.logger.info("Email notifications are disabled")
                return False
            
            # Generate subject if not provided
            if subject is None:
                from datetime import datetime
                subject = f"Monitoring Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = ', '.join(recipients)
            
            # Add body text
            body = """
            <html>
            <body>
            <h2>Website Monitoring Report</h2>
            <p>Please find the attached monitoring report.</p>
            <p>This report contains detailed information about website monitoring results.</p>
            <br>
            <p>Best regards,<br>Website Monitoring System</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            # Add report as attachment
            self._add_attachment(msg, report_path)
            
            # Send email
            self._send_email(msg, recipients)
            
            self.logger.info(f"Report email sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send report email: {e}")
            return False
    
    def test_configuration(self) -> bool:
        """Test email configuration by sending a test email"""
        try:
            if not self.config.enabled:
                return False
            
            # Create test message
            msg = MIMEText("This is a test email from the Website Monitoring System.")
            msg['Subject'] = "Test Email - Website Monitor"
            msg['From'] = self.config.sender_email
            msg['To'] = self.config.sender_email  # Send to self for testing
            
            # Send test email
            self._send_email(msg, [self.config.sender_email])
            
            self.logger.info("Test email sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Email configuration test failed: {e}")
            return False
    
    def _send_email(self, msg, recipients: List[str]) -> None:
        """Send email using SMTP"""
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            if self.config.use_tls:
                server.starttls()
            
            server.login(self.config.sender_email, self.config.sender_password)
            server.send_message(msg, to_addrs=recipients)
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> None:
        """Add file attachment to email message"""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"Attachment file not found: {file_path}")
                return
            
            with open(path, 'rb') as f:
                attachment = MIMEApplication(f.read())
                attachment.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=path.name
                )
                msg.attach(attachment)
                
        except Exception as e:
            self.logger.error(f"Failed to add attachment {file_path}: {e}")
    
    def _generate_default_content(self, result: MonitorResult) -> str:
        """Generate default HTML email content"""
        status_color = "#28a745" if result.success else "#dc3545"
        status_text = "SUCCESS ✅" if result.success else "FAILED ❌"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 1.8em;">Monitoring Notification</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div style="padding: 30px;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h2 style="margin: 0; color: {status_color}; font-size: 1.5em;">{status_text}</h2>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Website:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{result.website_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">URL:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;"><a href="{result.url}" style="color: #667eea; text-decoration: none;">{result.url}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Status Code:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{result.status_code or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Response Time:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{result.response_time:.2f}s</td>
                        </tr>
                    </table>
        """
        
        # Add error message if present
        if result.error_message:
            html += f"""
                    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #721c24;">Error Details</h3>
                        <p style="margin: 0; color: #721c24;">{result.error_message}</p>
                    </div>
            """
        
        html += """
                </div>
                
                <div style="background-color: #333; color: white; text-align: center; padding: 20px; font-size: 0.9em;">
                    <p style="margin: 0;">Website Monitoring and Reporting System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_alert_content(self, result: MonitorResult) -> str:
        """Generate alert email content for failures"""
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #a71d2a 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 1.8em;">🚨 WEBSITE DOWN ALERT</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Immediate attention required</p>
                </div>
                
                <div style="padding: 30px;">
                    <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 10px 0; color: #721c24;">{result.website_name} is not responding</h2>
                        <p style="margin: 0; color: #721c24;">The website monitoring system has detected that your website is currently unavailable.</p>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Website:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{result.website_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">URL:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;"><a href="{result.url}" style="color: #667eea; text-decoration: none;">{result.url}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Failed at:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Error:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; color: #dc3545;">{result.error_message or 'Unknown error'}</td>
                        </tr>
                    </table>
                    
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #856404;">Recommended Actions</h3>
                        <ul style="margin: 0; color: #856404;">
                            <li>Check if the website is accessible manually</li>
                            <li>Verify server status and logs</li>
                            <li>Check DNS resolution</li>
                            <li>Contact your hosting provider if needed</li>
                        </ul>
                    </div>
                </div>
                
                <div style="background-color: #333; color: white; text-align: center; padding: 20px; font-size: 0.9em;">
                    <p style="margin: 0;">You will receive a recovery notification when the website is back online.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_recovery_content(self, result: MonitorResult) -> str:
        """Generate recovery email content"""
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 1.8em;">✅ WEBSITE RECOVERED</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Service restored successfully</p>
                </div>
                
                <div style="padding: 30px;">
                    <div style="background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 10px 0; color: #155724;">{result.website_name} is back online</h2>
                        <p style="margin: 0; color: #155724;">The website is now responding normally and all systems appear to be operational.</p>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Website:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{result.website_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">URL:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;"><a href="{result.url}" style="color: #667eea; text-decoration: none;">{result.url}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Recovered at:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: #666;">Response Time:</td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee; color: #28a745;">{result.response_time:.2f}s</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #333; color: white; text-align: center; padding: 20px; font-size: 0.9em;">
                    <p style="margin: 0;">Continue monitoring for optimal performance.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text for email alternative"""
        # Simple HTML to text conversion
        import re
        
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html_content)
        
        # Replace HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text