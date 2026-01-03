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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_rss_items_approved ON rss_items(approved)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_rss_items_date ON rss_items(date DESC)
        """
    ]
