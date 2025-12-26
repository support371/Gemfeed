# Overview

This is an RSS curation system that automates content aggregation and distribution. The application fetches RSS feeds, uses Google Gemini AI to generate optimized summaries, and distributes approved content to Telegram channels. It provides a web dashboard for content review, a modern newsletter feed, and a social distribution manager for multi-platform broadcasting.

# System Architecture

## Content Processing Pipeline
- **Feed Aggregation**: Scheduled RSS feed parsing and content extraction.
- **AI Enhancement**: Automated summary generation using Google Gemini AI, optimized for Telegram and social platforms.
- **Manual Curation**: Web dashboard for content approval and review with quality ratings.
- **Distribution**: 
  - Automatic posting to Telegram channels upon approval.
  - Multi-platform social distribution via Ayrshare (X, Facebook, Nextdoor, Instagram, TikTok).
  - Media Generation for vertical video and branded images.

# External Dependencies

## AI Services
- **Google Gemini AI**: Replaced OpenAI for content summarization and optimization.

## Distribution
- **Ayrshare API**: Multi-platform social media posting engine.
- **Telegram Bot API**: Content distribution to cybersecurity channels.
- **SendGrid**: Email invitation delivery system.
