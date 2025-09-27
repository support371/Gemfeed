
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
    """Main orchestrator for the invitation system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.telegram_client = TelegramClient()
        self.email_service = EmailService()
        self.database = InviteDatabase()
        
    def send_single_invitation(self, contact: Dict) -> Tuple[bool, str, Optional[str]]:
        """Send a single invitation to a contact"""
        if not validate_config():
            return False, "System configuration incomplete", None
        
        try:
            # Check if contact already exists
            if self.database.contact_exists(contact['email'], contact.get('entity', '')):
                return False, "Contact already invited previously", None
            
            # Generate run ID for this single invite
            run_id = f"single_{uuid.uuid4().hex[:8]}"
            
            # Add initial record
            contact_hash = self.database.add_invite_record(contact, run_id)
            
            # Create Telegram invite link
            self.logger.info(f"Creating Telegram invite for {contact['name']} ({contact['email']})")
            
            if DRY_RUN:
                self.logger.info(f"DRY RUN: Would create invite for {contact['name']}")
                invite_link = f"https://t.me/+DRYRUN_{uuid.uuid4().hex[:8]}"
                success = True
            else:
                success, result = self.telegram_client.create_invite_link(contact.get('entity', contact['name']))
                invite_link = result.get('invite_link') if success else None
            
            if not success:
                error_msg = result.get('error', 'Failed to create invite link')
                self.database.update_invite_status(contact_hash, 'error', error_msg)
                return False, error_msg, None
            
            # Update database with invite link
            invite_data = {
                'invite_link': invite_link,
                'status': 'created',
                'delivery_channel': 'email'
            }
            self.database.add_invite_record(contact, run_id, invite_data)
            
            # Send email invitation
            if not DRY_RUN:
                email_success, email_message = self.email_service.send_invitation_email(contact, invite_link)
                
                if email_success:
                    self.database.update_invite_status(contact_hash, 'sent')
                    self.logger.info(f"Successfully sent invitation to {contact['email']}")
                    
                    # Send admin notification
                    self.telegram_client.send_admin_alert(
                        f"✅ Invitation sent successfully to {contact['name']} ({contact['email']}) "
                        f"from {contact.get('entity', 'Unknown Entity')}"
                    )
                    
                    return True, "Invitation sent successfully", invite_link
                else:
                    self.database.update_invite_status(contact_hash, 'email_failed', email_message)
                    return False, f"Failed to send email: {email_message}", invite_link
            else:
                self.database.update_invite_status(contact_hash, 'sent')
                return True, "DRY RUN: Invitation would be sent", invite_link
                
        except Exception as e:
            error_msg = f"Exception in send_single_invitation: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None
    
    def send_bulk_invitations(self, contacts: List[Dict], csv_filename: str = "") -> Dict:
        """Send invitations to multiple contacts"""
        if not validate_config():
            return {'success': False, 'message': 'System configuration incomplete'}
        
        run_id = f"bulk_{uuid.uuid4().hex[:8]}"
        total_contacts = len(contacts)
        
        # Create run record
        self.database.create_run(run_id, csv_filename, total_contacts)
        
        stats = {
            'total': total_contacts,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        self.logger.info(f"Starting bulk invitation run {run_id} with {total_contacts} contacts")
        
        # Send admin notification
        self.telegram_client.send_admin_alert(
            f"🚀 Starting bulk invitation run: {total_contacts} contacts"
        )
        
        for i, contact in enumerate(contacts, 1):
            try:
                # Check if contact already exists
                if self.database.contact_exists(contact['email'], contact.get('entity', '')):
                    self.logger.info(f"Skipping {contact['email']} - already invited")
                    stats['skipped'] += 1
                    continue
                
                # Send invitation
                success, message, invite_link = self.send_single_invitation(contact)
                
                if success:
                    stats['successful'] += 1
                    self.logger.info(f"[{i}/{total_contacts}] ✅ {contact['name']} - {message}")
                else:
                    stats['failed'] += 1
                    stats['errors'].append(f"{contact['name']} ({contact['email']}): {message}")
                    self.logger.error(f"[{i}/{total_contacts}] ❌ {contact['name']} - {message}")
                
                stats['processed'] += 1
                
                # Update run statistics
                self.database.update_run_stats(run_id, stats['processed'], stats['successful'], stats['failed'])
                
                # Rate limiting between contacts
                if i < total_contacts:
                    time.sleep(2)
                    
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Exception processing {contact.get('name', 'Unknown')}: {str(e)}"
                stats['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        # Complete the run
        self.database.complete_run(run_id)
        
        # Send completion notification
        self.telegram_client.send_admin_alert(
            f"📊 Bulk invitation run completed\\n"
            f"• Total: {stats['total']}\\n"
            f"• Successful: {stats['successful']}\\n"
            f"• Failed: {stats['failed']}\\n"
            f"• Skipped: {stats['skipped']}"
        )
        
        self.logger.info(f"Bulk invitation run {run_id} completed: {stats}")
        
        return {
            'success': True,
            'run_id': run_id,
            'stats': stats
        }
    
    def get_invitation_stats(self) -> Dict:
        """Get overall invitation statistics"""
        # Implementation depends on your database structure
        # This is a placeholder that can be expanded
        return {
            'total_invitations': 0,
            'successful_invitations': 0,
            'failed_invitations': 0,
            'pending_invitations': 0
        }
    
    def test_system(self) -> Tuple[bool, str]:
        """Test all system components"""
        issues = []
        
        # Test configuration
        if not validate_config():
            issues.append("Configuration validation failed")
        
        # Test Telegram bot permissions
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
