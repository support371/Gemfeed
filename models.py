"""Database models and schema definitions"""

def get_schema():
    """Returns the database schema as SQL commands compatible with PostgreSQL"""
    return [
        """
        CREATE TABLE IF NOT EXISTS rss_feeds (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            name TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS rss_items (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT,
            link TEXT UNIQUE NOT NULL,
            category TEXT DEFAULT 'General',
            date TEXT,
            approved BOOLEAN DEFAULT FALSE,
            ai_suggestion TEXT,
            feed_source TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_rss_items_approved ON rss_items(approved)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_rss_items_date ON rss_items(date DESC)
        """
    ]
