# Instagram LeadGen - Full-Stack Application

## User Preferences

**CRITICAL**: NEVER MAKE CODE CHANGES UNTIL USER APPROVAL
- All code modifications must be explicitly approved by the user before implementation
- Present proposed changes and wait for user confirmation
- Do not proceed with any code edits without explicit user consent

## Overview

K+L Influence is a Flask-based Instagram lead generation and outreach automation tool that crawls Instagram hashtags, enriches profile data, and generates personalized email outreach campaigns. The application features a modern, professional design following the K+L Internal Web App Style Guide, with Natural Green branding, Inter typography, and Google Sheets-style table interactions for efficient data management.

## Recent Changes

### 2025-07-22: Fixed Edit Modal Display Issue and Prevented Outside Click Closing (COMPLETED)
- **Issue**: After closing the email/subject template modal by clicking outside, the modal could not be reopened
- **Root Cause**: The `showEditModal` function only added the 'show' class but didn't set `style.display = 'flex'`, while `closeModal` set `style.display = 'none'`, preventing the modal from being visible again
- **Additional Issue**: Modal was closing when clicking outside, which interfered with user workflow
- **Solution Implemented**:
  - Updated `showEditModal` to set `modal.style.display = 'flex'` before adding the 'show' class
  - Added "X" close button to editModal header matching promptSettingsModal pattern
  - Updated cancel button to use unified `closeModal('editModal')` approach
  - Enhanced `closeModal` function with special cleanup for editModal (editingUsername, editingField)
  - Excluded editModal from global click-outside-to-close behavior (like promptSettingsModal)
- **Technical Implementation**:
  - Modified `showEditModal` function to match promptSettingsModal opening pattern
  - Updated HTML template to include close button in modal header
  - Modified global modal click listener to exclude both promptSettingsModal and editModal
  - Removed old `closeEditModal` function and unified all modal closing through `closeModal`
- **Benefits**:
  - Edit modal only closes via "X" button or "Cancel" button, not outside clicks
  - Modal can be reopened multiple times without page refresh
  - Consistent modal behavior across the application
  - Fixed the bug where users couldn't edit subject/email fields after closing modal once
- **Status**: Edit modal display and closing mechanism fixed - modal behavior now consistent with user expectations

### 2025-07-22: Fixed SQLAlchemy Relationship Loading for Checkbox Variables (COMPLETED)
- **Feature**: Fixed SQLAlchemy relationship loading issue that prevented product data from appearing in auto-generated email content
- **Root Issue**: Lead queries weren't loading the `selected_product` relationship, causing `lead.selected_product` to be None even when `selected_product_id` existed
- **Solution Implemented**:
  - **Eager Loading**: Added `db.joinedload(Lead.selected_product)` to lead query in `/draft-email/<username>` endpoint
  - **Single Query Load**: Lead and associated Product now loaded together in single database operation
  - **Relationship Fix**: `lead.selected_product` now contains actual Product object with name, URL, description
- **Technical Implementation**:
  - **Query Enhancement**: `Lead.query.options(db.joinedload(Lead.selected_product)).filter_by(username=username).first()`
  - **Proper Relationship Access**: Product data now accessible via `lead.selected_product.name`, `lead.selected_product.url`, etc.
  - **Auto-Generated Content**: Product variables now properly included in structured data sent to OpenAI
- **Expected Result**: OpenAI now receives complete structured data:
  ```
  Username: actiplant_suisse
  Full Name: actiplant_suisse
  Hashtag: #vitalpilzextrakt
  Product Name: Funghi Funk
  Product URL: https://www.kasimirlieselotte.de/shop/Funghi-Funk-Spray-50-ml-kaufen
  Product Description: Funghi Funk Spray 50ml - 100% rein - Hergestellt in Deutschland
  ```
- **Benefits**:
  - **Complete Data**: All checkbox variables (including product data) now pass real information to OpenAI
  - **Performance**: Single query loads both Lead and Product efficiently
  - **Reliable Relationships**: SQLAlchemy relationships work properly throughout application
  - **Personalized Emails**: OpenAI can generate truly personalized content with actual product information
- **Status**: SQLAlchemy relationship loading fixed - checkbox variables now send complete real data including product information to OpenAI

### 2025-07-22: Auto-Generated Structured Data System for Email Generation (COMPLETED)
- **Feature**: Implemented auto-generated structured data system that passes checkbox variables directly to OpenAI without complex template substitution
- **Root Issue**: Checkbox variables were collected correctly but had no template to populate, resulting in empty content sent to OpenAI
- **Solution Implemented**:
  - **Always Generate Data**: System always creates structured data from enabled checkbox variables regardless of user template existence
  - **Real Data Only**: Uses actual lead data (username, full_name, bio, hashtag, caption, product info) - no synthetic content
  - **User Text Integration**: When user provides template text, it's added to the front of auto-generated structured data
  - **No Fallbacks**: Removed all complex template substitution logic and fallback systems
- **Technical Implementation**:
  - **Auto Data Parts**: Creates `Username: actiplant_suisse\nFull Name: actiplant_suisse\nProduct Name: Funghi Funk` etc.
  - **Checkbox Filtering**: Only includes variables with enabled checkboxes in structured data
  - **Clean Logic**: Simplified from complex template parsing to straightforward data generation
  - **User Context**: Optional user text prepended with double newline separation for clarity
- **Two Scenarios Supported**:
  - **No User Text**: Returns pure structured data from checkbox variables
  - **With User Text**: Returns `{user_text}\n\n{structured_data}` for additional context like sales promotions
- **Benefits**:
  - **Always Functional**: Checkbox variables always get passed to OpenAI with real data
  - **Flexible Context**: Users can add specific instructions/context when needed
  - **No Empty Content**: Eliminates the empty string problem that broke email generation
  - **Simplified Architecture**: Removed complex template substitution in favor of clean data structure
- **Status**: Auto-generated structured data system fully implemented - checkbox variables now properly send real data to OpenAI

### 2025-07-22: Dynamic Prompt Template System with Conditional Variable Filtering (COMPLETED)
- **Feature**: Implemented sophisticated dynamic prompt template system where unchecked variables are completely excluded from AI prompts
- **Root Issue**: Variables were being sent to AI as empty data rather than being excluded from prompt instructions entirely
- **Solution Implemented**:
  - **Template Parser**: Created `parse_prompt_template()` function with conditional markup `[IF variable_enabled]content[/IF]`
  - **Dynamic System Prompts**: System prompts now filter out instruction sections for disabled variables
  - **Dynamic User Prompts**: User prompts exclude disabled variable data entirely from profile content
  - **Template Markup**: Both system and user prompts use conditional sections that get removed when variables are disabled
  - **Variable Settings Integration**: Checkbox states control which template sections remain active
