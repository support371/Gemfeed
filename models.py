"""Database models and schema definitions"""

def get_schema():
    """Returns the database schema as SQL commands"""
    return [
        """
        CREATE TABLE IF NOT EXISTS rss_feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            name TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS rss_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            link TEXT UNIQUE NOT NULL,
            category TEXT DEFAULT 'General',
            date TEXT,
            approved INTEGER DEFAULT 0,
            ai_suggestion TEXT,
            feed_source TEXT,
            quality_score INTEGER DEFAULT 5,
            image_url TEXT,
            time_ago TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_rss_items_approved ON rss_items(approved)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_rss_items_date ON rss_items(date DESC)
        """,
        """
        CREATE TABLE IF NOT EXISTS social_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            content_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            external_post_id TEXT,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error TEXT
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_social_posts_dedupe ON social_posts(platform, content_id)
        """
    ]
