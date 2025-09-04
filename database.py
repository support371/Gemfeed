import sqlite3
import os
import logging
from models import get_schema

DATABASE_PATH = "database.db"

def get_db_connection():
    """Get a database connection with proper configuration"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_db():
    """Initialize the database with required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute schema creation
        for sql_command in get_schema():
            cursor.execute(sql_command)
        
        # Add some default RSS feeds if none exist
        cursor.execute("SELECT COUNT(*) FROM rss_feeds")
        feed_count = cursor.fetchone()[0]
        if feed_count == 0:
            default_feeds = [
                ("https://www.cisa.gov/news.xml", "CISA Security Advisories"),
                ("https://krebsonsecurity.com/feed/", "Krebs on Security"),
                ("https://feeds.feedburner.com/TheHackersNews", "The Hacker News"),
                ("https://www.darkreading.com/rss.xml", "Dark Reading"),
                ("https://www.bleepingcomputer.com/feed/", "Bleeping Computer"),
                ("https://threatpost.com/feed", "Threatpost"),
                ("https://www.securityweek.com/feed", "Security Week"),
            ]
            
            for url, name in default_feeds:
                try:
                    cursor.execute("""
                        INSERT INTO rss_feeds (url, name) VALUES (?, ?)
                    """, (url, name))
                except sqlite3.IntegrityError:
                    # Feed already exists, skip
                    pass
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise

def cleanup_old_items(days_old=30):
    """Remove old approved items to keep database size manageable"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM rss_items 
            WHERE approved = 1 
            AND created_at < datetime('now', '-{} days')
        """.format(days_old))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logging.info(f"Cleaned up {deleted_count} old items")
        
        return deleted_count
    except Exception as e:
        logging.error(f"Error cleaning up old items: {e}")
        return 0