- **Technical Implementation**:
  - **Template Syntax**: Uses `[IF variable_name_enabled]content[/IF]` conditional markup in all prompts
  - **System Prompt Filtering**: `parse_prompt_template()` removes instruction sections for unchecked variables
  - **User Content Building**: `build_dynamic_prompt_content()` creates contextually appropriate profile data
  - **Fallback Logic**: Robust fallback system ensures essential data (username) always included
  - **Default Templates**: Updated all default prompts with conditional markup for complete variable control
- **Benefits**:
  - **Clean AI Instructions**: AI never receives confusing references to disabled variables
  - **Contextual Prompts**: Instructions focus only on available data fields
  - **Dynamic Filtering**: Real-time template parsing based on checkbox selections
  - **Professional Output**: No empty classifiers or incomplete variable references sent to AI
- **Status**: Dynamic template system fully implemented - unchecked variables completely excluded from both system instructions and user data

### 2025-07-22: Connected Prompt Settings to Email Generation and Removed EmailTemplate Table (COMPLETED)
- **Issue**: Email generation was using EmailTemplate table while Prompt Settings updated SystemPrompt table - no connection between them
- **Root Cause**: Two separate database tables were being used for the same purpose without any integration
- **Solution Implemented**:
  - **Email Generation Fix**: Modified `/draft-email/<username>` endpoint to use SystemPrompt table instead of EmailTemplate
  - **Dynamic Prompt Selection**: Email generation now checks `has_product` flag from lead to select appropriate prompts
  - **EmailTemplate Removal**: Completely removed EmailTemplate model and all references from codebase
  - **Import Cleanup**: Removed EmailTemplate from model imports
  - **API Cleanup**: Removed `/api/email-templates` GET and POST endpoints
  - **Index Route Update**: Removed EmailTemplate queries from main index route
- **Technical Implementation**:
  - Email generation queries SystemPrompt table based on `prompt_type` and `has_product` flag
  - Fallback to default prompts if SystemPrompt entries don't exist
  - Simplified architecture with single source of truth for prompts
- **Benefits**:
  - **Working Integration**: Changes in Prompt Settings now directly affect email generation
  - **Cleaner Architecture**: Single table for all prompt management
  - **Consistent Behavior**: No more confusion between two separate prompt systems
  - **Simplified Codebase**: Removed redundant EmailTemplate model and endpoints
- **Status**: Prompt Settings and email generation are now properly connected through SystemPrompt table

### 2025-07-22: Fixed Caption Data Loss in Hashtag Discovery Phase (COMPLETED)
- **Issue**: Caption data was being extracted correctly by APIFY actor but never saved to hashtag_username_pair table during discovery phase
- **Root Cause Discovery Process**:
  1. **Initial Theory**: Emoji encoding issues during database save operations
  2. **Emoji-Safe Processing**: Implemented `clean_caption_for_database()` function with UTF-8 encoding safety
  3. **True Root Cause Found**: Caption data was being discarded during hashtag discovery phase, not due to emoji encoding
- **Actual Problem**: The `discover_hashtags_async` function was creating profile data structures WITHOUT caption field
- **Debug Evidence**: 
  - Extraction phase: `caption_length=1124, caption_preview=Leider habe ich es gestern...`
  - Discovery phase: Only storing `username`, `hashtag`, `timestamp`, `post_url` - **NO CAPTION**
  - Database save: `caption=None` because caption was never included in profile data
- **Solution Implemented**:
  - **Discovery Phase Fix**: Added `caption = item.get('caption', '')` to hashtag item processing loop
  - **Profile Data Structure**: Updated `hashtag_usernames` to include caption field
  - **Database Save**: Modified `all_profiles` creation to include caption in profile dictionary
  - **Enhanced Debug Logging**: Added caption length and preview to discovery phase logging
  - **Emoji-Safe Processing**: Retained emoji-safe handling as defensive programming measure
- **Technical Implementation**:
  - Fixed lines 1548, 1564, 1591 in `discover_hashtags_async` function
  - Caption data now flows: APIFY extraction → Discovery processing → Profile creation → Database save
  - Enhanced debug logging shows caption extraction during discovery phase
  - Emoji-safe processing ensures robust database storage
- **Benefits**:
  - **Complete Caption Preservation**: Instagram post captions now saved to hashtag_username_pair table
  - **Data Pipeline Integrity**: Caption data flows through entire processing pipeline
  - **Enhanced Debug Visibility**: Clear tracking of caption data at every stage
  - **Robust Encoding**: Emoji-safe processing handles international characters and emojis
- **Status**: Caption data loss fully resolved - captions now save correctly to both hashtag_username_pair and lead tables
- **Verification Confirmed**: Database inspection shows complete caption preservation with emojis and German content intact throughout entire pipeline

### 2025-07-22: Added Caption Field (Beitragstext) to Hashtag Discovery and Lead Enrichment (COMPLETED)
- **Feature**: Implemented caption field extraction from APIFY Actor DrF9mzPPEuVizVF4l for post content tracking
- **Database Schema Changes**:
  - **HashtagUsernamePair Model**: Added `beitragstext` Text column to store Instagram post captions
  - **Lead Model**: Added `beitragstext` Text column to store original post captions during enrichment
  - **Model Updates**: Enhanced `to_dict()` methods in both models to include beitragstext field
- **Data Extraction Enhancement**:
  - **APIFY Integration**: Modified `call_apify_actor_sync` to extract `caption` field from both `latestPosts` and `topPosts`
  - **Data Processing**: Updated username_data_map structure to include caption alongside hashtag, timestamp, and post_url
  - **Profile Building**: Enhanced processed_items creation to include caption data when available
- **Database Saving Logic**:
  - **HashtagUsernamePair**: Updated `save_hashtag_username_pairs` to save caption as `beitragstext` for both new and existing records
  - **Lead Enrichment**: Modified `save_leads_incrementally` to transfer caption from HashtagUsernamePair to Lead records
  - **Data Transfer**: Enhanced hashtag pair lookup to extract and transfer caption during lead creation/updates
- **Technical Implementation**:
  - Enhanced extraction logic in both latestPosts and topPosts processing loops
  - Added caption field to profile data structure with proper null handling
  - Updated database creation and update operations for both tables
  - Implemented proper data flow from Instagram posts → HashtagUsernamePair → Lead records
  - Added debug logging for caption data tracking (truncated to 50 characters for readability)
