import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
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

# Enable CORS for API endpoints
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

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
    region = request.form.get('region', '')

    if not name or not email:
        flash("Name and email are required", "error")
        return redirect(url_for('invitations'))

    try:
        from inviter.invitation_manager import InvitationManager
        
        manager = InvitationManager()
        
        contact = {
            'name': name,
            'email': email,
            'entity': entity,
            'region': region
        }
        
        success, message, invite_link = manager.send_single_invitation(contact)
        
        if success:
            # Store in main database for dashboard display
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO invitations 
                    (name, email, entity, region, invite_link, status, sent_at) 
                    VALUES (?, ?, ?, ?, ?, 'sent', CURRENT_TIMESTAMP)
                ''', (name, email, entity, region, invite_link))
                conn.commit()
            finally:
                conn.close()
            
            flash(f"✅ {message}", "success")
        else:
            # Store error in main database
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO invitations 
                    (name, email, entity, region, status, error_message) 
                    VALUES (?, ?, ?, ?, 'error', ?)
                ''', (name, email, entity, region, message))
                conn.commit()
            finally:
                conn.close()
            
            flash(f"❌ {message}", "error")

    except Exception as e:
        flash(f"❌ Error creating invitation: {str(e)}", "error")

    return redirect(url_for('invitations'))

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    """Upload CSV file for bulk invitations"""
    if 'csv_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('invitations'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('invitations'))
    
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('invitations'))
    
    try:
        from inviter.csv_processor import CSVProcessor
        from inviter.invitation_manager import InvitationManager
        
        # Process CSV file
        processor = CSVProcessor()
        contacts = processor.process_csv_upload(file)
        
        if not contacts:
            flash('No valid contacts found in CSV file', 'warning')
            return redirect(url_for('invitations'))
        
        # Start bulk invitation process
        manager = InvitationManager()
        result = manager.send_bulk_invitations(contacts, file.filename)
        
        if result['success']:
            stats = result['stats']
            flash(f"✅ Bulk invitation started! Processing {stats['total']} contacts. "
                  f"Check the activity log for progress.", "success")
        else:
            flash(f"❌ Failed to start bulk invitations: {result.get('message', 'Unknown error')}", "error")
    
    except Exception as e:
        flash(f"❌ Error processing CSV: {str(e)}", "error")
    
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

@app.route('/news')
def news():
    """Enterprise news page showing approved RSS content"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get approved RSS items for display
        cursor.execute("""
            SELECT id, title, summary, link, category, date, approved, ai_suggestion, feed_source
            FROM rss_items 
            WHERE approved = 1
            ORDER BY date DESC, id DESC
            LIMIT 50
        """)
        items = cursor.fetchall()

        # Convert to list of dicts
        approved_items = []
        categories = {}
        
        for item in items:
            item_dict = {
                'id': item[0],
                'title': item[1],
                'summary': item[2],
                'link': item[3],
                'category': item[4] or 'General',
                'date': item[5],
                'approved': item[6],
                'ai_suggestion': item[7],
                'feed_source': item[8]
            }
            approved_items.append(item_dict)
            
            # Count categories for stats
            category_key = item[4].lower() if item[4] else 'general'
            if 'vulnerability' in category_key:
                categories['vulnerability'] = categories.get('vulnerability', 0) + 1
            elif 'threat' in category_key:
                categories['threat'] = categories.get('threat', 0) + 1
            elif 'trend' in category_key:
                categories['trend'] = categories.get('trend', 0) + 1
            elif 'tool' in category_key:
                categories['tool'] = categories.get('tool', 0) + 1

        conn.close()
        
        return render_template('news.html', 
                             approved_items=approved_items, 
                             categories=categories)
    except Exception as e:
        logging.error(f"Error in news page: {e}")
        flash(f"Error loading news: {str(e)}", 'danger')
        return render_template('news.html', approved_items=[], categories={})

@app.route('/subscribe_newsletter', methods=['POST'])
def subscribe_newsletter():
    """Handle newsletter subscription"""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    entity = request.form.get('entity', '').strip()

    if not name or not email:
        return jsonify({'success': False, 'message': 'Name and email are required'})

    try:
        from inviter.invitation_manager import InvitationManager
        
        manager = InvitationManager()
        
        contact = {
            'name': name,
            'email': email,
            'entity': entity or 'Newsletter Subscriber',
            'region': 'Web Subscription'
        }
        
        success, message, invite_link = manager.send_single_invitation(contact)
        
        if success:
            # Store in main database for dashboard display
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO invitations 
                    (name, email, entity, region, invite_link, status, sent_at) 
                    VALUES (?, ?, ?, ?, ?, 'sent', CURRENT_TIMESTAMP)
                ''', (name, email, entity, 'Newsletter', invite_link))
                conn.commit()
            finally:
                conn.close()
            
            return jsonify({
                'success': True, 
                'message': 'Successfully subscribed to GEM Security newsletter!'
            })
        else:
            return jsonify({'success': False, 'message': message})

    except Exception as e:
        logging.error(f"Error in newsletter subscription: {e}")
        return jsonify({
            'success': False, 
            'message': f'Subscription failed: {str(e)}'
        })

@app.route('/refresh_news')
def refresh_news():
    """Refresh news feed (similar to refresh_feeds but returns JSON)"""
    try:
        new_items = parse_feeds()
        return jsonify({
            'success': True, 
            'message': f'Found {new_items} new items',
            'new_items': new_items
        })
    except Exception as e:
        logging.error(f"Error refreshing news: {e}")
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500

@app.route('/api/news')
def api_news():
    """API endpoint for loading more news items"""
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 6))
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get approved RSS items with pagination
        cursor.execute("""
            SELECT id, title, summary, link, category, date, ai_suggestion, feed_source
            FROM rss_items 
            WHERE approved = 1
            ORDER BY date DESC, id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        items = cursor.fetchall()
        conn.close()

        # Convert to list of dicts
        items_list = []
        for item in items:
            items_list.append({
                'id': item[0],
                'title': item[1],
                'summary': item[2],
                'link': item[3],
                'category': item[4] or 'General',
                'date': item[5],
                'ai_suggestion': item[6],
                'feed_source': item[7]
            })

        return jsonify({'items': items_list})
    except Exception as e:
        logging.error(f"Error in API news: {e}")
        return jsonify({'error': str(e)}), 500

