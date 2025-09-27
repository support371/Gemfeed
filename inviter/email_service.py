
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
import logging
from typing import Dict, Tuple
import requests
from .config import SENDGRID_API_KEY, FROM_EMAIL, FROM_NAME, TEST_MODE

class EmailService:
    """Email service for sending invitation emails"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = SENDGRID_API_KEY
        self.from_email = FROM_EMAIL
        self.from_name = FROM_NAME
    
    def send_invitation_email(self, contact: Dict, invite_link: str) -> Tuple[bool, str]:
        """Send invitation email via SendGrid"""
        if not self.api_key:
            return False, "SendGrid API key not configured"
        
        try:
            name = contact.get('name', 'Valued Partner')
            email = contact.get('email', '')
            entity = contact.get('entity', 'Your Organization')
            
            # Create email content
            subject = "Invitation to Join GÉM Security Telegram Channel"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">You're Invited to Join GÉM Security</h2>
                
                <p>Dear {name},</p>
                
                <p>You're cordially invited to join the <strong>GÉM Security Telegram Channel</strong>, 
                where cybersecurity professionals like yourself stay updated with the latest threat intelligence, 
                security insights, and industry developments.</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #495057; margin-top: 0;">What You'll Get:</h3>
                    <ul style="color: #6c757d;">
                        <li>Daily curated security news and threat intelligence</li>
                        <li>Expert analysis and actionable insights</li>
                        <li>Community discussions with security professionals</li>
                        <li>Real-time alerts on emerging threats</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invite_link}" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Join GÉM Security Channel
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #6c757d;">
                    This invitation is specifically for <strong>{entity}</strong> and expires in 7 days.
                    If you have any questions, please don't hesitate to reach out.
                </p>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #6c757d;">
                    Best regards,<br>
                    The GÉM Security Team<br>
                    <a href="mailto:{self.from_email}">{self.from_email}</a>
                </p>
            </div>
            """
            
            text_content = f"""
            Dear {name},

            You're invited to join the GÉM Security Telegram Channel for cybersecurity professionals.

            Join here: {invite_link}

            What you'll get:
            - Daily curated security news and threat intelligence
            - Expert analysis and actionable insights  
            - Community discussions with security professionals
            - Real-time alerts on emerging threats

            This invitation is for {entity} and expires in 7 days.

            Best regards,
            The GÉM Security Team
            {self.from_email}
            """
            
            # Send via SendGrid
            return self._send_via_sendgrid(email, subject, html_content, text_content)
            
        except Exception as e:
            error_msg = f"Error creating email: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _send_via_sendgrid(self, to_email: str, subject: str, 
                          html_content: str, text_content: str) -> Tuple[bool, str]:
        """Send email via SendGrid API"""
        
        if TEST_MODE:
            self.logger.info(f"TEST MODE: Would send email to {to_email}")
            return True, "Test mode - email not actually sent"
        
        url = "https://api.sendgrid.com/v3/mail/send"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": text_content
                },
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 202:
                self.logger.info(f"Email sent successfully to {to_email}")
                return True, "Email sent successfully"
            else:
                error_msg = f"SendGrid API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Exception sending email: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
