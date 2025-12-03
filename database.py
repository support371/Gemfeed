import psycopg2
import psycopg2.extras
import os
import logging
from models import get_schema

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    """Get a PostgreSQL database connection"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Initialize the database with required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute schema creation
        for sql_command in get_schema():
            if sql_command.strip(): # Avoid executing empty commands
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
                    cursor.execute(
                        "INSERT INTO rss_feeds (url, name) VALUES (%s, %s)",
                        (url, name)
                    )
                except psycopg2.IntegrityError:
                    # Feed already exists, skip
                    conn.rollback() # Rollback the failed transaction
                    pass
        
        conn.commit()
        cursor.close()
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
        cursor.execute(
            "DELETE FROM rss_items WHERE approved = TRUE AND created_at < NOW() - INTERVAL '%s days'",
            (days_old,)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if deleted_count > 0:
            logging.info(f"Cleaned up {deleted_count} old items")
        
        return deleted_count
    except Exception as e:
        logging.error(f"Error cleaning up old items: {e}")
        return 0