# API Endpoints for Enterprise Website Integration
@app.route('/api/newsletter/latest')
def api_newsletter_latest():
    """API endpoint for latest newsletter content"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get latest approved items for newsletter
        cursor.execute("""
            SELECT id, title, summary, link, category, date, ai_suggestion, feed_source
            FROM rss_items 
            WHERE approved = 1
            ORDER BY date DESC, id DESC
            LIMIT 20
        """)
        items = cursor.fetchall()
        conn.close()

        # Format for API response
        newsletter_items = []
        for item in items:
            newsletter_items.append({
                'id': item[0],
                'title': item[1],
                'summary': item[2] or '',
                'link': item[3],
                'category': item[4] or 'General',
                'date': item[5],
                'ai_suggestion': item[6] or '',
                'feed_source': item[7] or '',
                'content': item[6] if item[6] else item[2]  # Use AI suggestion or fallback to summary
            })

        return jsonify({
            'success': True,
            'items': newsletter_items,
            'total': len(newsletter_items),
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error in newsletter API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/newsletter/categories')
def api_newsletter_categories():
    """API endpoint for newsletter content by categories"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get categorized content
        cursor.execute("""
            SELECT category, COUNT(*) as count,
                   GROUP_CONCAT(title, '|||') as titles,
                   GROUP_CONCAT(link, '|||') as links,
                   GROUP_CONCAT(COALESCE(ai_suggestion, summary), '|||') as content
            FROM rss_items 
            WHERE approved = 1 AND date >= date('now', '-7 days')
            GROUP BY category
            ORDER BY count DESC
        """)
        categories = cursor.fetchall()
        conn.close()

        # Format categorized data
        categorized_content = {}
        for cat in categories:
            category_name = cat[0] or 'General'
            titles = cat[2].split('|||') if cat[2] else []
            links = cat[3].split('|||') if cat[3] else []
            content = cat[4].split('|||') if cat[4] else []
            
            categorized_content[category_name] = {
                'count': cat[1],
                'items': [
                    {
                        'title': titles[i] if i < len(titles) else '',
                        'link': links[i] if i < len(links) else '',
                        'content': content[i] if i < len(content) else ''
                    }
                    for i in range(min(len(titles), len(links), len(content)))
                ]
            }

        return jsonify({
            'success': True,
            'categories': categorized_content,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error in categories API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/newsletter/subscribe', methods=['POST'])
def api_newsletter_subscribe():
    """API endpoint for newsletter subscription from enterprise website"""
    try:
        data = request.get_json()
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        entity = data.get('entity', 'Enterprise Website').strip()
        source = data.get('source', 'Main Website')

        if not name or not email:
            return jsonify({
                'success': False,
                'message': 'Name and email are required'
            }), 400

        from inviter.invitation_manager import InvitationManager
        
        manager = InvitationManager()
        
        contact = {
            'name': name,
            'email': email,
            'entity': entity,
            'region': f'{source} - Auto Subscription'
        }
        
        success, message, invite_link = manager.send_single_invitation(contact)
        
        if success:
            # Store in main database for dashboard display
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO invitations 
                    (name, email, entity, region, invite_link, status, sent_at) 
                    VALUES (?, ?, ?, ?, ?, 'sent', CURRENT_TIMESTAMP)
                ''', (name, email, entity, source, invite_link))
                conn.commit()
            finally:
                conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Successfully subscribed to GEM Security newsletter!',
                'invite_link': invite_link
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500

    except Exception as e:
        logging.error(f"Error in API newsletter subscription: {e}")
        return jsonify({
            'success': False,
            'message': f'Subscription failed: {str(e)}'
        }), 500

@app.route('/api/newsletter/stats')
def api_newsletter_stats():
    """API endpoint for newsletter statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get content stats
        cursor.execute("SELECT COUNT(*) FROM rss_items WHERE approved = 1")
        total_articles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rss_items WHERE approved = 1 AND date >= date('now', '-7 days')")
        weekly_articles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM invitations WHERE status = 'sent'")
        total_subscribers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rss_feeds WHERE active = 1")
        active_sources = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_articles': total_articles,
                'weekly_articles': weekly_articles,
                'total_subscribers': total_subscribers,
                'active_sources': active_sources,
                'last_updated': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logging.error(f"Error in stats API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('dashboard.html', items=[]), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {error}")
    return render_template('dashboard.html', items=[]), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)