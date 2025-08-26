# Overview

This is an RSS curation system that automates content aggregation and distribution. The application fetches RSS feeds, uses AI to generate optimized summaries, and distributes approved content to Telegram channels. It provides a web dashboard for content review and feed management, enabling users to curate and share relevant content efficiently.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Components**: Bootstrap 5 with dark theme and Feather icons
- **Architecture Pattern**: Server-side rendered templates with minimal JavaScript
- **Styling**: Custom CSS with Bootstrap overrides for enhanced user experience

## Backend Architecture
- **Web Framework**: Flask with modular component structure
- **Database Layer**: SQLite with custom connection management and schema definitions
- **RSS Processing**: Feedparser library for RSS/Atom feed parsing
- **AI Integration**: OpenAI GPT-5 for content summarization and optimization
- **Messaging**: Telegram Bot API for content distribution

## Data Storage
- **Primary Database**: SQLite with two main tables:
  - `rss_feeds`: Stores RSS feed sources and metadata
  - `rss_items`: Stores parsed content items with approval status
- **Schema Features**: Indexed queries for performance, unique constraints for deduplication
- **Data Management**: Automatic cleanup mechanisms for old content

## Authentication and Authorization
- **Session Management**: Flask sessions with configurable secret keys
- **Security**: Environment-based configuration for sensitive data
- **Access Control**: Basic session-based authentication (no user management implemented)

## Content Processing Pipeline
- **Feed Aggregation**: Scheduled RSS feed parsing and content extraction
- **AI Enhancement**: Automated summary generation optimized for Telegram format (280 character limit)
- **Manual Curation**: Web dashboard for content approval and review
- **Distribution**: Automatic posting to Telegram channels upon approval

## API Design
- **RESTful Endpoints**: Standard HTTP methods for CRUD operations
- **Form-based Actions**: POST endpoints for feed management and content actions
- **AJAX Support**: Asynchronous AI suggestion generation
- **Error Handling**: Comprehensive logging and user feedback mechanisms

# External Dependencies

## Core Dependencies
- **Flask**: Web framework for application structure
- **feedparser**: RSS/Atom feed parsing and content extraction
- **requests**: HTTP client for external API communication
- **python-dotenv**: Environment variable management

## AI Services
- **OpenAI API**: GPT-5 model integration for content summarization
- **Configuration**: API key-based authentication with graceful degradation

## Messaging Platform
- **Telegram Bot API**: Content distribution and channel management
- **Authentication**: Bot token and chat ID configuration
- **Features**: Markdown formatting, link previews, message scheduling

## Database
- **SQLite**: Embedded database for development and small-scale deployment
- **Migration Support**: Schema versioning through models.py
- **Performance**: Indexed queries and connection pooling

## Frontend Assets
- **Bootstrap 5**: UI framework with dark theme support
- **Feather Icons**: Lightweight icon system
- **Custom CSS**: Enhanced styling and responsive design
- **JavaScript**: Minimal client-side functionality for form handling and AJAX

## Development Tools
- **Logging**: Python logging module with configurable levels
- **Error Handling**: Comprehensive exception management
- **Environment Configuration**: Flexible deployment settings