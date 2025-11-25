import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from .config import TEST_MODE
from .database import InviteDatabase
from .csv_processor import CSVProcessor
from .telegram_client import TelegramClient
from .email_client import EmailClient

class InviteWorkflow:
    """Main workflow orchestrator for sending Telegram invite links"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = InviteDatabase()
        self.csv_processor = CSVProcessor()
        self.telegram = TelegramClient()
        self.email = EmailClient()
        self.run_id = str(uuid.uuid4())[:8]
        
        logging.basicConfig(
            level=logging.DEBUG if TEST_MODE else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def run_from_csv(self, csv_file_path: str, dry_run: bool = False, 
                     send_via: str = 'email') -> Dict:
        """Run the complete workflow from a CSV file"""
        
        self.logger.info(f"Starting invite workflow (Run ID: {self.run_id})")
        self.logger.info(f"Processing: {csv_file_path}")
        
        # Step 1: Test bot permissions
        can_create, perm_msg = self.telegram.test_bot_permissions()
        if not can_create:
            self.logger.error(f"Bot permission check failed: {perm_msg}")
            return {
                'success': False,
                'run_id': self.run_id,
                'error': f"Bot permissions: {perm_msg}",
                'processed': 0,
                'successful': 0,
                'failed': 0
            }
        
        self.logger.info("✓ Bot permissions verified")
        
        # Step 2: Read and validate CSV
        try:
            contacts = self.csv_processor.process_csv_file(csv_file_path)
            self.logger.info(f"Loaded {len(contacts)} contacts from CSV")
        except Exception as e:
            self.logger.error(f"Failed to process CSV: {e}")
            return {
                'success': False,
                'run_id': self.run_id,
                'error': f"CSV processing failed: {str(e)}",
                'processed': 0,
                'successful': 0,
                'failed': 0
            }
        
        # Step 3: Create run record
        self.db.create_run(self.run_id, csv_file_path, len(contacts))
        
        # Step 4: Process each contact
        processed = 0
        successful = 0
        failed = 0
        skipped_duplicates = 0
        
        for contact in contacts:
            try:
                processed += 1
                
                # Check for duplicates
                if self.db.contact_exists(contact['email'], contact['entity']):
                    self.logger.warning(f"Skipping duplicate: {contact['email']} ({contact['entity']})")
                    skipped_duplicates += 1
                    continue
                
                # Create invite link
                success, invite_data = self.telegram.create_invite_link(contact['entity'])
                
                if not success:
                    self.logger.error(f"Failed to create invite for {contact['name']}: {invite_data.get('error', 'Unknown error')}")
                    contact_hash = self.db.add_invite_record(
                        contact, 
                        self.run_id,
                        {'status': 'failed', 'error': invite_data.get('error', 'Unknown error')}
                    )
                    self.db.update_invite_status(
                        contact_hash, 
                        'failed',
                        invite_data.get('error', 'Unknown error')
                    )
                    failed += 1
                    continue
                
                # Add to database with invite info
                invite_data['delivery_channel'] = send_via
                invite_data['status'] = 'created'
                contact_hash = self.db.add_invite_record(contact, self.run_id, invite_data)
                
                # Send via email or DM
                if send_via == 'email' and contact.get('email'):
                    email_success, email_msg = self.email.send_invite_email(
                        contact['email'],
                        contact['name'],
                        invite_data['invite_link'],
                        contact['entity']
                    )
                    
                    if email_success:
                        self.logger.info(f"✓ Invite sent to {contact['email']}")
                        self.db.update_invite_status(contact_hash, 'delivered')
                        successful += 1
                    else:
                        self.logger.error(f"Failed to send email to {contact['email']}: {email_msg}")
                        self.db.update_invite_status(contact_hash, 'failed', f"Email failed: {email_msg}")
                        failed += 1
                else:
                    self.logger.info(f"✓ Invite created for {contact['name']}: {invite_data['invite_link'][:50]}...")
                    self.db.update_invite_status(contact_hash, 'created')
                    successful += 1
            
            except Exception as e:
                self.logger.error(f"Error processing contact: {str(e)}")
                failed += 1
        
        # Step 5: Complete run and return results
        self.db.update_run_stats(self.run_id, processed, successful, failed)
        self.db.complete_run(self.run_id)
        
        results = {
            'success': True,
            'run_id': self.run_id,
            'total_contacts': len(contacts),
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'skipped_duplicates': skipped_duplicates,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Workflow complete: {successful} successful, {failed} failed, {skipped_duplicates} duplicates")
        
        return results
    
    def get_run_status(self, run_id: str) -> Dict:
        """Get status of a specific run"""
        return self.db.get_run_stats(run_id)