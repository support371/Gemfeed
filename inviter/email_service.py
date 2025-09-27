
import os
import logging
from typing import Dict, Tuple
import sendgrid
from sendgrid.helpers.mail import Mail, To, From, Subject, HtmlContent, PlainTextContent
from .config import SENDGRID_API_KEY, FROM_EMAIL, FROM_NAME

class EmailService:
    """Email service for sending invitation links"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        
    def send_invitation_email(self, contact: Dict, invite_link: str) -> Tuple[bool, str]:
        """Send invitation email with Telegram invite link"""
        try:
            # Create personalized email content
            html_content = self._create_html_content(contact, invite_link)
            plain_content = self._create_plain_content(contact, invite_link)
            
            # Create email
            message = Mail(
                from_email=From(FROM_EMAIL, FROM_NAME),
                to_emails=To(contact['email'], contact['name']),
                subject=Subject("Exclusive Invitation to GÉM Security Channel"),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(plain_content)
            )
            
            # Send email
            response = self.sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                self.logger.info(f"Invitation email sent successfully to {contact['email']}")
                return True, "Email sent successfully"
            else:
                error_msg = f"SendGrid error: {response.status_code}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _create_html_content(self, contact: Dict, invite_link: str) -> str:
        """Create HTML email content"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GÉM Security Invitation</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .invite-button {{ display: inline-block; background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                .security-note {{ background: #e9ecef; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ GÉM Security</h1>
                    <p>Exclusive Telegram Channel Invitation</p>
                </div>
                <div class="content">
                    <h2>Hello {contact['name']},</h2>
                    
                    <p>You've been personally invited to join our exclusive <strong>GÉM Security Telegram channel</strong> - a premium cybersecurity intelligence community.</p>
                    
                    <p><strong>What you'll get:</strong></p>
                    <ul>
                        <li>🔐 Real-time cybersecurity threat intelligence</li>
                        <li>📊 Daily security briefings and analysis</li>
                        <li>🚨 Breaking security alerts and advisories</li>
                        <li>💡 Expert insights from security professionals</li>
                        <li>🤝 Access to an exclusive security community</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="{invite_link}" class="invite-button">
                            Join GÉM Security Channel
                        </a>
                    </div>
                    
                    <div class="security-note">
                        <strong>🔒 Security Note:</strong> This is a single-use invite link that expires in 7 days. 
                        Only you can use this link to join our secure channel.
                    </div>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to reach out.</p>
                    
                    <p>Best regards,<br>
                    <strong>The GÉM Security Team</strong></p>
                </div>
                <div class="footer">
                    <p>© 2024 GÉM Security. All rights reserved.</p>
                    <p>This invitation was sent to {contact['email']} for {contact.get('entity', 'your organization')}.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_plain_content(self, contact: Dict, invite_link: str) -> str:
        """Create plain text email content"""
        return f"""
Hello {contact['name']},

You've been personally invited to join our exclusive GÉM Security Telegram channel - a premium cybersecurity intelligence community.

What you'll get:
• Real-time cybersecurity threat intelligence
• Daily security briefings and analysis  
• Breaking security alerts and advisories
• Expert insights from security professionals
• Access to an exclusive security community

Join here: {invite_link}

SECURITY NOTE: This is a single-use invite link that expires in 7 days. Only you can use this link to join our secure channel.

If you have any questions or need assistance, please don't hesitate to reach out.

Best regards,
The GÉM Security Team

---
© 2024 GÉM Security. All rights reserved.
This invitation was sent to {contact['email']} for {contact.get('entity', 'your organization')}.
        """