- **Benefits**:
  - **Content Analysis**: Access to original Instagram post content for lead qualification
  - **Campaign Intelligence**: Understanding of user engagement through post captions
  - **Targeted Outreach**: Personalized messaging based on actual post content
  - **Data Completeness**: Full post context preserved throughout the lead generation pipeline
- **Status**: Caption field extraction and storage fully implemented across all database tables and processing stages

### 2025-07-21: Fixed Hashtag Matching for Timestamp and Post URL Data Transfer (COMPLETED)
- **Issue**: Timestamp and post_url data was being captured correctly in hashtag_username_pair table but not transferring to leads table during enrichment
- **Root Cause**: Hashtag mismatch during enrichment lookup - stored hashtag variants (e.g., 'pilzextrakten') didn't match search keywords (e.g., 'pilzextrakt')
- **Solution Implemented**:
  - **Enhanced Hashtag Matching**: Added intelligent hashtag matching logic with three fallback levels:
    1. Exact keyword match (original behavior)
    2. Partial match using LIKE '%keyword%' for hashtag variants
    3. Fallback to any hashtag pair for the username
  - **Debug Logging**: Added comprehensive logging to track hashtag matching success/failure
  - **Data Flow Fix**: Enhanced `save_leads_incrementally` function with robust hashtag pair lookup
- **Technical Details**:
  - Modified hashtag pair query to handle Instagram's hashtag variations
  - Added LIKE pattern matching for hashtag variants containing the search keyword
  - Implemented fallback mechanism to ensure data is never lost due to minor hashtag differences
  - Added detailed logging for debugging hashtag matching issues
- **Verification**:
  - Successfully tested with existing data where 'pilzextrakt' search matches 'pilzextrakten' stored hashtag
  - Lead ID 154 now properly shows timestamp '2022-11-06 19:18:45' and post_url 'https://www.instagram.com/p/CkoYbfCAWyP/'
  - Confirmed data flows from hashtag_username_pair to lead table during enrichment
- **Benefits**:
  - Timestamp and post URL data now properly transfers to leads table
  - Robust handling of Instagram hashtag variations and plurals
  - Enhanced data integrity with intelligent matching fallbacks
  - Complete audit trail from original Instagram posts to final leads
- **Status**: Hashtag matching fix fully implemented and verified with real data

### 2025-07-18: Added Timestamp and Post URL Tracking to Hashtag Data Collection (COMPLETED)
- **Update**: Extended first Apify API call to capture timestamp and post URL from Instagram posts
- **New Fields Added**:
  - **HashtagUsernamePair Table**: Added `timestamp` (DateTime) and `post_url` (String) fields
  - **Lead Table**: Added `source_timestamp` and `source_post_url` fields to store original post data
- **Data Flow Enhancement**:
  - **Extraction**: Modified `call_apify_actor_sync` to extract `timestamp` and `url` from Instagram posts
  - **Storage**: Updated `save_hashtag_username_pairs` to save timestamp and post URL data
  - **Enrichment**: Enhanced Lead creation to include source post information from HashtagUsernamePair table
- **Technical Implementation**:
  - Enhanced data extraction from both `latestPosts` and `topPosts` arrays
  - ISO timestamp parsing with proper timezone handling
  - Preference for latest timestamp when multiple posts exist for same username
  - Database schema updates with new columns in both tables
  - Automatic data transfer during lead enrichment process
- **Benefits**:
  - Track when posts were originally created for trend analysis
  - Direct access to original Instagram post URLs for manual review
  - Enhanced lead qualification with post timing data
  - Better content analysis and engagement tracking
- **Status**: Fully implemented and integrated with existing hashtag discovery workflow

### 2025-07-18: Added Business Account Detection Field (COMPLETED)
- **Feature**: Implemented `is_business` field to identify Instagram business accounts from Apify profile enrichment
- **Database Changes**:
  - **Lead Model**: Added `is_business` boolean column to Lead model with default False
  - **LeadBackup Model**: Added `is_business` column to backup table for consistency
  - **Database Migration**: Applied ALTER TABLE statements to add column to existing database
- **API Integration**: 
  - **Profile Enrichment**: Enhanced lead creation to capture `is_business` field from Apify actor `8WEn9FvZnhE7lM3oA`
  - **Data Mapping**: Added `is_business=lead_data.get('is_business', False)` to lead creation process
  - **Backup Function**: Updated backup function to include `is_business` field preservation
- **Export Functionality**:
  - **CSV Export**: Added "Business Account" column to CSV export with Yes/No values
  - **JSON Export**: Included `isBusiness` field in lead dictionary serialization
  - **Google Sheets Compatible**: Business account status exported as human-readable text
- **Technical Implementation**:
  - Database schema updated with ALTER TABLE commands for both `lead` and `lead_backup` tables
  - Lead creation enhanced to capture business account status from profile enrichment API
  - Export functions updated to include business account detection in all formats
- **Benefits**:
  - **Lead Qualification**: Easily identify business vs personal Instagram accounts
  - **Targeting Precision**: Better lead segmentation for business-focused outreach campaigns
  - **Export Analytics**: Business account data included in all lead exports for analysis
- **Status**: Business account detection fully implemented and operational

### 2025-07-18: Fixed Hashtag Selection UI Bug (COMPLETED)
- **Bug Identified**: Auto-revert functionality in hashtag selection was causing the UI to close prematurely when users unselected hashtag variants
- **Root Cause**: Checkbox change events and global click listeners were triggering automatic revert to leads table, leaving users with blank canvas
- **Fix Implemented**:
  - **Removed Auto-Revert on Checkboxes**: Eliminated checkbox change event listeners that triggered automatic revert
  - **Removed Global Click Listener**: Disabled container-wide click events that caused premature UI closure
  - **Preserved Cancel Functionality**: Kept revert behavior only for "Cancel" button to maintain expected user flow
  - **Maintained Selection State**: Users can now freely select/deselect hashtag variants without losing the UI
- **User Experience Improvements**:
  - **Stable UI**: Hashtag selection interface remains open during selection process
  - **Proper Workflow**: Users can complete hashtag selection without premature UI closure
  - **Expected Behavior**: Only "Cancel" button and "Continue with Enrichment" trigger UI changes
  - **No Blank Canvas**: Fixed issue where unselecting variants left users with empty display
- **Technical Changes**:
  - Removed `setTimeout(revertToLeadsTable, 300)` from checkbox change events
  - Removed global container click listener that triggered auto-revert
  - Simplified button event handlers to remove unnecessary revert calls
  - Preserved cancel button functionality for proper user exit path
- **Status**: Hashtag selection UI now functions correctly without premature closure

