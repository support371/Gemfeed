import os
import requests
import logging
from urllib.parse import quote

# Get Telegram configuration from environment
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_to_telegram(title, content, link):
    """Send a message to Telegram channel/chat"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logging.error("Telegram bot token or chat ID not configured")
        return False
    
    try:
        # Format the message with proper Telegram markdown
        message = f"*{title}*\n\n{content}\n\n[Read more →]({link})"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logging.info(f"Successfully sent message to Telegram: {title[:50]}...")
                return True
            else:
                logging.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                return False
        else:
            logging.error(f"HTTP error sending to Telegram: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error sending to Telegram: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error sending to Telegram: {e}")
        return False

def test_telegram_connection():
    """Test the Telegram bot connection"""
    if not TELEGRAM_TOKEN:
        return False, "Bot token not configured"
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                bot_info = result.get("result", {})
                bot_name = bot_info.get("username", "Unknown")
                return True, f"Connected to bot: @{bot_name}"
            else:
                return False, f"API error: {result.get('description', 'Unknown error')}"
        else:
            return False, f"HTTP error: {response.status_code}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def get_chat_info():
    """Get information about the configured chat"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return None
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat"
        data = {"chat_id": CHAT_ID}
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                return result.get("result", {})
        
        return None
        
    except Exception as e:
        logging.error(f"Error getting chat info: {e}")
        return None

def send_test_message():
    """Send a test message to verify configuration"""
    test_title = "🧪 Test Message"
    test_content = "This is a test message from your RSS Curation System. If you see this, everything is working correctly!"
    test_link = "https://github.com"
    
    return send_to_telegram(test_title, test_content, test_link)
