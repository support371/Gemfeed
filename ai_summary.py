import os
import json
import logging
from google import genai
from google.genai import types

# IMPORTANT: KEEP THIS COMMENT - Using blueprint:python_gemini integration
# Using Gemini 2.5 models for AI summarization

# Initialize Gemini client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY not set - AI features will be disabled")
    gemini_client = None
else:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def generate_summary(title, summary):
    """Generate a Telegram-optimized summary using Gemini AI"""
    if not gemini_client:
        logging.warning("Gemini not configured - returning original summary")
        return summary or title
    
    try:
        # Create a prompt for Telegram-optimized content
        prompt = f"""
        Rewrite this cybersecurity RSS feed content for Telegram in a concise, professional, and engaging style:

        Title: {title}
        Summary: {summary}

        Requirements:
        - Maximum 280 characters
        - Include key cybersecurity insights
        - Use engaging language suitable for security professionals
        - Maintain professional tone
        - Add relevant security emojis if appropriate (🔒 🛡️ ⚠️ 🚨)
        - Focus on threat intelligence and actionable insights

        Return only the rewritten content, nothing else.
        """
        
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        if response.text:
            ai_summary = response.text.strip()
            logging.debug(f"Generated Gemini summary for: {title[:50]}...")
            return ai_summary
        else:
            logging.warning("Empty Gemini response received")
            return summary or title
        
    except Exception as e:
        logging.error(f"Error generating Gemini summary: {e}")
        # Fallback to original summary
        return summary or title

def analyze_content(title, summary):
    """Analyze cybersecurity content using Gemini AI"""
    if not gemini_client:
        return {
            'category': 'Security Alert',
            'sentiment': 'neutral',
            'confidence': 0.5
        }
    
    try:
        system_prompt = (
            "You are a cybersecurity content analysis expert. "
            "Analyze the content and categorize it appropriately for security professionals. "
            "Respond with JSON in this exact format: "
            "{'category': 'category_name', 'sentiment': 'positive/negative/neutral', 'confidence': 0.8}"
        )
        
        prompt = f"""
        Analyze this cybersecurity RSS feed content:

        Title: {title}
        Summary: {summary}

        Categories should be one of: Security Alert, Threat Intelligence, Vulnerability, Incident Response, Technology, Regulation, General
        Sentiment: positive (good security news), negative (threats/breaches), neutral (informational)
        Confidence: between 0 and 1
        """
        
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Content(role="user", parts=[types.Part(text=prompt)])
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json"
            )
        )
        
        if response.text:
            result = json.loads(response.text)
            
            # Validate and sanitize the response
            analysis = {
                'category': result.get('category', 'Security Alert'),
                'sentiment': result.get('sentiment', 'neutral'),
                'confidence': max(0, min(1, result.get('confidence', 0.5)))
            }
            
            logging.debug(f"Gemini analysis for '{title[:30]}...': {analysis}")
            return analysis
        else:
            logging.warning("Empty Gemini response received for content analysis")
            return {
                'category': 'Security Alert',
                'sentiment': 'neutral',
                'confidence': 0.5
            }
        
    except Exception as e:
        logging.error(f"Error analyzing content with Gemini: {e}")
        return {
            'category': 'Security Alert',
            'sentiment': 'neutral',
            'confidence': 0.5
        }

def generate_hashtags(title, summary, category):
    """Generate relevant cybersecurity hashtags using Gemini"""
    if not gemini_client:
        return f"#{category.lower().replace(' ', '')} #cybersecurity"
    
    try:
        prompt = f"""
        Generate 3-5 relevant cybersecurity hashtags for this content:

        Title: {title}
        Summary: {summary}
        Category: {category}

        Focus on cybersecurity, infosec, and threat intelligence hashtags.
        Return only the hashtags separated by spaces, starting with #.
        Keep hashtags concise and security-focused.
        """
        
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        if response.text:
            hashtags = response.text.strip()
            return hashtags
        else:
            logging.warning("Empty Gemini response received for hashtag generation")
            return f"#{category.lower().replace(' ', '')} #cybersecurity"
        
    except Exception as e:
        logging.error(f"Error generating hashtags with Gemini: {e}")
        return f"#{category.lower().replace(' ', '')} #cybersecurity"