### 2025-07-17: PostgreSQL Database Integration (COMPLETED)
- **Update**: Successfully integrated PostgreSQL database using Replit's database service
- **Database Setup**:
  - **Database Creation**: Created PostgreSQL database instance with auto-configured environment variables
  - **Connection Configuration**: Updated Flask app to use `DATABASE_URL` environment variable
  - **SSL Configuration**: Configured secure connection with `sslmode=prefer`
  - **Connection Pool**: Optimized connection pooling with 300s recycle time and pre-ping enabled
  - **Application Name**: Set connection application name to "KL_Influence" for monitoring
- **Tables Created**:
  - `email_template` - Stores email generation templates for subjects and bodies
  - `hashtag_username_pair` - Stores deduplicated hashtag-username pairs from Instagram
  - `lead` - Main table for Instagram lead data with contact information
  - `lead_backup` - Backup table for lead data preservation
  - `processing_session` - Tracks processing sessions and status
  - `product` - Stores product information for personalized emails
- **Data Initialization**:
  - **Email Templates**: Automatically creates default subject and body templates for German influencer outreach
  - **Product Catalog**: Initializes Zeck Zack and Funghi Funk products with URLs and descriptions
  - **Database Seeding**: Populates essential data on application startup
- **Benefits**:
  - Reliable PostgreSQL database with automatic backups and scaling
  - Secure connections with SSL support
  - Optimized connection pooling for better performance
  - Automatic table creation and data seeding on startup
  - Environment-based configuration for easy deployment
- **Technical Implementation**:
  - Database URI configured via `DATABASE_URL` environment variable
  - SQLAlchemy ORM with PostgreSQL-specific optimizations
  - Connection pooling with health checks and timeouts
  - Secure SSL connections with prefer mode
  - Automatic schema creation with `db.create_all()`
- **Status**: PostgreSQL database fully integrated and operational with all tables created and seeded

### 2025-07-17: Pre-set Follower Range Filters Implementation (COMPLETED)
- **Update**: Implemented intuitive dropdown-based follower filtering with pre-set ranges instead of manual comparison operators
- **Features Implemented**:
  - **Dropdown Filter Interface**: Replaced text input with professional dropdown selection for follower ranges
  - **Pre-set Range Options**: Added industry-standard influencer tiers:
    - Micro-influencers: 1-100, 100-1K, 1K-10K, 10K-50K, 50K-100K
    - Macro-influencers: 100K-500K, 500K-1M, 1M+ followers
  - **Custom Filter Fallback**: "Benutzerdefiniert..." option reveals text input for advanced users
  - **Range Filtering Logic**: Enhanced `applyFilters()` to handle range-based filtering (e.g., "1000-10000")
  - **Backward Compatibility**: Maintained existing comparison operators (>, <, >=, <=, =) for custom input
  - **UI Consistency**: Added matching CSS styling with K+L branding colors and hover effects
  - **Smart State Management**: Proper show/hide logic for custom input based on dropdown selection
- **User Experience Improvements**:
  - **One-Click Filtering**: Users can filter by follower ranges with single dropdown selection
  - **Professional Appearance**: Dropdown looks more polished than text input with comparison operators
  - **Error Reduction**: No need to remember comparison syntax - intuitive range selection
  - **Accessibility**: Better for users unfamiliar with mathematical comparison operators
  - **Clear Categories**: Pre-defined ranges match common influencer marketing industry standards
- **Technical Implementation**:
  - **HTML Structure**: Dropdown with hidden custom input that shows on "custom" selection
  - **JavaScript Logic**: Enhanced `initializeTableFilters()` with separate event handlers for dropdown and custom input
  - **Range Parsing**: Modified filtering logic to handle "min-max" format in `applyFilters()`
  - **CSS Styling**: Added `.filter-select` class with consistent K+L branding and custom dropdown arrow
  - **Filter Reset**: Updated `clearFilters()` to properly reset both dropdown and custom input
- **Filter Options**:
  - "Alle Follower" (no filter)
  - "1 - 100" (1-100 followers)
  - "100 - 1K" (100-1000 followers)
  - "1K - 10K" (1000-10000 followers)
  - "10K - 50K" (10000-50000 followers)
  - "50K - 100K" (50000-100000 followers)
  - "100K - 500K" (100000-500000 followers)
  - "500K - 1M" (500000-1000000 followers)
  - "1M+" (1000000+ followers)
  - "Benutzerdefiniert..." (reveals custom text input)
- **Benefits**:
  - Faster lead filtering with industry-standard follower ranges
  - More intuitive user interface matching professional data management tools
  - Reduced learning curve for new users
  - Maintained advanced functionality for power users
  - Enhanced visual consistency with existing K+L design system
- **Status**: Pre-set follower range filters fully implemented and ready for testing

### 2025-07-15: Auto-Revert Hashtag Selection to Leads Table (COMPLETED)
- **Update**: Modified hashtag selection interface to automatically revert to leads table on any interaction
- **Features Implemented**:
  - **Global Click Listener**: Added click event listener to entire hashtag selection container
  - **Automatic Revert Function**: Created `revertToLeadsTable()` function that clears selection UI and shows leads table
  - **Smart Event Handling**: 
    - All buttons use `stopPropagation()` to prevent immediate container click
    - Checkbox changes trigger revert after small delay to show user feedback
    - Button clicks execute their function then revert with appropriate timing
  - **Fetch All Leads Function**: Added `fetchAndDisplayAllLeads()` helper function to retrieve and display current leads
  - **User Feedback**: Shows "Zurück zur Leads-Tabelle" toast message when reverting
  - **State Management**: Properly resets lead generation state and processing UI
- **Interaction Triggers**:
  - Clicking anywhere on hashtag selection container
  - Selecting/deselecting individual hashtags
  - Clicking "Alle auswählen" or "Alle abwählen" buttons
  - Clicking "Mit Anreicherung fortfahren" button
  - Clicking "Abbrechen" button
- **Benefits**:
  - Prevents users from getting stuck in hashtag selection interface
  - Always returns to functional leads table view
  - Maintains smooth user workflow and prevents UI confusion
  - Automatic fallback ensures users can always access their data
- **Status**: Auto-revert functionality fully implemented and operational

