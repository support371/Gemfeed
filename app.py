import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import init_db, get_db_connection
from rss_parser import parse_feeds, get_rss_feeds, add_rss_feed, remove_rss_feed
from ai_summary import generate_summary
from telegram_bot import send_to_telegram

# --- New imports for invitation system ---
from inviter.telegram_client import TelegramClient
from inviter.config import validate_config
# --- End new imports ---

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize database
init_db()

@app.route('/')
def landing():
    """Official landing page showcasing the RSS curation system"""
    return render_template('landing.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard showing RSS items for review"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all RSS items, ordered by date (newest first)
        cursor.execute("""
            SELECT id, title, summary, link, category, date, approved, ai_suggestion, feed_source
            FROM rss_items 
            ORDER BY date DESC, id DESC
        """)
        items = cursor.fetchall()
        conn.close()

        # Convert to list of dicts for easier template handling
        items_list = []
        for item in items:
            items_list.append({
                'id': item[0],
                'title': item[1],
                'summary': item[2],
                'link': item[3],
                'category': item[4],
                'date': item[5],
                'approved': item[6],
                'ai_suggestion': item[7],
                'feed_source': item[8]
            })

        return render_template('dashboard.html', items=items_list)
    except Exception as e:
        logging.error(f"Error in dashboard: {e}")
        flash(f"Error loading dashboard: {str(e)}", 'danger')
        return render_template('dashboard.html', items=[])

@app.route('/generate_suggestion/<int:item_id>')
def generate_suggestion(item_id):
    """Generate AI suggestion for a specific item"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the item
        cursor.execute("SELECT title, summary FROM rss_items WHERE id = ?", (item_id,))
        item = cursor.fetchone()

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Generate AI suggestion
        ai_text = generate_summary(item[0], item[1])

        # Update the item with the suggestion
        cursor.execute("""
            UPDATE rss_items SET ai_suggestion = ? WHERE id = ?
        """, (ai_text, item_id))
        conn.commit()
        conn.close()

        return jsonify({'suggestion': ai_text})
    except Exception as e:
        logging.error(f"Error generating suggestion: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/approve/<int:item_id>', methods=['POST'])
def approve(item_id):
    """Approve an item and send to Telegram"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the item details
        cursor.execute("""
            SELECT title, summary, link, ai_suggestion 
            FROM rss_items WHERE id = ?
        """, (item_id,))
        item = cursor.fetchone()

        if not item:
            flash('Item not found', 'danger')
            return redirect(url_for('dashboard'))

        # Use AI suggestion if available, otherwise original summary
        content_to_send = item[3] if item[3] else item[1]

        # Send to Telegram
        success = send_to_telegram(item[0], content_to_send, item[2])

        if success:
            # Mark as approved
            cursor.execute("UPDATE rss_items SET approved = 1 WHERE id = ?", (item_id,))
            conn.commit()
            flash('Item approved and sent to Telegram!', 'success')
        else:
            flash('Failed to send to Telegram', 'danger')

        conn.close()
        return redirect(url_for('dashboard'))
    except Exception as e:
        logging.error(f"Error approving item: {e}")
        flash(f'Error approving item: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/reject/<int:item_id>', methods=['POST'])
def reject(item_id):
    """Reject an item (delete it)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rss_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        flash('Item rejected and removed', 'info')
        return redirect(url_for('dashboard'))
    except Exception as e:
        logging.error(f"Error rejecting item: {e}")
        flash(f'Error rejecting item: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/feeds')
def manage_feeds():
    """RSS feed management page"""
    feeds = get_rss_feeds()
    return render_template('feeds.html', feeds=feeds)

@app.route('/add_feed', methods=['POST'])
def add_feed():
    """Add a new RSS feed"""
    feed_url = request.form.get('feed_url', '').strip()
    feed_name = request.form.get('feed_name', '').strip()

    if not feed_url:
        flash('Feed URL is required', 'danger')
        return redirect(url_for('manage_feeds'))

    try:
        success = add_rss_feed(feed_url, feed_name)
        if success:
            flash(f'Feed "{feed_name or feed_url}" added successfully!', 'success')
        else:
            flash('Failed to add feed - please check the URL', 'danger')
    except Exception as e:
        logging.error(f"Error adding feed: {e}")
        flash(f'Error adding feed: {str(e)}', 'danger')

    return redirect(url_for('manage_feeds'))

@app.route('/remove_feed/<int:feed_id>', methods=['POST'])
def remove_feed(feed_id):
    """Remove an RSS feed"""
    try:
        success = remove_rss_feed(feed_id)
        if success:
            flash('Feed removed successfully!', 'success')
        else:
            flash('Failed to remove feed', 'danger')
    except Exception as e:
        logging.error(f"Error removing feed: {e}")
        flash(f'Error removing feed: {str(e)}', 'danger')

    return redirect(url_for('manage_feeds'))

@app.route('/refresh_feeds', methods=['POST'])
def refresh_feeds():
    """Manually refresh all RSS feeds"""
    try:
        new_items = parse_feeds()
        flash(f'Feeds refreshed! Found {new_items} new items.', 'success')
    except Exception as e:
        logging.error(f"Error refreshing feeds: {e}")
        flash(f'Error refreshing feeds: {str(e)}', 'danger')

    return redirect(url_for('dashboard'))

@app.route('/test_telegram')
def test_telegram():
    """Test endpoint for Telegram integration"""
    from telegram_bot import test_telegram_connection, send_test_message

    # Test connection
    is_connected, message = test_telegram_connection()

    if is_connected:
        # Try sending a test message
        if send_test_message():
            flash("✅ Telegram test successful! Check your channel for the test message.", "success")
        else:
            flash("⚠️ Connected to Telegram but failed to send message. Check your chat ID.", "warning")
    else:
        flash(f"❌ Telegram connection failed: {message}", "error")

    return redirect(url_for('dashboard'))

@app.route('/invitations')
def invitations():
    """Invitation management dashboard"""
    # Get invitation statistics from database
    conn = get_db_connection()
    try:
        # Check if invitations table exists, create if not
        conn.execute('''
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                entity TEXT,
                region TEXT,
                invite_link TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                error_message TEXT
            )
        ''')

        # Get recent invitations
        recent_invites = conn.execute('''
            SELECT * FROM invitations 
            ORDER BY created_at DESC 
            LIMIT 50
        ''').fetchall()

        # Get statistics
        stats = conn.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as errors
            FROM invitations
        ''').fetchone()

        conn.commit()
    finally:
        conn.close()

    return render_template('invitations.html', 
                         recent_invites=recent_invites,
                         stats=stats)

@app.route('/invite_single', methods=['POST'])
def invite_single():
    """Send single invitation"""
    name = request.form.get('name')
    email = request.form.get('email')
    entity = request.form.get('entity', '')

    if not name or not email:
        flash("Name and email are required", "error")
        return redirect(url_for('invitations'))

    # Validate configuration
    if not validate_config():
        flash("Invitation system not properly configured. Check environment variables.", "error")
        return redirect(url_for('invitations'))

    try:
        telegram_client = TelegramClient()

        # Create invite link
        success, result = telegram_client.create_invite_link(entity or name)

        if success:
            invite_link = result.get('invite_link')

            # Store in database
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO invitations 
                    (name, email, entity, invite_link, status) 
                    VALUES (?, ?, ?, ?, 'created')
                ''', (name, email, entity, invite_link))
                conn.commit()
            finally:
                conn.close()

            # Send email (you'll need to implement email sending)
            flash(f"✅ Invitation created for {name}. Link: {invite_link}", "success")
        else:
            error_msg = result.get('description', 'Unknown error')

            # Store error in database
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO invitations 
                    (name, email, entity, status, error_message) 
                    VALUES (?, ?, ?, 'error', ?)
                ''', (name, email, entity, error_msg))
                conn.commit()
            finally:
                conn.close()

            flash(f"❌ Failed to create invitation: {error_msg}", "error")

    except Exception as e:
        flash(f"❌ Error creating invitation: {str(e)}", "error")

    return redirect(url_for('invitations'))

@app.route('/test_inviter')
def test_inviter():
    """Test the invitation system configuration"""
    if not validate_config():
        flash("❌ Invitation system configuration incomplete. Check environment variables.", "error")
        return redirect(url_for('invitations'))

    try:
        telegram_client = TelegramClient()

        # Test bot permissions
        success, message = telegram_client.test_bot_permissions()

        if success:
            flash(f"✅ Invitation system test passed: {message}", "success")
        else:
            flash(f"❌ Invitation system test failed: {message}", "error")

    except Exception as e:
        flash(f"❌ Error testing invitation system: {str(e)}", "error")

    return redirect(url_for('invitations'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('dashboard.html', items=[]), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {error}")
    return render_template('dashboard.html', items=[]), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)