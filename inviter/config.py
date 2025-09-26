import os
import logging

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TARGET_GROUP_CHAT_ID = os.environ.get("TARGET_GROUP_CHAT_ID")  # -100XXXXXXXXXX format
ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID", "7700844581")  # For alerts

# Rate Limiting
MAX_API_CALLS_PER_MINUTE = 40
INVITE_EXPIRE_DAYS = 7
INVITE_MEMBER_LIMIT = 1

# Email Configuration (for sending invite links)
EMAIL_SERVICE = os.environ.get("EMAIL_SERVICE", "sendgrid")  # sendgrid, mailgun, smtp
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "invites@gemsecurity.com")
FROM_NAME = os.environ.get("FROM_NAME", "GÉM Security Team")

# Logging Configuration (Google Sheets or Airtable)
LOGGING_SERVICE = os.environ.get("LOGGING_SERVICE", "sheets")  # sheets, airtable
GOOGLE_SHEETS_URL = os.environ.get("GOOGLE_SHEETS_URL")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.environ.get("AIRTABLE_TABLE_NAME", "InviteLog")

# Compliance Settings
TEST_MODE = os.environ.get("TEST_MODE", "true").lower() == "true"
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

# Validation
def validate_config():
    """Validate required configuration"""
    errors = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is required")
    
    if not TARGET_GROUP_CHAT_ID:
        errors.append("TARGET_GROUP_CHAT_ID is required")
    
    if EMAIL_SERVICE == "sendgrid" and not SENDGRID_API_KEY:
        errors.append("SENDGRID_API_KEY is required when using SendGrid")
    
    if LOGGING_SERVICE == "sheets" and not GOOGLE_SHEETS_URL:
        errors.append("GOOGLE_SHEETS_URL is required when using Google Sheets")
    
    if LOGGING_SERVICE == "airtable" and (not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID):
        errors.append("AIRTABLE_API_KEY and AIRTABLE_BASE_ID are required when using Airtable")
    
    if errors:
        logging.error(f"Configuration errors: {', '.join(errors)}")
        return False
    
    return True

# CSV Field Mapping
CSV_FIELD_MAPPING = {
    'name': ['PRINCIPAL_NAME', 'FIRST_NAME', 'LAST_NAME'],
    'email': ['EMAIL'],
    'entity': ['ENTITY_NAME', 'ENTITY_NUM'],
    'region': ['PHYSICAL_STATE', 'STATE']
}