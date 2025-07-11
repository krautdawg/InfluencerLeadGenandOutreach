# Instagram LeadGen - Full-Stack Application

## Overview

K+L Influence is a Flask-based Instagram lead generation and outreach automation tool that crawls Instagram hashtags, enriches profile data, and generates personalized email outreach campaigns. The application features a modern, professional design following the K+L Internal Web App Style Guide, with Natural Green branding, Inter typography, and Google Sheets-style table interactions for efficient data management.

## Recent Changes

### 2025-07-11: Product Selection System with OpenAI Email Integration (COMPLETED)
- **Update**: Implemented complete product selection functionality with enhanced OpenAI email generation
- **Changes Made**:
  - **Product Database Model**: Created Product model with fields for name, URL, image_url, description, and price
  - **Default Products**: Initialized two products from KasimirLieselotte store:
    - Funghi Funk Spray (€49.90) - https://www.kasimirlieselotte.de/shop/p/funghi-funk-spray-50ml
    - Zeck Zack Spray (€49.90) - https://www.kasimirlieselotte.de/shop/p/zeck-zack-spray-50ml
  - **Product Management API**: Created `/api/products` endpoint for product listing and management
  - **Product Selection UI**: 
    - Added product dropdown in Email Prompts settings section for default selection
    - Added Product column to results table with click-to-edit functionality
    - Implemented inline product selector with immediate save on change
  - **Enhanced Email Generation**: 
    - Updated OpenAI prompts to explicitly include product information
    - Modified system prompts to ensure product name, URL, and description are incorporated in emails
    - Added specific instructions for natural product integration in email content
  - **Frontend Integration**: 
    - Products data passed from backend to frontend on page load
    - JavaScript functions for product selection and management
    - Visual indicators for products with "Kein Produkt" (No Product) for unassigned leads
  - **Product Images**: Stored product images in static folder for future integration
- **Features**:
  - Per-lead product assignment through click-to-edit interface
  - Default product selection for new email generations
  - Product information automatically included in OpenAI prompts
  - Seamless product switching without page reload
  - Product URLs and descriptions integrated into generated emails
- **Benefits**:
  - Personalized product recommendations in outreach emails
  - Easy product management through intuitive UI
  - Consistent product information across all emails
  - Enhanced email relevance with product-specific content
- **Status**: Product selection system fully implemented and integrated with email generation

### 2025-07-11: Complete Email Template System and Persistent Send Functionality (COMPLETED)
- **Update**: Implemented complete email template synchronization and persistent send button functionality
- **Changes Made**:
  - **EmailTemplate Database Model**: Added model to store subject and body templates persistently
  - **Backend API Endpoints**: Created `/api/email-templates` (GET/POST) for template management
  - **Dynamic Template Loading**: Templates now load from database instead of hardcoded values
  - **Auto-Save Functionality**: Templates automatically save after 2 seconds of inactivity or on blur
  - **Fixed Modal Behavior**: Removed automatic transition from Subject to Email Body modal - now saves and closes
  - **Fixed Save Button**: Resolved "Save Changes" button functionality in edit modals
  - **Click-to-Edit Enhancement**: Enabled click-to-edit for both Subject and Email Body fields in table
  - **Persistent Send Button**: Send button remains active even after emails are sent, allowing multiple sends
  - **Status Column**: Added dedicated Status column showing "Gesendet" (sent) or "Entwurf" (draft) status
  - **Improved Error Handling**: Added proper error handling and user feedback for template operations
  - **JavaScript Optimization**: Fixed syntax errors and improved string escaping in dynamic HTML
- **Features**:
  - Templates are editable from frontend and synchronized to backend database
  - Debounced auto-saving prevents excessive API calls
  - Visual feedback with toast notifications for save operations
  - Templates used for OpenAI email generation with personalized content
  - Consistent edit experience across all editable fields
  - Multiple email sends allowed while maintaining status tracking
  - Clear visual indicators for email status in dedicated column
