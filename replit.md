# Instagram LeadGen - Full-Stack Application

## Overview

This is a Flask-based Instagram lead generation and outreach automation tool that crawls Instagram hashtags, enriches profile data, and generates personalized email outreach campaigns. The application uses a minimalist design inspired by Kasimir Lieselotte's aesthetic, featuring elegant serif typography with Cormorant Garamond font.

## Recent Changes

### 2025-07-09: Fixed Critical Memory Issues and Frontend Errors (COMPLETED)
- **Issue**: Application experiencing SIGKILL errors due to memory exhaustion and frontend showing "unexpected error"
- **Resolution**: Implemented extremely aggressive memory optimization and fixed frontend/backend sync issues
- **Changes Made**:
  - **Aggressive Batch Processing**: Reduced batch size from 20 to 10 items with forced garbage collection
  - **Item Limits**: Reduced maximum item limit from 1000 to 300 to prevent memory overflow
  - **Essential Data Only**: Strip unnecessary fields from Apify responses, keep only required data
  - **Database Optimization**: Reduced batch commit size from 20 to 10 with proper session cleanup
  - **Concurrent Processing**: Further reduced from 3 to 2 simultaneous operations for profile enrichment
  - **Sequential Processing**: Changed from parallel to sequential batch processing to minimize memory usage
  - **Search Limits**: Reduced maximum search limit from 100 to 50 for memory safety
  - **Username Limits**: Added hard limit of 50 usernames processed per request
  - **Frequent GC**: Added forced garbage collection after each batch and processing delay (0.3s)
  - **Processing Delay**: Increased delays between operations to reduce memory pressure
  - **Frontend Fixes**: 
    - Updated search limit validation from 100 to 50
    - Fixed timeout alignment (190s frontend vs 180s backend)
    - Improved error handling to ignore browser extension rejections
    - Added detailed error logging for debugging
  - **Frontend Update**: Updated UI to reflect new search limits (max 50, default 25)
- **Status**: Memory usage heavily optimized, SIGKILL errors resolved, frontend/backend errors fixed, Apify processing working successfully

### 2025-07-09: Integrated PostgreSQL Database
- **Issue**: Application was using in-memory storage which lost data on restart
- **Resolution**: Added PostgreSQL database integration using Flask-SQLAlchemy
- **Changes Made**:
  - Created `models.py` with Lead and ProcessingSession database models
  - Updated main.py to use SQLAlchemy database operations
  - Replaced in-memory `app_data['leads']` storage with database persistence
  - Added proper error handling and transaction management
  - Updated all CRUD operations to work with database models
  - Maintained existing API compatibility with to_dict() serialization
- **Status**: Database successfully integrated, data now persists between sessions

### 2025-07-09: Fixed Frontend Error Handling and Server Stability
- **Issue**: Frontend showing "unexpected error occurred" and server crashes during processing
- **Resolution**: Improved error handling, logging, and stability
- **Changes Made**:
  - Added comprehensive error handling for missing Instagram session ID
  - Implemented request timeout protection (5 minutes) on frontend
  - Added automatic session modal display for missing credentials
  - Enhanced logging throughout the processing pipeline
  - Added fallback handling for empty results
  - Improved exception handling to prevent server crashes
- **Status**: Application now properly handles errors and provides clear user feedback

### 2025-07-09: Fixed Apify API Integration
- **Issue**: API calls were timing out due to incorrect input format and direct HTTP calls
- **Resolution**: Updated to use official Apify client library with correct API formats
- **Changes Made**:
  - Hashtag search now uses: `{"search": keyword, "searchType": "hashtag", "searchLimit": 100}`
  - Profile enrichment uses: `{"instagram_ids": [urls], "SessionID": sessionid, "proxy": {...}}`
  - Replaced direct HTTP calls with `ApifyClient` library for better reliability
  - Fixed data processing to handle multiple profile results correctly
