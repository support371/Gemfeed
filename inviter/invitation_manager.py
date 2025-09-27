import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from .telegram_client import TelegramClient
from .email_service import EmailService
from .database import InviteDatabase
from .config import validate_config, DRY_RUN, TEST_MODE

class InvitationManager:
    """Main manager for the invitation workflow"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.telegram_client = TelegramClient()
        self.email_service = EmailService()
        self.database = InviteDatabase()

        # Initialize database
        self.database.init_database()

    def send_single_invitation(self, contact: Dict) -> Tuple[bool, str, Optional[str]]:
        """Send a single invitation"""
        try:
            name = contact.get('name', 'Valued Partner')
            email = contact.get('email', '')
            entity = contact.get('entity', 'Your Organization')

            if not email:
                return False, "Email address is required", None

            self.logger.info(f"Processing invitation for {name} ({email})")

            # Create Telegram invite link
            success, invite_data = self.telegram_client.create_invite_link(entity)

            if not success:
                error_msg = f"Failed to create Telegram invite: {invite_data.get('error', 'Unknown error')}"
                self.database.log_invitation(contact, status='error', error_message=error_msg)
                return False, error_msg, None

            invite_link = invite_data['invite_link']

            # Send email
            email_success, email_message = self.email_service.send_invitation_email(
                contact, invite_link
            )

            if email_success:
                # Log successful invitation
                self.database.log_invitation(contact, invite_link, status='sent')
                success_msg = f"Invitation sent successfully to {name}"
                self.logger.info(success_msg)
                return True, success_msg, invite_link
            else:
                # Log email failure
                self.database.log_invitation(contact, invite_link, status='error', 
                                           error_message=f"Email failed: {email_message}")
                return False, f"Email sending failed: {email_message}", invite_link

        except Exception as e:
            error_msg = f"Exception processing invitation: {str(e)}"
            self.logger.error(error_msg)
            self.database.log_invitation(contact, status='error', error_message=error_msg)
            return False, error_msg, None

    def send_bulk_invitations(self, contacts: List[Dict], filename: str = None) -> Dict:
        """Send bulk invitations with progress tracking"""
        batch_id = str(uuid.uuid4())
        total_contacts = len(contacts)

        self.logger.info(f"Starting bulk invitation batch {batch_id} with {total_contacts} contacts")

        # Initialize batch record
        try:
            conn = self.database.init_database()  # Ensure DB is ready
        except:
            pass

        stats = {
            'total': total_contacts,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'batch_id': batch_id
        }

        for i, contact in enumerate(contacts, 1):
            try:
                # Add batch ID to contact
                contact['batch_id'] = batch_id

                success, message, invite_link = self.send_single_invitation(contact)

                stats['processed'] += 1
                if success:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1

                # Small delay between invitations to respect rate limits
                if i < total_contacts:
                    time.sleep(2)

                # Progress logging
                if i % 10 == 0 or i == total_contacts:
                    self.logger.info(f"Batch {batch_id}: Processed {i}/{total_contacts} contacts")

            except Exception as e:
                self.logger.error(f"Error processing contact {i}: {e}")
                stats['failed'] += 1
                stats['processed'] += 1

        self.logger.info(f"Batch {batch_id} completed: {stats['successful']} successful, {stats['failed']} failed")

        return {
            'success': True,
            'stats': stats,
            'batch_id': batch_id
        }

    def test_system(self) -> Tuple[bool, str]:
        """Test all system components"""
        issues = []

        # Test configuration
        if not validate_config():
            issues.append("Configuration validation failed")

        # Test Telegram bot
        try:
            success, message = self.telegram_client.test_bot_permissions()
            if not success:
                issues.append(f"Telegram bot test failed: {message}")
        except Exception as e:
            issues.append(f"Telegram test exception: {str(e)}")

        # Test database connection
        try:
            self.database.init_database()
        except Exception as e:
            issues.append(f"Database test failed: {str(e)}")

        if issues:
            return False, "; ".join(issues)
        else:
            return True, "All system components are working correctly"