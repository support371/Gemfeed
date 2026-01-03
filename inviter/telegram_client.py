import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from .config import (
    TELEGRAM_BOT_TOKEN, TARGET_GROUP_CHAT_ID, MAX_API_CALLS_PER_MINUTE,
    INVITE_EXPIRE_DAYS, INVITE_MEMBER_LIMIT, ADMIN_TELEGRAM_ID
)

class TelegramClient:
    """Telegram API client with rate limiting and error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_base = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        self.last_call_time = 0
        self.call_count = 0
        self.minute_start = time.time()
        
    def _enforce_rate_limit(self):
        """Enforce rate limiting of API calls"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.minute_start >= 60:
            self.call_count = 0
            self.minute_start = current_time
        
        # Check if we've hit the rate limit
        if self.call_count >= MAX_API_CALLS_PER_MINUTE:
            sleep_time = 60 - (current_time - self.minute_start)
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached. Sleeping for {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                self.call_count = 0
                self.minute_start = time.time()
        
        # Minimum delay between calls (1.5 seconds to be safe)
        time_since_last = current_time - self.last_call_time
        if time_since_last < 1.5:
            time.sleep(1.5 - time_since_last)
        
        self.call_count += 1
        self.last_call_time = time.time()
    
    def create_invite_link(self, entity_name: str) -> Tuple[bool, Dict]:
        """Create a single-use invite link for the target group"""
        self._enforce_rate_limit()
        
        expire_date = int((datetime.now() + timedelta(days=INVITE_EXPIRE_DAYS)).timestamp())
        
        url = f"{self.api_base}/createChatInviteLink"
        data = {
            'chat_id': TARGET_GROUP_CHAT_ID,
            'name': f"GÉM Invite - {entity_name}",
            'expire_date': expire_date,
            'member_limit': INVITE_MEMBER_LIMIT,
            'creates_join_request': False  # Direct join, no approval needed
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 429:
                # Rate limited by Telegram
                retry_after = int(response.headers.get('Retry-After', 60))
                self.logger.warning(f"Telegram rate limit hit. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.create_invite_link(entity_name)  # Retry
            
            if response.status_code == 200:
                result = response.json()
                if result['ok']:
                    invite_data = result['result']
                    self.logger.debug(f"Created invite link for {entity_name}: {invite_data['invite_link']}")
                    return True, {
                        'invite_link': invite_data['invite_link'],
                        'invite_id': invite_data.get('invite_link', '').split('/')[-1],
                        'expire_date': datetime.fromtimestamp(expire_date).isoformat(),
                        'member_limit': INVITE_MEMBER_LIMIT
                    }
                else:
                    error_msg = result.get('description', 'Unknown error')
                    self.logger.error(f"Telegram API error creating invite: {error_msg}")
                    return False, {'error': error_msg}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.logger.error(f"HTTP error creating invite: {error_msg}")
                return False, {'error': error_msg}
                
        except Exception as e:
            error_msg = f"Exception creating invite: {str(e)}"
            self.logger.error(error_msg)
            return False, {'error': error_msg}
    
    def send_message(self, chat_id: str, message: str, parse_mode: str = 'Markdown') -> bool:
        """Send a message to a chat"""
        self._enforce_rate_limit()
        
        url = f"{self.api_base}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                self.logger.warning(f"Message rate limit hit. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.send_message(chat_id, message, parse_mode)  # Retry
            
            if response.status_code == 200:
                result = response.json()
                return result['ok']
            else:
                self.logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception sending message: {e}")
            return False
    
    def test_bot_permissions(self) -> Tuple[bool, str]:
        """Test if bot has required permissions in target group"""
        self._enforce_rate_limit()
        
        try:
            # Get bot info in the target chat
            url = f"{self.api_base}/getChatMember"
            data = {
                'chat_id': TARGET_GROUP_CHAT_ID,
                'user_id': TELEGRAM_BOT_TOKEN.split(':')[0]  # Bot ID from token
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result['ok']:
                    member_info = result['result']
                    status = member_info['status']
                    
                    if status != 'administrator':
                        return False, f"Bot is not an administrator (status: {status})"
                    
                    # Check if bot can invite users
                    can_invite = member_info.get('can_invite_users', False)
                    if not can_invite:
                        return False, "Bot does not have permission to invite users"
                    
                    return True, "Bot has required permissions"
                else:
                    return False, f"API error: {result.get('description', 'Unknown')}"
            else:
                return False, f"HTTP error: {response.status_code}"
                
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def send_admin_alert(self, message: str) -> bool:
        """Send alert to admin"""
        if ADMIN_TELEGRAM_ID:
            alert_message = f"🚨 **GÉM Invite System Alert**\\n\\n{message}"
            return self.send_message(ADMIN_TELEGRAM_ID, alert_message)
        return False
    
    def get_chat_info(self, chat_id: str = None) -> Optional[Dict]:
        """Get information about a chat"""
        target_chat = chat_id or TARGET_GROUP_CHAT_ID
        if not target_chat:
            return None
        
        self._enforce_rate_limit()
        
        url = f"{self.api_base}/getChat"
        data = {'chat_id': target_chat}
        
        try:
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result['ok']:
                    return result['result']
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting chat info: {e}")
            return None