### 2025-07-15: Resource Protection with UI State Management (COMPLETED)
- **Update**: Implemented mutual exclusion between lead generation and email draft creation to prevent resource strain
- **Features Implemented**:
  - **Global State Management**: Added `isLeadGenerationInProgress` and `isEmailDraftGenerationInProgress` state variables
  - **UI Protection System**: Automatically disables/greys out conflicting UI elements based on processing states
  - **Lead Generation Protection**: 
    - Disables "Leads generieren" button when email drafts are being created
    - Greys out keyword input and search limit fields during email generation
    - Shows informative tooltips explaining why buttons are disabled
  - **Email Draft Protection**:
    - Disables all "Email" buttons in results table when lead generation is running
    - Prevents multiple simultaneous email generations
    - Shows warning messages when attempting conflicting operations
  - **Smart State Updates**: `updateUIState()` function manages all UI elements based on current processing states
  - **Comprehensive Integration**: State management integrated into all relevant functions:
    - `processKeyword()` - Lead generation initiation
    - `continueWithEnrichment()` - Profile enrichment phase
    - `generateEmailContent()` - Individual email draft creation
    - `displayResults()` - Table rendering with proper button states
- **User Experience Improvements**:
  - Clear visual feedback with opacity changes and informative tooltips
  - Prevents accidental resource conflicts that could crash the system
  - User-friendly warning messages in German explaining why actions are blocked
  - Automatic state cleanup when processes complete or are cancelled
- **Technical Implementation**:
  - State variables track processing status globally
  - `setLeadGenerationState()` and `setEmailDraftGenerationState()` manage state transitions
  - `updateUIState()` applies visual changes to all affected UI elements
  - Integration with existing `finally` blocks ensures proper cleanup
  - Initialization in `DOMContentLoaded` ensures correct initial state
- **Benefits**:
  - Prevents system overload from simultaneous heavy API operations
  - Reduces risk of memory issues and crashes during processing
  - Clearer user workflow with obvious next steps
  - Professional UX with proper loading states and user guidance
- **Status**: Resource protection system fully implemented and operational

### 2025-07-15: Basic Login Authentication System (COMPLETED)
- **Update**: Added comprehensive login system with password protection using Replit secrets
- **Security Implementation**:
  - **Login Required Decorator**: Created `@login_required` decorator to protect all application routes
  - **Session Management**: Implemented Flask sessions with 24-hour permanent session lifetime
  - **Password Authentication**: Uses `APP_PASSWORD` environment variable from Replit secrets
  - **Login Page**: Modern login interface matching K+L Influence branding with Natural Green colors
  - **Route Protection**: Protected all 18+ application routes including API endpoints, data exports, and admin functions
  - **Logout Functionality**: Added logout button in navigation bar and `/logout` route
- **User Experience**:
  - **Elegant Login UI**: Professional login page with K+L Influence logo and branding
  - **Password Validation**: Client-side and server-side password validation with error messages
  - **Session Persistence**: 24-hour session duration with automatic logout after timeout
  - **Redirect Logic**: Automatic redirect to login page when accessing protected routes
  - **Navigation Integration**: Logout button added to main navigation bar
- **Technical Implementation**:
  - **Authentication Routes**: `/login` (GET/POST) and `/logout` routes added
  - **Session Security**: Uses `SESSION_SECRET` environment variable for session encryption
  - **Password Storage**: Password stored securely in Replit secrets as `APP_PASSWORD`
  - **Error Handling**: Proper error messages for invalid password attempts
  - **Mobile Responsive**: Login page fully responsive for mobile devices
- **Protected Routes**: All application functionality now requires authentication:
  - Main application (`/`)
  - Lead generation (`/process`, `/stop-processing`)
  - Data management (`/export/*`, `/clear`, `/api/leads`)
  - Email functionality (`/draft-email/*`, `/send-email/*`)
  - Settings and templates (`/api/email-templates`, `/api/products`)
  - Debug and monitoring (`/debug`, `/api-metrics`, `/api-health`)
- **Benefits**:
  - Secure access control preventing unauthorized usage
  - Professional login experience matching brand identity
  - Session-based authentication with reasonable timeout
  - Easy password management through Replit secrets
  - Complete route protection covering all application features
- **Status**: Authentication system fully implemented and operational with elegant UI

### 2025-07-14: Fixed URL Encoding and Missing HTML Container Issues (COMPLETED)
- **Update**: Fixed URL-encoded hashtag display and missing resultsContainer element
- **Issues Resolved**:
  - Hashtag names were displaying URL-encoded (e.g., `zeckenhalsb%c3%a4nder` instead of `zeckenhalsbänder`)
  - Missing `resultsContainer` div in HTML template prevented hashtag selection UI from displaying
  - Undefined `keyword` variable in `call_apify_actor_sync` function caused extraction errors
- **Fixes Implemented**:
  - **URL Decoding**: Added `urllib.parse.unquote()` to decode URL-encoded hashtag names in `discover_hashtags_async`
  - **HTML Structure**: Added missing `resultsContainer` div to wrap the main content area in index.html
  - **Keyword Parameter**: Fixed keyword extraction from `input_data` in `call_apify_actor_sync` function
  - **Debug Logging**: Added console logging to frontend response processing for better debugging
- **Technical Details**:
  - URL decoding ensures proper German character display (ä, ö, ü, ß)
  - HTML container structure now supports dynamic content injection for hashtag selection
  - Keyword parameter properly extracted from search input for hashtag fallback
- **Benefits**:
  - Hashtag variants now display with proper German characters and umlauts
  - Hashtag selection UI displays correctly in the main content area
  - Better user experience with readable hashtag names
  - Improved debugging capabilities for response handling
- **Status**: All fixes implemented and hashtag selection functionality working correctly

### 2025-07-14: Hashtag Selection Step Before Enrichment (COMPLETED)
- **Update**: Added intermediate hashtag selection step after discovery phase
- **New Workflow**: 
  1. User enters keyword and search limit
  2. System discovers hashtag variants and shows them for selection
  3. User selects which hashtag variants to enrich
  4. System proceeds with enrichment only for selected hashtags
- **Changes Made**:
  - **Backend Split**: Separated processing into two phases:
    - `discover_hashtags_async`: Finds hashtag variants without enrichment
    - `enrich_selected_profiles_async`: Enriches only selected profiles
  - **New API Endpoints**:
    - `/api/hashtag-variants`: Returns discovered hashtag variants with user counts
    - `/continue-enrichment`: Processes selected hashtags for enrichment
  - **Frontend Updates**:
    - Created hashtag selection UI with checkboxes and user counts
    - Added "Select All" and "Deselect All" buttons for convenience
    - Shows number of profiles per hashtag variant
    - Continue button proceeds with enrichment for selected hashtags only
  - **Styling**: Added CSS for hashtag selection container with K+L branding
- **Benefits**:
  - Users can avoid processing irrelevant hashtag variants
  - Saves time and API calls by skipping unwanted hashtags
  - Better control over which profiles to enrich
  - Clear visibility of hashtag distribution before processing
