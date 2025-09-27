
import pandas as pd
import logging
from typing import List, Dict, Optional
from io import StringIO
from .config import CSV_FIELD_MAPPING

class CSVProcessor:
    """Process CSV files containing contact information"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_csv_upload(self, file_upload) -> List[Dict]:
        """Process uploaded CSV file and return list of contacts"""
        try:
            # Read CSV content
            content = file_upload.read().decode('utf-8')
            csv_data = pd.read_csv(StringIO(content))
            
            self.logger.info(f"Processing CSV with {len(csv_data)} rows")
            
            contacts = []
            for index, row in csv_data.iterrows():
                contact = self._extract_contact_info(row)
                if contact and self._validate_contact(contact):
                    contacts.append(contact)
                else:
                    self.logger.warning(f"Skipping invalid contact at row {index + 1}")
            
            self.logger.info(f"Successfully processed {len(contacts)} valid contacts")
            return contacts
            
        except Exception as e:
            self.logger.error(f"Error processing CSV: {e}")
            raise
    
    def _extract_contact_info(self, row: pd.Series) -> Optional[Dict]:
        """Extract contact information from CSV row"""
        try:
            contact = {}
            
            # Map name fields
            name_fields = CSV_FIELD_MAPPING.get('name', [])
            name_parts = []
            for field in name_fields:
                if field in row and pd.notna(row[field]):
                    name_parts.append(str(row[field]).strip())
            
            if name_parts:
                contact['name'] = ' '.join(name_parts)
            else:
                # Try common field names
                for field in ['name', 'full_name', 'contact_name']:
                    if field in row and pd.notna(row[field]):
                        contact['name'] = str(row[field]).strip()
                        break
            
            # Map email
            email_fields = CSV_FIELD_MAPPING.get('email', [])
            for field in email_fields:
                if field in row and pd.notna(row[field]):
                    contact['email'] = str(row[field]).strip().lower()
                    break
            else:
                # Try common field names
                for field in ['email', 'email_address', 'e_mail']:
                    if field in row and pd.notna(row[field]):
                        contact['email'] = str(row[field]).strip().lower()
                        break
            
            # Map entity
            entity_fields = CSV_FIELD_MAPPING.get('entity', [])
            entity_parts = []
            for field in entity_fields:
                if field in row and pd.notna(row[field]):
                    entity_parts.append(str(row[field]).strip())
            
            if entity_parts:
                contact['entity'] = ' - '.join(entity_parts)
            else:
                # Try common field names
                for field in ['entity', 'company', 'organization', 'org']:
                    if field in row and pd.notna(row[field]):
                        contact['entity'] = str(row[field]).strip()
                        break
                else:
                    contact['entity'] = 'Unknown Entity'
            
            # Map region
            region_fields = CSV_FIELD_MAPPING.get('region', [])
            for field in region_fields:
                if field in row and pd.notna(row[field]):
                    contact['region'] = str(row[field]).strip()
                    break
            else:
                # Try common field names
                for field in ['region', 'state', 'location']:
                    if field in row and pd.notna(row[field]):
                        contact['region'] = str(row[field]).strip()
                        break
                else:
                    contact['region'] = ''
            
            return contact if contact.get('name') and contact.get('email') else None
            
        except Exception as e:
            self.logger.error(f"Error extracting contact info: {e}")
            return None
    
    def _validate_contact(self, contact: Dict) -> bool:
        """Validate contact information"""
        # Check required fields
        if not contact.get('name') or not contact.get('email'):
            return False
        
        # Basic email validation
        email = contact['email']
        if '@' not in email or '.' not in email.split('@')[1]:
            return False
        
        return True
    
    def get_csv_preview(self, file_upload, max_rows: int = 5) -> Dict:
        """Get preview of CSV file for validation"""
        try:
            content = file_upload.read().decode('utf-8')
            file_upload.seek(0)  # Reset file pointer
            
            csv_data = pd.read_csv(StringIO(content))
            
            preview = {
                'total_rows': len(csv_data),
                'columns': list(csv_data.columns),
                'sample_rows': csv_data.head(max_rows).to_dict('records'),
                'detected_fields': self._detect_fields(csv_data.columns)
            }
            
            return preview
            
        except Exception as e:
            self.logger.error(f"Error creating CSV preview: {e}")
            return {'error': str(e)}
    
    def _detect_fields(self, columns: List[str]) -> Dict:
        """Detect which columns contain which type of information"""
        detected = {
            'name': [],
            'email': [],
            'entity': [],
            'region': []
        }
        
        columns_lower = [col.lower() for col in columns]
        
        for field_type, field_patterns in CSV_FIELD_MAPPING.items():
            for pattern in field_patterns:
                if pattern.lower() in columns_lower:
                    idx = columns_lower.index(pattern.lower())
                    detected[field_type].append(columns[idx])
        
        return detected
