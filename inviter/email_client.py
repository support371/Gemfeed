import logging
from typing import Tuple
from .config import (
    EMAIL_SERVICE, SENDGRID_API_KEY, FROM_EMAIL, FROM_NAME, DRY_RUN
)

class EmailClient:
    """Handle email delivery of invite links"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service = EMAIL_SERVICE
    
    def send_invite_email(self, recipient_email: str, recipient_name: str, 
                         invite_link: str, entity_name: str, expire_days: int = 7) -> Tuple[bool, str]:
        """Send invite link via email"""
        
        if DRY_RUN:
            self.logger.info(f"[DRY RUN] Would send email to {recipient_email}")
            return True, "dry_run"
        
        try:
            if self.service == "sendgrid":
                return self._send_via_sendgrid(recipient_email, recipient_name, invite_link, entity_name, expire_days)
            else:
                self.logger.error(f"Unknown email service: {self.service}")
                return False, "unknown_service"
        except Exception as e:
            self.logger.error(f"Error sending email to {recipient_email}: {e}")
            return False, str(e)
    
    def _send_via_sendgrid(self, recipient_email: str, recipient_name: str,
                          invite_link: str, entity_name: str, expire_days: int) -> Tuple[bool, str]:
        """Send email using SendGrid"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To
            
            if not SENDGRID_API_KEY:
                return False, "sendgrid_api_key_not_set"
            
            subject = f"Invitation to join GÉM Security - {entity_name}"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #1a73e8;">Welcome to GÉM Security</h2>
                        
                        <p>Hi <strong>{recipient_name}</strong>,</p>
                        
                        <p>You've been invited to join our exclusive GÉM Telegram group for cybersecurity professionals and compliance experts.</p>
                        
                        <p><strong>Your Invitation Link:</strong></p>
                        <p style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #1a73e8; margin: 20px 0;">
                            <a href="{invite_link}" style="color: #1a73e8; text-decoration: none; font-weight: bold;">{invite_link}</a>
                        </p>
                        
                        <p><strong>Important Details:</strong></p>
                        <ul>
                            <li>This link expires in <strong>{expire_days} days</strong></li>
                            <li>It can be used by <strong>one person only</strong></li>
                            <li>For entity: <strong>{entity_name}</strong></li>
                        </ul>
                        
                        <p>If you have any questions, please reach out to our team.</p>
                        
                        <p>Best regards,<br/>
                        <strong>GÉM Security Team</strong></p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px;">
                            This is an automated message from GÉM Security. Do not reply directly to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            text_content = f"""
Hi {recipient_name},

You've been invited to join the GÉM Telegram group.

Your Invitation Link:
{invite_link}

This link expires in {expire_days} days and can be used by one person only.
Entity: {entity_name}

Best regards,
GÉM Security Team
            """
            
            message = Mail(
                from_email=Email(FROM_EMAIL, FROM_NAME),
                to_emails=To(recipient_email),
                subject=subject,
                plain_text_content=text_content,
                html_content=html_content
            )
            
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                self.logger.info(f"Email sent successfully to {recipient_email}")
                return True, "sent"
            else:
                self.logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False, f"sendgrid_error_{response.status_code}"
        
        except ImportError:
            self.logger.error("sendgrid package not installed")
            return False, "sendgrid_not_installed"
        except Exception as e:
            self.logger.error(f"SendGrid error: {e}")
            return False, str(e)