- **Status**: Hashtag selection functionality fully implemented and operational

### 2025-07-13: Extended Worker Timeout to 2 Hours (COMPLETED)
- **Update**: Increased worker timeout from 30 minutes to 2 hours to handle long processing runs
- **Issue**: Worker timeout error occurred during large batch processing with multiple anti-spam pauses
- **Root Cause**: Processing with 33+ leads and 90-second pauses between batches exceeded 30-minute timeout
- **Fixes Implemented**:
  - **Backend Timeout**: Increased gunicorn worker timeout from 1800s (30min) to 7200s (2h)
  - **Frontend Timeout**: Updated both `ui.js` and `kl-influence-app.js` fetch timeouts to 7320000ms (2h 2min)
  - **Timeout Alignment**: Ensures frontend waits slightly longer than backend for proper error handling
- **Technical Details**:
  - Modified `gunicorn.conf.py` timeout configuration
  - Updated frontend JavaScript timeout in fetch requests
  - Prevents "WORKER TIMEOUT" errors during extended processing
- **Benefits**:
  - Can process large datasets with multiple batches without timeout
  - Handles extensive anti-spam pause sequences (90s between batches)
  - Stable processing for up to 2 hours of continuous operation
- **Status**: 2-hour timeout configuration implemented and application restarted

### 2025-07-13: Fixed Progress Display and Hashtag Storage (COMPLETED)
- **Update**: Fixed two critical issues with progress tracking and hashtag data storage
- **Issue 1 - Progress Display**: Progress was stuck at "1." and didn't show profile counts or enrichment progress
- **Issue 2 - Hashtag Storage**: Only storing input keyword instead of actual hashtags from Instagram posts
- **Fixes Implemented**:
  - **Hashtag Extraction**: Modified `call_apify_actor_sync` to extract both username AND hashtag ID from each post
  - **Username-Hashtag Mapping**: Changed from simple username set to username-hashtag map to preserve hashtag data
  - **Progress Updates**: Added de-duplication statistics display after hashtag search
  - **Enrichment Progress**: Shows "X/Y Profile angereichert" during batch processing
  - **De-duplication Display**: Shows total found, existing in DB, and new to enrich counts
- **Technical Details**:
  - Extracts hashtag from item fields: `id`, `ID`, `hashtag`, `name` (falls back to keyword)
  - Stores hashtag with each username in the extraction phase
  - Progress now shows: "139 Profile gefunden (60 bereits in Datenbank, 79 werden angereichert)"
  - During enrichment shows: "24/79 Profile angereichert - Batch 9/27"
- **Benefits**:
  - Users can see exact progress and de-duplication statistics
  - Proper hashtag tracking for analytics and filtering
  - Clear visibility into what the system is doing at each step
- **Status**: Progress tracking and hashtag storage fully fixed and operational

### 2025-07-13: Implemented User-Controlled Stop Processing Feature (COMPLETED)
- **Update**: Added comprehensive stop functionality allowing users to cancel lead generation processing at any time
- **Features Implemented**:
  - **Stop Button UI**: Added stop button that appears during processing and replaces run button
  - **Backend Stop Endpoint**: Created `/stop-processing` API endpoint to handle stop requests
  - **Stop Flag System**: Implemented `app_data['stop_requested']` flag for graceful processing cancellation
  - **Stop Check Points**: Added stop checks at critical processing points:
    - Before hashtag search starts
    - Before each batch of profile enrichment
    - During long-running operations
  - **Graceful Shutdown**: Stop requests preserve any leads already processed and saved to database
  - **UI State Management**: Proper button state transitions (run → stop → run) with loading indicators
  - **Progress Integration**: Stop status integrated with progress tracking system
  - **Notification Cleanup**: Reduced notification spam by only showing notifications for significant batches (3+ leads)
  - **Notification Throttling**: Added 3-second cooldown between notifications to prevent spam
- **Technical Implementation**:
  - Stop checks at beginning of hashtag search and before each enrichment batch
  - Partial results preservation when processing is stopped mid-way
  - Button state management with proper disabled/enabled states
  - Progress status shows "Stoppe Verarbeitung..." when stop is requested
  - Clean UI reset after stop completion
- **Benefits**:
  - Users have full control over processing and can stop long-running operations
  - No data loss - any leads processed before stop are preserved
  - Better user experience with responsive stop functionality
  - Cleaner notification system without overwhelming spam
  - Immediate feedback when stop is requested
- **Status**: Stop functionality fully implemented and tested - works with slight delay as expected

### 2025-07-13: Removed Debug Logger Module and Fixed Syntax Errors (COMPLETED)
- **Update**: Successfully removed all references to the missing debug_logger module and fixed all resulting syntax errors
- **Issue**: Application failed to start with ModuleNotFoundError for debug_logger, followed by cascading syntax errors
- **Resolution**: 
  - Removed import statement for non-existent debug_logger module
  - Cleaned up all 29 references to debug_logger throughout main.py
  - Fixed multiple syntax errors caused by incomplete cleanup:
    - Added missing closing braces for dictionaries in exception handlers
    - Fixed orphaned code fragments (stray parentheses and parameters)
    - Corrected indentation errors from leftover debug_logger code
    - Fixed unclosed dictionaries in API response handlers
  - Replaced debug_logger calls with standard Python logger
  - Simplified error handling to use Python's built-in logging
- **Challenges**:
  - Initial cleanup script left orphaned code fragments causing syntax errors
  - Multiple cascading syntax errors required fixing one-by-one
  - Structural damage to code required careful manual repair
- **Benefits**:
  - Application now starts successfully without dependency errors
  - Cleaner codebase with standard Python logging
  - Reduced complexity by removing unnecessary debug infrastructure
  - All functionality preserved while removing unused debug features
- **Status**: All syntax errors fixed and application running successfully on port 5000

### 2025-07-12: Advanced Anti-Scraping Strategy with Batch Groups and Extended Timeouts (COMPLETED)
- **Update**: Implemented advanced anti-scraping strategy with batch groups and 30-minute timeout configuration
- **Strategy**: Process 3 profiles, wait 90s, repeat 3x, then wait 3 minutes before next group
- **Changes Made**:
  - Increased gunicorn worker timeout from 600s to 1800s (30 minutes)
  - Updated frontend JavaScript timeout to match (1800000 milliseconds)
  - Reduced batch size from 5 to 3 profiles per batch
  - Implemented batch grouping logic: after every 3 batches, wait 3 minutes instead of 90 seconds
  - Updated progress display to show "Erweiterte Anti-Spam Pause (3min)" for group pauses
  - Enhanced time estimation to accurately calculate remaining time with new pause pattern
  - Adjusted semaphore limit from 5 to 3 to match new batch size
