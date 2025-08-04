"""
Webhook notification system
"""

import asyncio
import aiohttp
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import config_manager
from core.monitor import MonitorResult


class WebhookNotifier:
    """Handles webhook notifications for monitoring results"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_notifications_config().webhook
    
    async def send_notification(self, result: MonitorResult, custom_payload: Optional[Dict[str, Any]] = None) -> bool:
        """Send webhook notification for monitoring result"""
        try:
            if not self.config.enabled:
                self.logger.info("Webhook notifications are disabled")
                return False
            
            if not self.config.url:
                self.logger.warning("No webhook URL configured")
                return False
            
            # Generate payload
            if custom_payload:
                payload = custom_payload
            else:
                payload = self._generate_default_payload(result)
            
            # Send webhook
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.config.url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status in [200, 201, 204]:
                        self.logger.info(f"Webhook notification sent successfully (status: {response.status})")
                        return True
                    else:
                        self.logger.error(f"Webhook notification failed with status: {response.status}")
                        response_text = await response.text()
                        self.logger.error(f"Response: {response_text}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.error("Webhook notification timeout")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False
    
    async def send_slack_notification(self, result: MonitorResult, channel: Optional[str] = None) -> bool:
        """Send Slack-formatted webhook notification"""
        color = "good" if result.success else "danger"
        status_emoji = "✅" if result.success else "❌"
        status_text = "SUCCESS" if result.success else "FAILED"
        
        payload = {
            "channel": channel,
            "username": "Website Monitor",
            "icon_emoji": ":robot_face:",
            "attachments": [
                {
                    "color": color,
                    "title": f"{status_emoji} {result.website_name} - {status_text}",
                    "title_link": result.url,
                    "fields": [
                        {
                            "title": "URL",
                            "value": result.url,
                            "short": True
                        },
                        {
                            "title": "Status Code",
                            "value": str(result.status_code) if result.status_code else "N/A",
                            "short": True
                        },
                        {
                            "title": "Response Time",
                            "value": f"{result.response_time:.2f}s" if result.response_time else "N/A",
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": result.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": "Website Monitoring System",
                    "ts": int(result.timestamp.timestamp())
                }
            ]
        }
        
        # Add error field if present
        if result.error_message:
            payload["attachments"][0]["fields"].append({
                "title": "Error",
                "value": result.error_message,
                "short": False
            })
        
        return await self.send_notification(result, payload)
    
    async def send_discord_notification(self, result: MonitorResult) -> bool:
        """Send Discord-formatted webhook notification"""
        color = 0x00ff00 if result.success else 0xff0000  # Green for success, red for failure
        status_emoji = "✅" if result.success else "❌"
        status_text = "SUCCESS" if result.success else "FAILED"
        
        embed = {
            "title": f"{status_emoji} Website Monitor Alert",
            "description": f"**{result.website_name}** - {status_text}",
            "color": color,
            "url": result.url,
            "fields": [
                {
                    "name": "URL",
                    "value": result.url,
                    "inline": True
                },
                {
                    "name": "Status Code",
                    "value": str(result.status_code) if result.status_code else "N/A",
                    "inline": True
                },
                {
                    "name": "Response Time",
                    "value": f"{result.response_time:.2f}s" if result.response_time else "N/A",
                    "inline": True
                }
            ],
            "timestamp": result.timestamp.isoformat(),
            "footer": {
                "text": "Website Monitoring System"
            }
        }
        
        # Add error field if present
        if result.error_message:
            embed["fields"].append({
                "name": "Error Details",
                "value": result.error_message,
                "inline": False
            })
        
        payload = {
            "embeds": [embed]
        }
        
        return await self.send_notification(result, payload)
    
    async def send_teams_notification(self, result: MonitorResult) -> bool:
        """Send Microsoft Teams-formatted webhook notification"""
        theme_color = "00FF00" if result.success else "FF0000"
        status_text = "SUCCESS" if result.success else "FAILED"
        
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"Website Monitor: {result.website_name} - {status_text}",
            "themeColor": theme_color,
            "sections": [
                {
                    "activityTitle": "Website Monitoring Alert",
                    "activitySubtitle": f"{result.website_name} - {status_text}",
                    "activityImage": "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/statuspage.svg",
                    "facts": [
                        {
                            "name": "Website",
                            "value": result.website_name
                        },
                        {
                            "name": "URL",
                            "value": result.url
                        },
                        {
                            "name": "Status Code",
                            "value": str(result.status_code) if result.status_code else "N/A"
                        },
                        {
                            "name": "Response Time",
                            "value": f"{result.response_time:.2f}s" if result.response_time else "N/A"
                        },
                        {
                            "name": "Timestamp",
                            "value": result.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    ]
                }
            ]
        }
        
        # Add error section if present
        if result.error_message:
            payload["sections"][0]["facts"].append({
                "name": "Error",
                "value": result.error_message
            })
        
        # Add potential actions
        payload["potentialAction"] = [
            {
                "@type": "OpenUri",
                "name": "Visit Website",
                "targets": [
                    {
                        "os": "default",
                        "uri": result.url
                    }
                ]
            }
        ]
        
        return await self.send_notification(result, payload)
    
    async def test_webhook(self) -> bool:
        """Test webhook configuration"""
        try:
            if not self.config.enabled or not self.config.url:
                return False
            
            # Create test payload
            test_payload = {
                "test": True,
                "message": "This is a test notification from Website Monitoring System",
                "timestamp": datetime.now().isoformat(),
                "system": "Website Monitor"
            }
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.config.url,
                    json=test_payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    success = response.status in [200, 201, 204]
                    if success:
                        self.logger.info("Webhook test successful")
                    else:
                        self.logger.error(f"Webhook test failed with status: {response.status}")
                    return success
                    
        except Exception as e:
            self.logger.error(f"Webhook test failed: {e}")
            return False
    
    def _generate_default_payload(self, result: MonitorResult) -> Dict[str, Any]:
        """Generate default webhook payload"""
        payload = {
            "event": "monitoring_check",
            "timestamp": result.timestamp.isoformat(),
            "website": {
                "name": result.website_name,
                "url": result.url
            },
            "result": {
                "success": result.success,
                "status_code": result.status_code,
                "response_time": result.response_time,
                "content_size": result.content_size,
                "error_message": result.error_message
            }
        }
        
        # Add screenshot if available
        if result.screenshot_path:
            payload["result"]["screenshot_path"] = result.screenshot_path
        
        # Add custom check results
        if result.custom_check_results:
            payload["result"]["custom_checks"] = result.custom_check_results
        
        # Add downloaded files
        if result.downloaded_files:
            payload["result"]["downloaded_files"] = result.downloaded_files
        
        # Add variables
        if result.variables:
            payload["variables"] = result.variables
        
        return payload