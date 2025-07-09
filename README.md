# Instagram LeadGen - Full-Stack Application

An elegant Instagram lead generation and outreach automation tool built with Flask and inspired by Kasimir Lieselotte's minimalist design aesthetic.

## Features

- **Hashtag Crawling**: Automated Instagram hashtag analysis using Apify
- **Profile Enrichment**: Concurrent profile data collection with contact information
- **AI-Powered Email Generation**: OpenAI GPT-4o integration for personalized outreach
- **Gmail Integration**: Direct email sending through Gmail API
- **Elegant Design**: Serif typography with Cormorant Garamond font
- **Data Export**: CSV and JSON export capabilities
- **Duplicate Detection**: Orange highlighting for duplicate profiles
- **Responsive Interface**: Mobile-friendly Bootstrap 5 design

## Tech Stack

- **Backend**: Flask, asyncio, httpx
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **APIs**: Apify, Perplexity, OpenAI, Gmail
- **Design**: Custom CSS with Kasimir Lieselotte inspiration

## Setup Instructions

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd instagram-leadgen
   ```

2. **Install dependencies**
   ```bash
   pip install flask httpx[async] asyncio python-dotenv google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client openai pytest black isort flake8
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the application**
   Open http://localhost:5000 in your browser

### Replit Deployment

1. **Import to Replit**
   - Create a new Replit project
   - Import this repository

2. **Configure Secrets**
   Go to Secrets tab and add:
   - `SESSION_SECRET`: Random secret key for Flask sessions
   - `APIFY_TOKEN`: Your Apify API token
   - `PERPLEXITY_API_KEY`: Your Perplexity API key
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `GMAIL_CLIENT_ID`: Gmail OAuth client ID
   - `GMAIL_CLIENT_SECRET`: Gmail OAuth client secret
   - `GMAIL_REFRESH_TOKEN`: Gmail OAuth refresh token
   - `IG_SESSIONID`: (Optional) Instagram session ID

3. **Run the application**
   Click the "Run" button in Replit

## API Credentials Setup

### Apify API
1. Sign up at [apify.com](https://apify.com)
2. Get your API token from Settings > Integrations
3. Required actors:
   - `DrF9mzPPEuVizVF4l` (Hashtag crawler)
   - `8WEn9FvZnhE7lM3oA` (Profile enrichment)

### Perplexity API
1. Sign up at [perplexity.ai](https://perplexity.ai)
2. Get your API key from the dashboard
3. Uses `llama-3.1-sonar-small-128k-online` model

### OpenAI API
1. Sign up at [openai.com](https://openai.com)
2. Get your API key from the dashboard
3. Uses `gpt-4o` model for email generation

### Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Generate refresh token using OAuth playground

### Instagram Session ID
1. Log into Instagram in your browser
2. Open Developer Tools (F12)
3. Go to Application/Storage > Cookies > instagram.com
4. Copy the value of `sessionid`

## Usage

1. **Session Setup**: Enter your Instagram Session ID when prompted
2. **Keyword Processing**: Enter a hashtag keyword and click "Run"
3. **Review Results**: Browse generated leads in the results table
4. **Email Configuration**: Customize email prompts in the settings panel
5. **Draft Emails**: Use AI to generate personalized email content
6. **Send Emails**: Send emails directly through Gmail integration
7. **Export Data**: Download results as CSV or JSON

## Features Detailed

### Concurrency Limits
- Apify API calls: Limited to 10 concurrent requests
- Perplexity API calls: Limited to 5 concurrent requests
- Async processing with proper error handling

### Data Processing
- Automatic deduplication based on hashtag|username key
- Orange highlighting for duplicate entries
- Sortable table with click-to-sort functionality

### Email Generation
- Customizable prompts for subject and body generation
- OpenAI GPT-4o integration with JSON response format
- Personalized content based on profile data

### Error Handling
- Comprehensive logging with error details
- User-friendly toast notifications
- Graceful fallbacks for API failures

## Development

### Code Formatting
```bash
black main.py
isort main.py
flake8 main.py
