
import os
import logging
import requests
from datetime import datetime

class NewsdataAPI:
    """Integration with Newsdata.io API for fetching cybersecurity news"""
    
    def __init__(self):
        self.api_key = os.environ.get('NEWSDATA_API_KEY', 'pub_a1ed43019bd645c2975638ce795bcf5a')
        self.base_url = "https://newsdata.io/api/1/news"
        
    def fetch_cybersecurity_news(self, categories=None):
        """
        Fetch cybersecurity and related news from Newsdata.io
        
        Args:
            categories: Optional list of specific categories to filter
            
        Returns:
            list: List of news articles or empty list on error
        """
        try:
            # Define search query focusing on cybersecurity and related topics
            query = "cybersecurity OR AI innovation OR Real Estate Investing OR Business management OR financial management"
            
            params = {
                'apikey': self.api_key,
                'q': query,
                'language': 'en'
            }
            
            logging.info(f"Fetching news from Newsdata.io with query: {query}")
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success' and 'results' in data:
                    articles = data['results']
                    logging.info(f"Successfully fetched {len(articles)} articles from Newsdata.io")
                    return articles
                else:
                    logging.warning(f"Newsdata.io returned unexpected format: {data}")
                    return []
            else:
                logging.error(f"Newsdata.io API error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching news from Newsdata.io: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error in Newsdata.io integration: {e}")
            return []
    
    def import_to_database(self, conn):
        """
        Fetch news from Newsdata.io and import to database
        
        Args:
            conn: Database connection
            
        Returns:
            int: Number of new items added
        """
        articles = self.fetch_cybersecurity_news()
        
        if not articles:
            logging.warning("No articles fetched from Newsdata.io")
            return 0
        
        cursor = conn.cursor()
        new_items = 0
        
        for article in articles:
            try:
                title = article.get('title', 'No Title')
                description = article.get('description', article.get('content', ''))
                link = article.get('link', '')
                
                # Get publication date
                pub_date = article.get('pubDate', datetime.now().isoformat())
                
                # Determine category from article keywords or category
                category = 'Cybersecurity News'
                if article.get('category'):
                    categories = article['category']
                    if isinstance(categories, list) and categories:
                        category = categories[0].title()
                
                # Get source name
                source = article.get('source_id', 'Newsdata.io')
                
                # Skip if essential fields are missing
                if not title or not link:
                    continue
                
                # Try to insert the item
                cursor.execute("""
                    INSERT INTO rss_items (title, summary, link, category, date, feed_source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, description, link, category, pub_date, f"Newsdata.io - {source}"))
                
                new_items += 1
                logging.debug(f"Added article: {title}")
                
            except Exception as e:
                # Skip duplicates or errors
                logging.debug(f"Skipping article: {str(e)}")
                continue
        
        conn.commit()
        logging.info(f"Imported {new_items} new articles from Newsdata.io")
        return new_items
