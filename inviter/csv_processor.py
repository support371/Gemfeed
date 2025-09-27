
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
import csv
import io
import logging
from typing import List, Dict, Optional
from .config import CSV_FIELD_MAPPING

class CSVProcessor:
    """Handles CSV file processing for bulk invitations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_csv_upload(self, file) -> List[Dict]:
        """Process uploaded CSV file and extract contact information"""
        contacts = []
        
        try:
            # Read file content
            file_content = file.read().decode('utf-8')
            file.seek(0)  # Reset file pointer
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    contact = self._extract_contact_from_row(row)
                    if contact and contact.get('email'):
                        contacts.append(contact)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing row {row_num}: {e}")
                    continue
            
            self.logger.info(f"Successfully processed {len(contacts)} contacts from CSV")
            return contacts
            
        except Exception as e:
            self.logger.error(f"Error processing CSV file: {e}")
            return []
    
    def _extract_contact_from_row(self, row: Dict) -> Optional[Dict]:
        """Extract contact information from CSV row"""
        contact = {}
        
        # Map CSV fields to contact fields
        for contact_field, csv_fields in CSV_FIELD_MAPPING.items():
            value = None
            
            # Try each possible CSV field name
            for csv_field in csv_fields:
                if csv_field in row and row[csv_field]:
                    value = row[csv_field].strip()
                    break
            
            if value:
                contact[contact_field] = value
        
        # Handle special cases
        if 'name' not in contact:
            # Try to construct name from first/last
            first_name = ''
            last_name = ''
            
            for field in row:
                if 'FIRST' in field.upper():
                    first_name = row[field].strip()
                elif 'LAST' in field.upper():
                    last_name = row[field].strip()
            
            if first_name or last_name:
                contact['name'] = f"{first_name} {last_name}".strip()
        
        # Validate required fields
        if not contact.get('email'):
            return None
        
        # Set defaults
        if not contact.get('name'):
            contact['name'] = contact['email'].split('@')[0].title()
        
        return contact
    
    def validate_csv_format(self, file) -> Tuple[bool, str, List[str]]:
        """Validate CSV format and return available fields"""
        try:
            file_content = file.read().decode('utf-8')
            file.seek(0)  # Reset file pointer
            
            csv_reader = csv.DictReader(io.StringIO(file_content))
            fieldnames = csv_reader.fieldnames or []
            
            # Check if we can find required fields
            found_email = False
            for field in fieldnames:
                if any(email_field in field.upper() for email_field in CSV_FIELD_MAPPING['email']):
                    found_email = True
                    break
            
            if not found_email:
                return False, "No email field found in CSV", fieldnames
            
            return True, "CSV format is valid", fieldnames
            
        except Exception as e:
            return False, f"Error validating CSV: {str(e)}", []
