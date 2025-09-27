
# Enterprise Website Newsletter Integration

This guide explains how to integrate the GEM Security RSS curation system with your enterprise website's newsletter page.

## API Endpoints Available

### 1. Latest Newsletter Content
```
GET /api/newsletter/latest
```
Returns the latest 20 approved security articles for newsletter display.

**Response:**
```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "title": "Critical Security Vulnerability Discovered",
      "summary": "Original article summary",
      "link": "https://example.com/article",
      "category": "Vulnerability",
      "date": "2024-01-01",
      "ai_suggestion": "AI-enhanced summary",
      "feed_source": "Security Blog",
      "content": "AI-enhanced or original summary"
    }
  ],
  "total": 20,
  "generated_at": "2024-01-01T12:00:00"
}
```

### 2. Newsletter Subscription
```
POST /api/newsletter/subscribe
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@company.com",
  "entity": "Company Name",
  "source": "Main Website"
}
```

### 3. Newsletter Categories
```
GET /api/newsletter/categories
```
Returns content organized by security categories.

### 4. Newsletter Statistics
```
GET /api/newsletter/stats
```
Returns subscription and content statistics.

## Integration Examples

### JavaScript Integration
```javascript
// Fetch latest newsletter content
async function loadNewsletterContent() {
    try {
        const response = await fetch('https://your-repl-url.replit.dev/api/newsletter/latest');
        const data = await response.json();
        
        if (data.success) {
            displayNewsletterItems(data.items);
        }
    } catch (error) {
        console.error('Failed to load newsletter content:', error);
    }
}

// Subscribe to newsletter
async function subscribeToNewsletter(formData) {
    try {
        const response = await fetch('https://your-repl-url.replit.dev/api/newsletter/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Subscription failed:', error);
        return { success: false, message: 'Network error' };
    }
}
```

### PHP Integration
```php
// Fetch newsletter content
function getNewsletterContent() {
    $url = 'https://your-repl-url.replit.dev/api/newsletter/latest';
    $response = file_get_contents($url);
    return json_decode($response, true);
}

// Subscribe user
function subscribeToNewsletter($name, $email, $entity) {
    $url = 'https://your-repl-url.replit.dev/api/newsletter/subscribe';
    $data = json_encode([
        'name' => $name,
        'email' => $email,
        'entity' => $entity,
        'source' => 'Enterprise Website'
    ]);
    
    $options = [
        'http' => [
            'header' => "Content-type: application/json\r\n",
            'method' => 'POST',
            'content' => $data
        ]
    ];
    
    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    return json_decode($result, true);
}
```

## CORS Configuration

If you need cross-origin requests, add this to your enterprise website's server configuration or contact support to enable CORS headers.

## Auto-Refresh Setup

Set up automatic content refresh on your enterprise website:

```javascript
// Auto-refresh newsletter content every 30 minutes
setInterval(loadNewsletterContent, 30 * 60 * 1000);

// Load content on page load
document.addEventListener('DOMContentLoaded', loadNewsletterContent);
```

## Security Notes

1. The API endpoints are public but rate-limited
2. Newsletter subscriptions automatically send Telegram invites
3. All subscriber data is stored securely
4. Content is pre-approved by security analysts

## Support

For technical support or custom integration needs, contact the GEM Security team.
