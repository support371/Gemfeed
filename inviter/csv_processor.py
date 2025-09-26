import csv
import logging
from typing import Dict, List, Optional
from .config import CSV_FIELD_MAPPING

class CSVProcessor:
    """Process CSV files and extract contact information"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_csv_file(self, file_path: str) -> List[Dict]:
        """Process a CSV file and extract contacts"""
        contacts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Detect delimiter
                sample = file.read(1024)
                file.seek(0)
                
                dialect = csv.Sniffer().sniff(sample)
                reader = csv.DictReader(file, dialect=dialect)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        contact = self.extract_contact_info(row)
                        if contact:
                            contact['row_number'] = row_num
                            contacts.append(contact)
                        else:
                            self.logger.warning(f"Row {row_num}: Could not extract valid contact info")
                    except Exception as e:
                        self.logger.error(f"Row {row_num}: Error processing - {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error reading CSV file {file_path}: {e}")
            raise
        
        self.logger.info(f"Processed {len(contacts)} contacts from {file_path}")
        return contacts
    
    def extract_contact_info(self, row: Dict) -> Optional[Dict]:
        """Extract and validate contact information from a CSV row"""
        contact = {}
        
        # Extract name
        name = self._extract_field(row, CSV_FIELD_MAPPING['name'])
        if not name:
            # Try combining first and last name
            first_name = self._get_field_value(row, ['FIRST_NAME'])
            last_name = self._get_field_value(row, ['LAST_NAME'])
            if first_name and last_name:
                name = f"{first_name} {last_name}"
            elif first_name:
                name = first_name
        
        if not name:
            return None
        
        # Extract email (required)
        email = self._extract_field(row, CSV_FIELD_MAPPING['email'])
        if not email or not self._is_valid_email(email):
            return None
        
        # Extract entity (required)
        entity = self._extract_field(row, CSV_FIELD_MAPPING['entity'])
        if not entity:
            return None
        
        # Extract region (optional)
        region = self._extract_field(row, CSV_FIELD_MAPPING['region'])
        
        contact = {
            'name': name.strip(),
            'email': email.strip().lower(),
            'entity': entity.strip(),
            'region': region.strip() if region else ''
        }
        
        return contact
    
    def _extract_field(self, row: Dict, field_options: List[str]) -> Optional[str]:
        """Extract a field value trying multiple column names"""
        for field_name in field_options:
            value = self._get_field_value(row, [field_name])
            if value:
                return value
        return None
    
    def _get_field_value(self, row: Dict, field_names: List[str]) -> Optional[str]:
        """Get field value with case-insensitive matching"""
        row_lower = {k.lower(): v for k, v in row.items()}
        
        for field_name in field_names:
            field_lower = field_name.lower()
            if field_lower in row_lower and row_lower[field_lower]:
                return str(row_lower[field_lower]).strip()
        
        return None
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        if not email or '@' not in email:
            return False
        
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        if not local or not domain or '.' not in domain:
            return False
        
        return True
    
    def validate_csv_structure(self, file_path: str) -> Dict:
        """Validate CSV structure and return analysis"""
        analysis = {
            'total_rows': 0,
            'valid_contacts': 0,
            'missing_name': 0,
            'missing_email': 0,
            'missing_entity': 0,
            'invalid_email': 0,
            'columns_found': [],
            'sample_contacts': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                sample = file.read(1024)
                file.seek(0)
                
                dialect = csv.Sniffer().sniff(sample)
                reader = csv.DictReader(file, dialect=dialect)
                
                analysis['columns_found'] = reader.fieldnames or []
                
                for row_num, row in enumerate(reader, 1):
                    analysis['total_rows'] += 1
                    
                    # Check for required fields
                    name = self._extract_field(row, CSV_FIELD_MAPPING['name'])
                    email = self._extract_field(row, CSV_FIELD_MAPPING['email'])
                    entity = self._extract_field(row, CSV_FIELD_MAPPING['entity'])
                    
                    if not name:
                        analysis['missing_name'] += 1
                    if not email:
                        analysis['missing_email'] += 1
                    elif not self._is_valid_email(email):
                        analysis['invalid_email'] += 1
                    if not entity:
                        analysis['missing_entity'] += 1
                    
                    # If valid contact, count it
                    if name and email and self._is_valid_email(email) and entity:
                        analysis['valid_contacts'] += 1
                        
                        # Add to sample (first 5 valid contacts)
                        if len(analysis['sample_contacts']) < 5:
                            region = self._extract_field(row, CSV_FIELD_MAPPING['region'])
                            analysis['sample_contacts'].append({
                                'name': name,
                                'email': email,
                                'entity': entity,
                                'region': region or 'N/A'
                            })
        
        except Exception as e:
            self.logger.error(f"Error validating CSV structure: {e}")
            analysis['error'] = str(e)
        
        return analysis