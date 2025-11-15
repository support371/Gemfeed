import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import init_db, get_db_connection
from rss_parser import parse_feeds, get_rss_feeds, add_rss_feed, remove_rss_feed
from ai_summary import generate_summary
from telegram_bot import send_to_telegram

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
    return render_template('feed.html', feeds=feeds)

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

@app.errorhandler(404)
def not_found_error(error):
    return render_template('dashboard.html', items=[]), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {error}")
    return render_template('dashboard.html', items=[]), 500

