import feedparser
import sqlite3
import logging
from datetime import datetime
from database import get_db_connection

def get_rss_feeds():
    """Get all active RSS feeds from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, name, active FROM rss_feeds WHERE active = 1")
        feeds = cursor.fetchall()
        conn.close()
        return feeds
    except Exception as e:
        logging.error(f"Error getting RSS feeds: {e}")
        return []

def add_rss_feed(url, name=None):
    """Add a new RSS feed"""
    try:
        # First validate the feed by trying to parse it
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            logging.warning(f"Invalid RSS feed: {url}")
            return False
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rss_feeds (url, name) VALUES (?, ?)
        """, (url, name or url))
        conn.commit()
        conn.close()
        
        logging.info(f"Added RSS feed: {name or url}")
        return True
    except sqlite3.IntegrityError:
        logging.warning(f"RSS feed already exists: {url}")
        return False
    except Exception as e:
        logging.error(f"Error adding RSS feed {url}: {e}")
        return False

def remove_rss_feed(feed_id):
    """Remove an RSS feed"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        logging.error(f"Error removing RSS feed {feed_id}: {e}")
        return False

def parse_single_feed(url, feed_name):
    """Parse a single RSS feed and return new items"""
    new_items = []
    try:
        logging.info(f"Parsing feed: {feed_name} ({url})")
        feed = feedparser.parse(url)
        
        if feed.bozo and not feed.entries:
            logging.warning(f"Could not parse feed {url}: {feed.bozo_exception}")
            return new_items
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for entry in feed.entries:
            try:
                # Extract entry data
                title = getattr(entry, 'title', 'No Title')
                summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
                link = getattr(entry, 'link', '')
                
                # Try to get publication date
                pub_date = ''
                if hasattr(entry, 'published'):
                    pub_date = entry.published
                elif hasattr(entry, 'updated'):
                    pub_date = entry.updated
                
                # Get category/tags
                category = 'General'
                if hasattr(entry, 'tags') and entry.tags:
                    category = entry.tags[0].term
                elif hasattr(entry, 'category'):
                    category = entry.category
                
                # Clean up summary (remove HTML tags if present)
                if summary:
                    import re
                    summary = re.sub('<[^<]+?>', '', summary)
                    summary = summary.strip()
                
                # Skip if essential fields are missing
                if not title or not link:
                    continue
                
                # Try to insert the item
                cursor.execute("""
                    INSERT INTO rss_items (title, summary, link, category, date, feed_source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, summary, link, category, pub_date, feed_name))
                
                new_items.append(title)
                logging.debug(f"Added item: {title}")
                
            except sqlite3.IntegrityError:
                # Item already exists (duplicate link), skip
                logging.debug(f"Skipping duplicate item: {getattr(entry, 'title', 'Unknown')}")
                continue
            except Exception as e:
                logging.error(f"Error processing feed entry: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        logging.info(f"Added {len(new_items)} new items from {feed_name}")
        return new_items
        
    except Exception as e:
        logging.error(f"Error parsing feed {url}: {e}")
        return new_items

def parse_feeds():
    """Parse all active RSS feeds and store new items"""
    total_new_items = 0
    feeds = get_rss_feeds()
    
    if not feeds:
        logging.warning("No active RSS feeds found")
        return total_new_items
    
    for feed in feeds:
        feed_id, url, name, active = feed
        if active:
            new_items = parse_single_feed(url, name or url)
            total_new_items += len(new_items)
    
    logging.info(f"Total new items added: {total_new_items}")
    return total_new_items

def get_feed_stats():
    """Get statistics about feeds and items"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count feeds
        cursor.execute("SELECT COUNT(*) FROM rss_feeds WHERE active = 1")
        active_feeds = cursor.fetchone()[0]
        
        # Count items by status
        cursor.execute("SELECT COUNT(*) FROM rss_items WHERE approved = 0")
        pending_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rss_items WHERE approved = 1")
        approved_items = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'active_feeds': active_feeds,
            'pending_items': pending_items,
            'approved_items': approved_items
        }
    except Exception as e:
        logging.error(f"Error getting feed stats: {e}")
        return {
            'active_feeds': 0,
            'pending_items': 0,
            'approved_items': 0
        }
