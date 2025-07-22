# K+L Influence - Instagram Lead Generation Platform

## Project Overview
A sophisticated Instagram lead generation platform that leverages advanced web scraping, AI-powered data enrichment, and intelligent marketing list creation with enhanced user experience.

**Current Status**: Enhanced with Emergency STOP functionality

## Recent Changes (July 22, 2025)
✓ **Emergency STOP System - Process Termination Implementation**: True immediate cessation
  - **REMOVED**: Regular stop functionality completely eliminated
  - **SIGNAL-BASED TERMINATION**: Emergency stop now kills worker process like Ctrl+C
  - Process termination using SIGTERM signal for immediate cessation
  - No dependency on API call completion or flag checking
  - Gunicorn automatically restarts worker after termination
  - Frontend shows process termination feedback and auto-reloads page
  - Fallback mechanism: touches main.py to force worker restart if signal fails
  - All running operations (Apify calls, ThreadPools, etc.) terminated immediately
  - Comprehensive logging with CRITICAL level for emergency stop events

## Project Architecture

### Technology Stack
- **Backend**: Flask web framework with SQLAlchemy
- **Database**: PostgreSQL with comprehensive lead tracking
- **APIs**: Apify Instagram scraping, OpenAI GPT-4o, Perplexity for enrichment
- **Frontend**: Bootstrap 5, responsive design with advanced UI controls
- **Processing**: Asynchronous Python with ThreadPoolExecutor

### Key Features
1. **Instagram Data Scraping**: Hashtag-based profile discovery
2. **AI-Powered Enrichment**: Contact information discovery via Perplexity API
3. **Email Generation**: Personalized outreach emails using OpenAI
4. **Product Integration**: Product-based campaign customization
5. **Emergency Controls**: Multi-level stop mechanisms for process control

### Processing Flow
1. Hashtag discovery phase with user selection
2. Profile enrichment in batches with anti-spam delays
3. AI-powered contact information discovery
4. Personalized email generation with product integration

### Emergency Stop System
- **ONLY Emergency Stop**: Immediate forceful termination via `/emergency-stop-processing`
- **No Regular Stop**: Regular stop functionality completely removed per user request
- **Forceful Termination**: Multiple rapid stop requests ensure immediate process killing
- **UI Controls**: Single prominent emergency button with pulsing animation
- **Multi-Level Checks**: Emergency stop verified in all processing loops and API calls
- **State Management**: Complete UI and backend state reset capabilities

## User Preferences
- Language: German (DE) for UI elements
- Processing: Batch-based with progress tracking
- Safety: Anti-spam delays and memory-conscious limits
- UX: Immediate feedback and comprehensive error handling

## Development Guidelines
- Flask best practices with proper error handling
- Async processing for long-running tasks
- PostgreSQL for data persistence
- Bootstrap 5 responsive design patterns
- German language UI with professional styling

## Security & Performance
- Session-based authentication
- Instagram session ID management
- Rate limiting and anti-spam measures
- Memory-conscious batch processing (max 50 profiles)
- Comprehensive logging for debugging

---
*Last Updated: July 22, 2025 - Emergency STOP system implementation*