- **Technical Implementation**:
  - Batch position calculation: `batch_position_in_group = i % 3`
  - Extended pause after groups: 180 seconds vs standard 90 seconds
  - Time calculation: Full groups = 2×90s + 1×180s = 360s total pause time
  - Progress messages differentiate between standard and extended pauses
- **Benefits**:
  - More sophisticated anti-scraping evasion with varied pause patterns
  - Reduced likelihood of Instagram detection and blocking
  - Better memory management with smaller batch sizes
  - Longer timeout prevents any processing interruption
  - Clear user feedback about different pause types
- **Status**: Advanced anti-scraping strategy fully implemented and operational

### 2025-07-12: Fixed Worker Timeout During Anti-Spam Pauses (COMPLETED)
- **Update**: Resolved timeout issues during 90-second anti-spam pauses by increasing worker timeout configuration
- **Issue**: Gunicorn worker was timing out with "Processing timed out after 3 minutes" error during anti-spam pauses
- **Resolution**: 
  - Increased gunicorn worker timeout from 180 seconds to 600 seconds (10 minutes)
  - Updated frontend JavaScript timeout to match (600000 milliseconds)
  - Fixed pause time calculations from 135 to 90 seconds throughout codebase
  - Confirmed pause implementation already uses non-blocking `asyncio.sleep()`
- **Technical Details**:
  - Modified `gunicorn.conf.py` to set `timeout = 600` with explanatory comment
  - Updated `kl-influence-app.js` fetch timeout to 600000ms
  - Corrected pause duration calculations in time estimation logic
  - No changes needed to pause mechanism - already using async/await properly
- **Benefits**:
  - Processing no longer times out during 90-second anti-spam pauses
  - Can handle longer processing runs with multiple batches
  - Maintains minimum 90-second pause for Instagram anti-spam protection
  - Better stability for production deployments
- **Status**: Timeout configuration fixed and application restarted successfully

### 2025-07-12: Enhanced Progress Display with Detailed Step Information (COMPLETED)
- **Update**: Completely redesigned progress tracking to show detailed step-by-step information with time estimates
- **Changes Made**:
  - **Detailed Step Names**: Changed from generic "Initializing" to specific steps like "1. Suche Instagram-Profile für Hashtag", "2. Erweitere Profil-Informationen", etc.
  - **Phase Tracking**: Added phase indicators (hashtag_search, profile_enrichment, completed) for better UX
  - **Time Estimates**: Each batch shows estimated time including pause duration (e.g., "ca. 2.4min")
  - **Batch Progress**: Shows current batch number and total batches during processing (e.g., "Batch 1/3")
  - **Perplexity Indicators**: Displays when Perplexity API is enriching contact data for specific users
  - **Anti-Spam Progress**: Clear pause countdown with next batch information ("⏸ Anti-Spam Pause: 1m 30s bis Batch 2/3")
  - **Completion Status**: Final step shows "3. Fertig! X Leads erfolgreich generiert und gespeichert ✓"
  - **Reduced Pause Time**: Updated from 2m15s to 90 seconds to prevent worker timeouts while maintaining anti-spam protection
- **UI Enhancements**:
  - Progress text shows phase-specific information
  - Real-time countdown during pauses with next batch preview
  - Visual indicators for different processing phases
  - German language progress messages for better user experience
- **Technical Implementation**:
  - Added phase tracking fields to progress object
  - Enhanced batch processing to update step names dynamically
  - Improved time calculation with batch-specific estimates
  - Phase-aware progress display in frontend JavaScript
  - Updated all pause references from 135s to 90s for faster processing
- **Benefits**:
  - Users know exactly what step the system is performing
  - Clear time estimates for each phase including pauses
  - Better understanding of the anti-spam protection process
  - No more confusion about what "Initializing" means
  - Faster processing with 90-second pauses preventing worker timeouts
- **Status**: Detailed progress display fully implemented with step-by-step information and optimized pause timing

### 2025-07-12: Fixed Automatic Sheet Updates During Processing (COMPLETED)
- **Update**: Enhanced the automatic sheet update mechanism to properly refresh leads without requiring page reload
- **Issue**: Leads were being generated but not automatically appearing in the sheet during processing
- **Resolution**: 
  - Added lead count tracking to detect when new leads are saved
  - Enhanced progress update function to compare current vs previous lead counts
  - Implemented automatic table refresh when lead count increases
  - Added visual feedback with opacity transitions and background color flash
  - Console logging for debugging automatic updates
- **Features**:
  - Automatic detection of new leads during processing
  - Real-time table refresh with visual indicators
  - Toast notifications when new leads are detected
  - Smooth visual transitions showing table updates
  - Lead count tracking resets between processing runs
- **Technical Details**:
  - `previousLeadCount` variable tracks last known lead count
  - Progress polling detects incremental changes every 2 seconds
  - `refreshLeadsTable()` fetches and displays new leads automatically
  - Visual feedback includes opacity changes and green background flash
- **Status**: Automatic sheet updates now working without page refresh

### 2025-07-12: Implemented Instagram Anti-Spam Batch Processing (COMPLETED)
- **Update**: Modified enrichment process to use 5-profile batches with 2m15s pauses to evade Instagram's switch kill blocker
- **Changes Made**:
  - **Batch Size**: Increased from 2 to 5 profiles per batch for more efficient processing
  - **Anti-Spam Pauses**: Implemented 2m15s (135 seconds) pauses between batches to avoid detection and prevent worker timeouts
  - **Progress Tracking**: Enhanced progress display to show pause countdowns with real-time updates
  - **Time Estimation**: Updated calculation to include pause time in total estimated processing time
  - **Semaphore Adjustment**: Increased concurrent processing limits to match new batch size (5 concurrent, 2 Perplexity)
  - **Pause Countdown**: Visual countdown showing minutes and seconds remaining during 2m15s anti-spam pauses
  - **Smart Timing**: No pause after the final batch to avoid unnecessary waiting
- **Benefits**:
  - Reduced risk of Instagram anti-spam detection and account blocking
  - More efficient batch processing with 5 profiles instead of 2
  - Clear user feedback during pause periods with countdown display
  - Better time estimation including pause periods for accurate progress tracking
  - Maintained data integrity with incremental saves after each batch
  - Reduced pause time from 5 minutes to 2m15s to prevent worker timeouts
