"""
Notification Service - Send alerts via multiple channels
Supports: Email, Slack, Webhook, SMS (Twilio), Telegram
"""
import logging
import smtplib
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    TELEGRAM = "telegram"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """Unified notification service supporting multiple channels"""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        slack_webhook: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        twilio_from_number: Optional[str] = None,
    ):
        # Email configuration
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        
        # Slack configuration
        self.slack_webhook = slack_webhook
        
        # Telegram configuration
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        
        # Twilio (SMS) configuration
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
        self.twilio_from_number = twilio_from_number

    async def send_notification(
        self,
        title: str,
        message: str,
        channels: List[NotificationChannel],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        recipients: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send notification across multiple channels
        
        Args:
            title: Notification title
            message: Notification body
            channels: List of channels to send to
            priority: Notification priority level
            metadata: Additional context data
            recipients: Channel-specific recipient info
                {
                    'email': ['admin@example.com'],
                    'sms': ['+1234567890'],
                }
        
        Returns:
            Dict mapping channel to success status
        """
        results = {}
        
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    success = await self._send_email(title, message, recipients.get('email', []), priority)
                    results['email'] = success
                
                elif channel == NotificationChannel.SLACK:
                    success = await self._send_slack(title, message, priority, metadata)
                    results['slack'] = success
                
                elif channel == NotificationChannel.TELEGRAM:
                    success = await self._send_telegram(title, message, priority)
                    results['telegram'] = success
                
                elif channel == NotificationChannel.SMS:
                    success = await self._send_sms(message, recipients.get('sms', []))
                    results['sms'] = success
                
                elif channel == NotificationChannel.WEBHOOK:
                    success = await self._send_webhook(title, message, metadata, recipients.get('webhook'))
                    results['webhook'] = success
                    
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
                results[channel.value] = False
        
        return results

    async def _send_email(
        self,
        title: str,
        message: str,
        recipients: List[str],
        priority: NotificationPriority,
    ) -> bool:
        """Send email notification"""
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password]):
            logger.warning("Email configuration incomplete, skipping email")
            return False
        
        if not recipients:
            logger.warning("No email recipients provided")
            return False
        
        try:
            # Priority emoji
            emoji = {
                NotificationPriority.LOW: "ℹ️",
                NotificationPriority.MEDIUM: "⚠️",
                NotificationPriority.HIGH: "🔴",
                NotificationPriority.CRITICAL: "🚨",
            }.get(priority, "📧")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{emoji} {title}"
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(recipients)
            
            # HTML body
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="padding: 20px; border-left: 4px solid #{'ff0000' if priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL] else '007bff'};">
                        <h2 style="color: #{'d32f2f' if priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL] else '1976d2'};">
                            {emoji} {title}
                        </h2>
                        <p style="font-size: 14px; line-height: 1.6;">
                            {message.replace(chr(10), '<br>')}
                        </p>
                        <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                        <p style="color: #666; font-size: 12px;">
                            <strong>Priority:</strong> {priority.value.upper()}<br>
                            <strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def _send_slack(
        self,
        title: str,
        message: str,
        priority: NotificationPriority,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send Slack notification"""
        if not self.slack_webhook:
            logger.warning("Slack webhook not configured")
            return False
        
        try:
            color = {
                NotificationPriority.LOW: "#36a64f",
                NotificationPriority.MEDIUM: "#ff9800",
                NotificationPriority.HIGH: "#ff5722",
                NotificationPriority.CRITICAL: "#d32f2f",
            }.get(priority, "#2196f3")
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": [
                        {
                            "title": "Priority",
                            "value": priority.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                            "short": True
                        }
                    ],
                    "footer": "Qoneqt Alert System",
                    "ts": int(datetime.utcnow().timestamp())
                }]
            }
            
            # Add metadata fields if provided
            if metadata:
                for key, value in metadata.items():
                    payload["attachments"][0]["fields"].append({
                        "title": key,
                        "value": str(value),
                        "short": True
                    })
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook, json=payload) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent")
                        return True
                    else:
                        logger.error(f"Slack returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def _send_telegram(
        self,
        title: str,
        message: str,
        priority: NotificationPriority,
    ) -> bool:
        """Send Telegram notification"""
        if not all([self.telegram_bot_token, self.telegram_chat_id]):
            logger.warning("Telegram not configured")
            return False
        
        try:
            emoji = {
                NotificationPriority.LOW: "ℹ️",
                NotificationPriority.MEDIUM: "⚠️",
                NotificationPriority.HIGH: "🔴",
                NotificationPriority.CRITICAL: "🚨",
            }.get(priority, "📢")
            
            text = f"{emoji} *{title}*\n\n{message}\n\n_Priority: {priority.value.upper()}_"
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Telegram notification sent")
                        return True
                    else:
                        logger.error(f"Telegram returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    async def _send_sms(self, message: str, recipients: List[str]) -> bool:
        """Send SMS via Twilio"""
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_from_number]):
            logger.warning("Twilio not configured")
            return False
        
        if not recipients:
            logger.warning("No SMS recipients")
            return False
        
        try:
            # Import Twilio client
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            for recipient in recipients:
                client.messages.create(
                    body=message[:160],  # SMS character limit
                    from_=self.twilio_from_number,
                    to=recipient
                )
            
            logger.info(f"SMS sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    async def _send_webhook(
        self,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]],
        webhook_url: Optional[str],
    ) -> bool:
        """Send webhook notification"""
        if not webhook_url:
            logger.warning("No webhook URL provided")
            return False
        
        try:
            payload = {
                "title": title,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Webhook notification sent")
                        return True
                    else:
                        logger.error(f"Webhook returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get notification service singleton"""
    global _notification_service
    
    if _notification_service is None:
        from app.core.config import settings
        
        _notification_service = NotificationService(
            smtp_host=getattr(settings, 'SMTP_HOST', None),
            smtp_port=getattr(settings, 'SMTP_PORT', None),
            smtp_user=getattr(settings, 'SMTP_USER', None),
            smtp_password=getattr(settings, 'SMTP_PASSWORD', None),
            slack_webhook=getattr(settings, 'SLACK_WEBHOOK_URL', None),
            telegram_bot_token=getattr(settings, 'TELEGRAM_BOT_TOKEN', None),
            telegram_chat_id=getattr(settings, 'TELEGRAM_CHAT_ID', None),
            twilio_account_sid=getattr(settings, 'TWILIO_ACCOUNT_SID', None),
            twilio_auth_token=getattr(settings, 'TWILIO_AUTH_TOKEN', None),
            twilio_from_number=getattr(settings, 'TWILIO_FROM_NUMBER', None),
        )
    
    return _notification_service