- **Status**: Backend API integration confirmed working, processes results successfully

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Bootstrap 5 with custom CSS styling
- **JavaScript**: Vanilla JavaScript for client-side interactions
- **Design Philosophy**: Minimalist design with elegant serif typography (Cormorant Garamond)
- **Responsive Design**: Mobile-friendly interface using Bootstrap's grid system
- **UI Components**: Modal dialogs, dynamic tables with sorting, toast notifications

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: PostgreSQL with Flask-SQLAlchemy ORM
- **Models**: Lead and ProcessingSession tables for persistent data storage
- **Concurrency**: asyncio and httpx for asynchronous operations
- **Session Management**: Flask sessions for storing user state
- **Data Storage**: PostgreSQL database with proper transaction management
- **Logging**: Python logging module for debugging and monitoring

### API Integration Pattern
- **Concurrent Processing**: ThreadPoolExecutor for parallel API calls
- **Rate Limiting**: Built-in concurrency limits (≤10 for profiles, ≤5 for Perplexity)
- **Error Handling**: Graceful fallback mechanisms for failed API calls

## Key Components

### Data Processing Pipeline
1. **Hashtag Crawling**: Uses Apify actor DrF9mzPPEuVizVF4l for Instagram hashtag analysis
2. **Profile Enrichment**: Concurrent profile data collection using Apify actor 8WEn9FvZnhE7lM3oA
3. **Contact Discovery**: Perplexity AI fallback for missing contact information
4. **Deduplication**: Removes duplicate profiles using hashtag|username composite keys
5. **Email Generation**: OpenAI GPT-4o integration for personalized outreach content

### Authentication & Session Management
- **Instagram Session**: Requires IG_SESSIONID for accessing Instagram data
- **Google OAuth**: Gmail API integration for email sending
- **Session Storage**: Flask sessions for maintaining user state across requests

### Data Export Capabilities
- **Formats**: CSV and JSON export functionality
- **Google Sheets**: Integration for direct export to Google Sheets
- **Excel**: Excel file generation for offline analysis

## Data Flow

1. **Session Initialization**: User provides Instagram Session ID via modal dialog
2. **Keyword Input**: User enters hashtag/keyword for analysis
3. **Data Collection**: 
   - Apify crawls Instagram hashtags
   - Concurrent profile enrichment
   - Perplexity fallback for missing contact info
4. **Data Processing**:
   - Deduplication based on hashtag|username pairs
   - Profile enrichment and contact discovery
   - Results stored in app_data global storage
5. **UI Display**: Results rendered in sortable HTML table with duplicate highlighting
6. **Email Generation**: AI-powered personalized email content creation
7. **Email Sending**: Direct Gmail API integration for outreach campaigns

## External Dependencies

### Core APIs
- **Apify**: Instagram hashtag crawling and profile data collection
- **Perplexity AI**: Contact information discovery fallback
- **OpenAI GPT-4o**: Personalized email content generation
- **Gmail API**: Email sending functionality

### Python Packages
- **Flask**: Web framework
- **httpx[async]**: Asynchronous HTTP client
- **asyncio**: Asynchronous programming support
- **google-auth**: Google API authentication
- **google-api-python-client**: Gmail API client
- **openai**: OpenAI API client
- **python-dotenv**: Environment variable management

### Frontend Dependencies
- **Bootstrap 5**: UI framework and responsive design
- **Font Awesome**: Icon library
- **Google Fonts**: Cormorant Garamond typography

## Deployment Strategy

### Environment Configuration
- **API Keys**: Stored in environment variables (.env file)
- **Session Secret**: Configurable via SESSION_SECRET environment variable
- **Development Mode**: Local development using `python main.py`

### Production Considerations
- **Database**: PostgreSQL with proper connection pooling and transaction management
- **Session Management**: Flask sessions suitable for single-instance deployment
- **Scaling**: Concurrent processing limited to prevent API rate limiting
- **Security**: Session secrets and API keys must be properly secured
- **Data Persistence**: All lead data now persists between application restarts

### Key Environment Variables
- `IG_SESSIONID`: Instagram session ID for API access
- `OPENAI_API_KEY`: OpenAI API key for GPT-4o integration
- `SESSION_SECRET`: Flask session encryption key
- Additional API keys for Apify, Perplexity, and Google services

### Testing
- **Unit Tests**: Basic deduplication functionality tests included
- **Test Framework**: pytest for test execution
- **Code Quality**: Black, isort, and flake8 for code formatting and linting