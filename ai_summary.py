import os
import json
import logging
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.warning("OPENAI_API_KEY not set - AI features will be disabled")
    openai_client = None
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_summary(title, summary):
    """Generate a Telegram-optimized summary using AI"""
    if not openai_client:
        logging.warning("OpenAI not configured - returning original summary")
        return summary or title
    
    try:
        # Create a prompt for Telegram-optimized content
        prompt = f"""
        Rewrite this RSS feed content for Telegram in a concise, professional, and engaging style:

        Title: {title}
        Summary: {summary}

        Requirements:
        - Maximum 280 characters
        - Include key points and insights
        - Use engaging language suitable for social media
        - Maintain professional tone
        - Add relevant emojis if appropriate
        - End with a call-to-action if relevant

        Return only the rewritten content, nothing else.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        
        content = response.choices[0].message.content
        if content:
            ai_summary = content.strip()
            logging.debug(f"Generated AI summary for: {title[:50]}...")
            return ai_summary
        else:
            logging.warning("Empty AI response received")
            return summary or title
        
    except Exception as e:
        logging.error(f"Error generating AI summary: {e}")
        # Fallback to original summary
        return summary or title

def analyze_content(title, summary):
    """Analyze content and provide categorization and sentiment"""
    if not openai_client:
        return {
            'category': 'General',
            'sentiment': 'neutral',
            'confidence': 0.5
        }
    
    try:
        prompt = f"""
        Analyze this RSS feed content and provide categorization and sentiment analysis:

        Title: {title}
        Summary: {summary}

        Please respond with JSON in this exact format:
        {{
            "category": "category_name",
            "sentiment": "positive/negative/neutral",
            "confidence": 0.8
        }}

        Categories should be one of: Technology, Business, Science, Politics, Sports, Entertainment, Health, General
        Sentiment should be: positive, negative, or neutral
        Confidence should be between 0 and 1
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=150,
            temperature=0.3,
        )
        
        content = response.choices[0].message.content
        if not content:
            logging.warning("Empty AI response received for content analysis")
            return {
                'category': 'General',
                'sentiment': 'neutral',
                'confidence': 0.5
            }
        result = json.loads(content)
        
        # Validate and sanitize the response
        analysis = {
            'category': result.get('category', 'General'),
            'sentiment': result.get('sentiment', 'neutral'),
            'confidence': max(0, min(1, result.get('confidence', 0.5)))
        }
        
        logging.debug(f"Content analysis for '{title[:30]}...': {analysis}")
        return analysis
        
    except Exception as e:
        logging.error(f"Error analyzing content: {e}")
        return {
            'category': 'General',
            'sentiment': 'neutral',
            'confidence': 0.5
        }

def generate_hashtags(title, summary, category):
    """Generate relevant hashtags for the content"""
    if not openai_client:
        return f"#{category.lower().replace(' ', '')}"
    
    try:
        prompt = f"""
        Generate 3-5 relevant hashtags for this content:

        Title: {title}
        Summary: {summary}
        Category: {category}

        Return only the hashtags separated by spaces, starting with #.
        Keep hashtags concise and relevant.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.5,
        )
        
        content = response.choices[0].message.content
        if content:
            hashtags = content.strip()
            return hashtags
        else:
            logging.warning("Empty AI response received for hashtag generation")
            return f"#{category.lower().replace(' ', '')}"
        
    except Exception as e:
        logging.error(f"Error generating hashtags: {e}")
        return f"#{category.lower().replace(' ', '')}"
