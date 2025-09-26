import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class InviteDatabase:
    """Local SQLite database for tracking invites and deduplication"""
    
    def __init__(self, db_path='inviter/invites.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create invites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                entity TEXT,
                region TEXT,
                invite_id TEXT,
                invite_link TEXT,
                expire_date TEXT,
                delivery_channel TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                run_id TEXT,
                error_text TEXT
            )
        ''')
        
        # Create runs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                csv_filename TEXT,
                total_contacts INTEGER DEFAULT 0,
                processed_contacts INTEGER DEFAULT 0,
                successful_invites INTEGER DEFAULT 0,
                failed_invites INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contact_hash ON invites(contact_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON invites(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_run_id ON invites(run_id)')
        
        conn.commit()
        conn.close()
    
    def generate_contact_hash(self, email: str, entity: str) -> str:
        """Generate a stable hash for contact deduplication"""
        key = f"{email.lower().strip()}||{entity.strip()}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def contact_exists(self, email: str, entity: str) -> bool:
        """Check if contact has already been processed"""
        contact_hash = self.generate_contact_hash(email, entity)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM invites WHERE contact_hash = ?', (contact_hash,))
        exists = cursor.fetchone() is not None
        conn.close()
        
        return exists
    
    def add_invite_record(self, contact: Dict, run_id: str, invite_data: Optional[Dict] = None) -> str:
        """Add a new invite record"""
        contact_hash = self.generate_contact_hash(contact['email'], contact['entity'])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prepare data
        expire_date = None
        if invite_data and 'expire_date' in invite_data:
            expire_date = invite_data['expire_date']
        
        cursor.execute('''
            INSERT OR REPLACE INTO invites 
            (contact_hash, name, email, entity, region, invite_id, invite_link, 
             expire_date, delivery_channel, status, run_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            contact_hash,
            contact['name'],
            contact['email'],
            contact['entity'],
            contact.get('region', ''),
            invite_data.get('invite_id') if invite_data else None,
            invite_data.get('invite_link') if invite_data else None,
            expire_date,
            invite_data.get('delivery_channel') if invite_data else None,
            invite_data.get('status', 'pending') if invite_data else 'pending',
            run_id,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return contact_hash
    
    def update_invite_status(self, contact_hash: str, status: str, error_text: str = None):
        """Update invite status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE invites 
            SET status = ?, error_text = ?, updated_at = ?
            WHERE contact_hash = ?
        ''', (status, error_text or '', datetime.now().isoformat(), contact_hash))
        
        conn.commit()
        conn.close()
    
    def get_invite_by_link(self, invite_link: str) -> Optional[Dict]:
        """Get invite record by invite link"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM invites WHERE invite_link = ?', (invite_link,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        
        return None
    
    def create_run(self, run_id: str, csv_filename: str, total_contacts: int):
        """Create a new run record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO runs (run_id, csv_filename, total_contacts)
            VALUES (?, ?, ?)
        ''', (run_id, csv_filename, total_contacts))
        
        conn.commit()
        conn.close()
    
    def update_run_stats(self, run_id: str, processed: int, successful: int, failed: int):
        """Update run statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE runs 
            SET processed_contacts = ?, successful_invites = ?, failed_invites = ?
            WHERE run_id = ?
        ''', (processed, successful, failed, run_id))
        
        conn.commit()
        conn.close()
    
    def complete_run(self, run_id: str, status: str = 'completed'):
        """Mark run as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE runs 
            SET status = ?, completed_at = ?
            WHERE run_id = ?
        ''', (status, datetime.now().isoformat(), run_id))
        
        conn.commit()
        conn.close()
    
    def get_run_stats(self, run_id: str) -> Optional[Dict]:
        """Get run statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM runs WHERE run_id = ?', (run_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        
        conn.close()
        return None