- **Technical Details**:
  - Batches process 5 profiles sequentially with async/await for non-blocking execution
  - Pause countdown updates every 15 seconds to provide user feedback
  - Total time calculation: hashtag search + (batch time + pause time) × (batches - 1) + final batch
  - Progress status shows current pause time remaining before next batch starts
  - Worker timeout adjusted to 180 seconds to accommodate shorter pause duration
- **Status**: Anti-spam batch processing with 2m15s pauses fully implemented and operational

### 2025-07-12: Added Website Column to Results Table (COMPLETED)
- **Update**: Added Website column to the right of Email column in the results table for better lead information display
- **Changes Made**:
  - **New Website Column**: Added Website column positioned between Email and Product columns
  - **Clickable Website Links**: Website URLs display as clickable links that open in new tab with green branding
  - **Inline Editing Support**: Website field supports click-to-edit functionality for manual entry/updates
  - **Filter Integration**: Added website filter input in filter row for searching by website domain
  - **Table Structure Updates**:
    - Updated table headers to include Website column with sorting capability
    - Adjusted column indices in JavaScript for proper filtering and sorting
    - Updated cell references to account for new column position
  - **Data Display Enhancement**:
    - Shows website as clickable link when available
    - Shows "Click to add" placeholder for missing website data
    - Maintains consistent styling with other editable fields
  - **Backend Integration**: Website field already exists in Lead model and update endpoints
- **Benefits**:
  - Quick access to influencer websites for research and verification
  - Better lead qualification with website information visible at a glance
  - Streamlined workflow for lead outreach with direct website access
  - Enhanced data completeness tracking and manual entry capabilities
- **Status**: Website column fully integrated with complete editing and filtering functionality

### 2025-07-12: Sticky Username Column and Header Row Freeze (COMPLETED)
- **Update**: Implemented frozen Username column and header rows for improved table navigation during scrolling
- **Changes Made**:
  - **Sticky Username Column**: Username column (2nd column) now remains fixed when horizontally scrolling through table data
  - **Frozen Header Row**: Main header row with column names stays visible when vertically scrolling through results
  - **Frozen Filter Row**: Filter input row also remains sticky below the main header for continuous filtering access
  - **Enhanced Table Navigation**: 
    - Username column has `position: sticky; left: 0` with proper z-index layering
    - Header rows use `position: sticky; top: 0` and filter row at `top: 48px`
    - Background colors and borders maintained for visual consistency
  - **Visual Improvements**:
    - Added border-right to sticky column for clear separation
    - Preserved alternating row colors and hover effects for sticky column
    - Proper z-index stacking ensures headers appear above content
  - **Scrolling Enhancement**:
    - Table container set to `max-height: calc(100vh - 200px)` for vertical scrolling
    - Table wrapper supports both horizontal and vertical overflow
    - Users can scroll through long lists while keeping reference points visible
- **Benefits**:
  - Username always visible for reference when reviewing leads horizontally
  - Column headers remain accessible for sorting during vertical scrolling
  - Filter inputs stay available without scrolling back to top
  - Improved usability for large datasets with many columns
  - Google Sheets-like navigation experience maintained
- **Status**: Sticky column and header freeze functionality fully implemented and operational

### 2025-07-12: Automatic Sheet Updates with Incremental Lead Notifications (COMPLETED)
- **Update**: Implemented real-time sheet updates during lead generation with incremental progress notifications
- **Changes Made**:
  - **Enhanced Progress Tracking**: Added `incremental_leads`, `keyword`, and `final_status` to progress tracking system
  - **Real-time Table Updates**: Created `/api/leads` endpoint for fetching leads by keyword during processing
  - **Incremental Notifications**: Modified progress updates to show current lead count as batches complete
  - **Partial Results Handling**: Added support for displaying partial results when lead generation fails midway
  - **Frontend Auto-refresh**: Implemented `refreshLeadsTable()` function for automatic table updates during processing
  - **Enhanced Error Handling**: Process failures now return partial results with 206 status code
  - **Visual Progress Feedback**: Progress text shows real-time lead counts during batch processing
  - **Success Notifications**: Final completion shows total generated leads count
- **Features**:
  - Sheet automatically updates as each batch of leads is processed and saved
  - Real-time notifications show "X leads generated for keyword" during processing
  - Failed processes still show any successfully generated leads with warning notification
  - Users see incremental progress without waiting for full completion
  - Table refreshes automatically with new leads as they become available
  - Partial success scenarios handled gracefully with appropriate user feedback
- **Benefits**:
  - Better user experience with real-time feedback during long processing runs
  - No data loss visibility - users see progress even if process crashes
  - Immediate access to generated leads without waiting for full completion
  - Clear distinction between partial success and complete failure
  - Enhanced confidence in system reliability with incremental updates
- **Status**: Automatic sheet updates with incremental notifications fully implemented and operational

### 2025-07-11: Product Selection System with Alternative Prompts (COMPLETED)
- **Update**: Implemented complete product selection functionality with smart OpenAI email generation that uses different prompts based on product selection
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
  - **Smart Email Generation System**: 
    - **WITH Product**: Uses original prompts with specific product integration instructions
    - **WITHOUT Product**: Uses alternative prompts that focus on general cooperation without product mentions
    - Updated system prompts to ensure natural product integration when selected
    - Added clean alternative prompts that explicitly avoid specific product references
  - **Alternative Prompt Logic**: 
    - Dynamic prompt selection based on `lead.selected_product` status
    - Clean alternative prompts remove all product-specific instructions
    - Maintains professional German tone and KasimirLieselotte branding in both scenarios
  - **Frontend Integration**: 
    - Products data passed from backend to frontend on page load
    - JavaScript functions for product selection and management
    - Visual indicators for products with "Kein Produkt" (No Product) for unassigned leads
  - **Product Images**: Stored product images in static folder for future integration
- **Features**:
  - Smart prompt selection: product-specific vs. general cooperation emails
  - Per-lead product assignment through click-to-edit interface
  - Default product selection for new email generations
  - Product information automatically included in OpenAI prompts when selected
  - Clean, general cooperation emails when no product is assigned
  - Seamless product switching without page reload
- **Benefits**:
  - Personalized product recommendations when product is selected
  - Professional general outreach emails when no specific product is chosen
  - Easy product management through intuitive UI
  - Consistent branding and tone across all email types
  - Enhanced email relevance with context-appropriate content
- **Status**: Product selection system with alternative prompts fully implemented and tested

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

Preferred communication style: Simple, everyday language.  Before implementing any code changes, always lay out what code changes will be implemented and then let the user decide to approve, change, or deny the code changes. The user is happy to receive recommendations on how to improve the code. The user is happy to receive recommendations on how to improve the code.

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