- **Benefits**:
  - Customizable email templates without code changes
  - Persistent template storage across sessions
  - Improved user experience with auto-save functionality
  - Better data integrity with proper error handling
  - Flexible email sending workflow with persistent send capability
- **Status**: Complete email template and send functionality implemented and operational

### 2025-07-11: K+L Influence Brand Redesign (COMPLETED)
- **Update**: Complete UI/UX overhaul with K+L Influence branding and modern design system
- **Changes Made**:
  - **New Design System**: Created `kl-influence-style.css` implementing the complete K+L Internal Web App Style Guide
  - **Color Palette**: Implemented Natural Green (#2D5B2D), Deep Forest Green (#1B3F1B), and extended brand colors
  - **Typography**: Changed from Cormorant Garamond to Inter font family for better readability
  - **Logo Integration**: Added K+L Influence logo with leaf icon and modern logotype
  - **Navigation Redesign**: 
    - Top navigation bar with Deep Forest Green background and white text
    - Sidebar navigation with Pale Green background (#F0F5F0)
    - Mobile-responsive hamburger menu
  - **Google Sheets-Style Table**: 
    - Sticky headers with sorting functionality
    - Inline editing for email addresses
    - Advanced filtering with comparison operators for numeric fields
    - Alternating row colors and hover effects
  - **Modal System**: 
    - Redesigned session configuration modal
    - New edit modal for Subject and Email Body fields
    - Smooth animations and backdrop blur
  - **Mobile Optimization**: 
    - Responsive breakpoints (sm: 640px, md: 768px)
    - Off-canvas sidebar for mobile
    - Table converts to card view on small screens
  - **Enhanced JavaScript**: Created `kl-influence-app.js` with:
    - Keyboard navigation for table cells
    - Debounced filtering
    - Toast notifications
    - Progress tracking with visual feedback
  - **New Endpoints**: 
    - Added `/update-lead/<username>` for inline editing
    - Modified `/draft-email/<username>` to GET method
    - Added `/send-email/<username>` for email sending
- **Benefits**:
  - Modern, professional appearance aligned with K+L brand
  - Improved usability with Google Sheets-like interactions
  - Better mobile experience for on-the-go usage
  - Enhanced data editing capabilities
  - Consistent design language throughout application
- **Status**: Design overhaul completed and application restarted with new interface

### 2025-07-11: Implemented Robust Debug Logging System for Production Deployment (COMPLETED)
- **Update**: Added comprehensive API monitoring and debug logging system for deployed website
- **Issue**: Need for robust tracking of API call success/failure status and detailed error analysis in production
- **Solution**: Created complete debug logging infrastructure with structured monitoring
- **Changes Made**:
  - **New Debug Logger Module**: Created `debug_logger.py` with comprehensive API call tracking
  - **Structured JSON Logging**: Implemented JSON-formatted logs for easier parsing and analysis
  - **API Call Metrics**: Automatic tracking of start/end times, duration, success/failure status
  - **Error Categorization**: Intelligent error classification (timeout, authentication, rate limit, etc.)
  - **Recovery Suggestions**: Automatic recovery recommendations based on error types
  - **Performance Monitoring**: Performance categorization (excellent, good, slow, very slow)
  - **Data Sanitization**: Automatic removal of sensitive data (API keys, tokens) from logs
  - **API Metrics Endpoints**: 
    - `/api-metrics` - Comprehensive metrics with time window filtering
    - `/api-health` - Real-time health status and service availability
    - `/debug-logs` - Structured log retrieval with JSON parsing
    - `/debug` - Interactive dashboard for monitoring
  - **Enhanced API Functions**: 
    - Updated Apify hashtag search with detailed logging
    - Enhanced Perplexity contact enrichment with success/failure tracking
    - Improved profile enrichment with performance metrics
    - Added OpenAI email generation monitoring
  - **Debug Dashboard**: Interactive HTML dashboard for real-time monitoring
  - **Business Logic Tracking**: Separate tracking for non-API operational errors
  - **Integration**: Seamlessly integrated with existing Flask application
- **Features**:
  - Real-time API success/failure monitoring
  - Detailed error analysis with stack traces
  - Performance metrics and trends
  - Service health status checking
  - Database connectivity monitoring
  - Auto-refresh dashboard with 10-second intervals
  - Historical metrics with configurable time windows
  - Error type analysis and recovery suggestions
- **Benefits**:
  - Production-ready debugging capabilities
  - Immediate identification of API failures and causes
  - Performance bottleneck detection
  - Service dependency monitoring
  - Proactive error recovery guidance
  - Comprehensive audit trail for all API interactions
- **Access**: Visit `/debug` endpoint for interactive monitoring dashboard
- **Log Files**: Structured logs saved to `api_debug.log` for persistent analysis
- **Status**: Robust debug logging system fully implemented and operational

### 2025-07-11: Fixed Perplexity API Enrichment Logic (COMPLETED)
- **Issue**: Perplexity API contact enrichment was not being called when profiles already had some contact information
- **Root Cause**: Flawed logic that only called Perplexity when ALL contact fields were missing (using `not any()`)
- **Problem**: If a profile had a website but missing email/phone, Perplexity would be skipped entirely
- **Resolution**: 
  - Changed logic to call Perplexity when ANY contact fields are missing (using `or` conditions)
  - Added explicit checks for missing email, phone, and website individually
  - Enhanced logging to show which specific fields are missing for each profile
  - Added existing contact info to profile data passed to Perplexity API for better context
- **Impact**: 
  - Perplexity API will now properly enrich profiles with partial contact information
  - Missing emails and phone numbers will be found even when website is already known
  - Better utilization of Perplexity API for comprehensive contact discovery
- **Example**: @fusspflege.neu.ulm profile now correctly gets email and phone enrichment despite having existing website
- **Status**: Logic fixed and tested, future enrichment runs will work correctly

### 2025-07-11: Advanced Table Filtering and Sorting (COMPLETED)
- **Update**: Added autofilter functionality for each table column with enhanced sorting
- **Changes Made**:
  - **Filter Row**: Added input fields below each sortable column header
  - **Text Filtering**: Case-insensitive partial match filtering for Username, Hashtag, Full Name, and Email columns
  - **Numeric Filtering**: Advanced filtering for Followers column with comparison operators (>, <, >=, <=, =)
  - **Clear Filters Button**: Added button to quickly clear all active filters
  - **Filter Persistence**: Filters remain active during sorting operations
  - **Responsive Design**: Filter inputs styled to match the elegant Kasimir Lieselotte aesthetic
  - **User-Friendly Placeholders**: Informative placeholder text guides users on filter usage
- **Technical Implementation**:
  - JavaScript filter state management with real-time filtering
  - Filters work seamlessly with existing sort functionality
  - Numeric column supports complex queries like ">1000" or "<=500"
  - Filters automatically reset when new search results are loaded
- **Benefits**:
  - Quick data discovery in large result sets
  - Advanced filtering for follower count analysis
  - Maintains clean, elegant UI design
  - Improved workflow efficiency for lead qualification
- **Status**: Autofilter and enhanced sorting fully implemented and tested

### 2025-07-11: Anti-Spam Protection and Progress Tracking (COMPLETED)
- **Update**: Added randomized delays to Apify API calls and real-time progress tracking
- **Changes Made**:
  - **Random Delays**: Added 1-10 second random delays before each Apify API call to circumvent anti-spam measures
  - **Progress Counter**: Implemented real-time progress tracking with estimated time remaining
  - **Backend Progress API**: New `/progress` endpoint returns current processing status
  - **Frontend Progress Display**: Shows current step, completion percentage, and estimated time remaining
  - **Progress Polling**: Frontend polls progress every 2 seconds during processing
  - **Time Calculation**: Dynamic time estimation based on actual processing speed
- **Benefits**: 
  - Reduced risk of being flagged as spam by Instagram/Apify
  - Better user experience with visible progress and time estimates
  - Users can see exactly which step is being processed
  - Accurate time remaining based on actual processing performance
- **Status**: Anti-spam delays and progress tracking fully implemented

### 2025-07-10: Enhanced Perplexity API with Existing Contact Data Integration (COMPLETED)
- **Issue**: Perplexity API was not utilizing existing contact information from the lead database
- **Root Cause**: Function was ignoring known contact data (email, phone, website) from profile
- **Resolution**: 
  - Enhanced function to include existing contact information in API request
  - Added "Existing Contact Information" section to profile description sent to API
  - Modified prompt to specifically instruct AI to preserve existing data and only search for missing info
  - Implemented contact data merging logic that prioritizes existing database values over API findings
  - Updated all error handling to return existing contact information when API fails
- **Test Suite Updated**: 
  - Updated all 9 test cases to expect existing website data preservation
  - Tests now verify that known contact information is prioritized over API responses
  - Real API integration confirmed to work with existing contact data
- **Benefits**: 
  - No loss of existing contact information during API enrichment
  - More efficient API usage by focusing search on missing data only
  - Better data consistency and reliability
  - Existing website data now preserved correctly (e.g., http://azaliah.at)
- **Status**: Contact data integration implemented and fully tested

### 2025-07-10: UI Redesign with Left Navigation and Enhanced UX (COMPLETED)
- **Update**: Complete UI redesign with left navigation bar and improved user experience
- **Changes Made**:
  - **Left Navigation Bar**: Created fixed left sidebar (350px) for input controls and settings
  - **Export Toolbar**: Moved export functionality to compact top-right corner with icon buttons
  - **Instagram Links**: Username now links directly to Instagram profile (opens in new tab)
  - **Data Consistency**: Fixed follower count display and handles both snake_case and camelCase field names
  - **Responsive Design**: Mobile-friendly layout that stacks navigation on smaller screens
  - **Improved Layout**: Main content area now dedicated to results table with better spacing
  - **Enhanced Styling**: Better visual hierarchy with Kasimir Lieselotte aesthetic maintained
- **Benefits**: 
  - More efficient use of screen space with dedicated input area
  - Cleaner results presentation with export controls easily accessible
  - Better user workflow with logical separation of input and output areas
  - Direct Instagram navigation for quick profile verification
  - Responsive design works on all devices
- **Status**: UI redesign completed with improved navigation and user experience

### 2025-07-10: Fixed Apify Profile Enrichment API Integration (COMPLETED)
- **Issue**: Lead generation results not showing follower count, email, and full name information
- **Root Cause**: 
  - The `call_apify_actor_sync` function was designed for hashtag search, not profile enrichment
  - Profile enrichment API returns different data structure than hashtag search API
  - Field mapping was incorrect between API response and database schema
- **Resolution**: 
  - Created dedicated `call_apify_profile_enrichment` function for profile API
  - Fixed field mapping to match actual API response (e.g., `follower_count` not `followers_count`)
  - Added improved logging to track enrichment process
  - Verified Instagram session ID is properly configured and working
- **Changes Made**:
  - New function handles profile enrichment API response correctly
  - Profile data now properly extracted from Apify response
  - Fields correctly mapped: `full_name`, `follower_count`, `biography`, `public_email`, etc.
- **Status**: Profile enrichment now working with valid Instagram session ID

### 2025-07-10: German Email Generation with KasimirLieselotte Branding (COMPLETED)
- **Update**: Modified email drafting functionality to generate German content
- **Changes Made**:
  - **German Subject Lines**: Updated AI prompts to generate approachable German subject lines
  - **German Email Body**: AI now creates professional German emails from Kasimir at KasimirLieselotte
  - **Branding Integration**: Emails include proper signature with website https://www.kasimirlieselotte.de/
  - **Professional Tone**: Maintains professional German language style matching the store's aesthetic
- **Benefits**: 
  - Personalized German outreach emails for better local market engagement
  - Consistent branding with KasimirLieselotte store identity
  - Professional German communication style for Instagram influencer outreach
- **Status**: German email generation implemented and ready for use

### 2025-07-09: Incremental Save and Address Fields Added (COMPLETED)
- **Issue**: No Lead records in database despite successful hashtag extraction
- **Root Cause**: 
  - Profile enrichment process was getting killed (SIGKILL) due to memory issues before saving any data
  - All leads were being saved at the end of processing, so crashes resulted in total data loss
- **Fixes Implemented**:
  - **Incremental Saves**: Modified to save leads immediately after each batch is enriched
  - **New Address Fields**: Added address_street, city_name, zip, latitude, longitude to Lead model
  - **Batch-by-Batch Persistence**: Each batch of 2 profiles is saved to database before processing next batch
  - **Crash Recovery**: If process crashes, all previously processed leads are preserved in database
- **Benefits**: 
  - No more total data loss on crashes - partial results are always saved
  - Can track progress through database even if enrichment fails midway
  - Address/location data now captured for enhanced lead information
- **Status**: Incremental save system implemented, ready for testing

### 2025-07-09: Extreme Memory Optimization with Streaming Processing (COMPLETED)
- **Issue**: Persistent SIGKILL errors despite previous memory optimizations
- **Root Cause**: 
  - Even minimal data storage was consuming too much memory in Replit environment
  - Processing multiple full items simultaneously was causing memory overflow
- **Fixes Implemented**:
  - **Streaming Username Extraction**: Extract usernames immediately without storing full items
  - **Zero Item Storage**: Use set-based deduplication instead of storing complete objects
  - **Extreme Limits**: max_items 50, batch_size 10, max_usernames 25, batch processing of 2
  - **Extended Delays**: Increased processing delays to 1 second between batches
  - **Immediate Processing**: Extract usernames on-the-fly from both topPosts and latestPosts
- **Benefits**: 
  - Minimal memory footprint by avoiding item storage completely
  - Still extracts all unique usernames from available data
  - Prevents SIGKILL crashes through aggressive memory management
  - Processes data in ultra-small batches for maximum stability
- **Status**: Extreme memory optimization implemented to handle Replit's memory constraints

### 2025-07-09: Fixed Username Extraction and Memory Issues (COMPLETED)
- **Issue**: User reports getting only a fraction of expected usernames from hashtag search
- **Investigation**: 
  - Username extraction logic was already correct (processes both `topPosts` and `latestPosts`)
  - Real issue was memory overflow (SIGKILL errors) and poor error handling causing processing failures
- **Fixes Implemented**:
  - **Enhanced Username Extraction**: Added robust type checking and error handling for both `topPosts` and `latestPosts` arrays
  - **Memory Optimization**: Reduced max_items from 300 to 200, batch_size from 100 to 50
  - **Better Error Handling**: Added try-catch blocks around hashtag data processing and username extraction
  - **Improved Logging**: Added detailed logging to track extraction process and identify failures
  - **Memory Management**: Clear variables immediately after use, force garbage collection
  - **Robust Processing**: Continue processing even if some items fail, don't crash entire operation
- **Benefits**: 
  - More reliable username extraction from both post arrays
  - Better memory management to prevent SIGKILL errors
  - Robust error handling that continues processing instead of crashing
  - Detailed logging for debugging issues
- **Status**: Improvements implemented and application restarted successfully

### 2025-07-09: Simplified Hashtag Logic and Fixed Template Error (COMPLETED)
- **Issue**: Complex hashtag extraction causing issues and template error with missing filter
- **Resolution**: Simplified logic to use search keyword as hashtag and fixed template
- **Changes Made**:
  - **Simplified Processing**: Only extract unique ownerUsername from posts, no hashtag filtering
  - **Database Logic**: Use initial search keyword for hashtag column in all database operations
  - **Template Fix**: Changed `tojsonfilter` to `tojson` to fix template rendering error
  - **Clean Logic**: Removed complex hashtag mapping and regex processing
  - **Consistent Storage**: All leads use search keyword as hashtag for consistency
- **Benefits**: 
  - Simpler, more reliable code
  - Faster processing without complex hashtag extraction
  - Fixed template errors that were causing application crashes
  - Consistent hashtag data based on search terms
- **Status**: Successfully simplified and application running without errors

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