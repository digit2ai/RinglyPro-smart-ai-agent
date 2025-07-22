# Smart AI Agent

AI-powered voice assistant with SMS, Email, and Reminder capabilities.

## Features

- 🎤 Voice command processing
- 📱 SMS messaging via Twilio
- 📧 Email sending with auto-enhancement
- ⏰ Smart reminders with natural language
- 🔄 Multi-recipient messaging
- 🎯 Professional message enhancement with Claude AI

## Quick Setup

### 1. GitHub Setup
1. Clone this repository
2. Copy `.env.template` to `.env` and add your API keys

### 2. Local Development
```bash
pip install -r requirements.txt
python app.py
```

### 3. Deploy to Render
1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy automatically

## Environment Variables

### Required
- `CLAUDE_API_KEY` - Get from Anthropic
- `EMAIL_ADDRESS` - Your email address
- `EMAIL_PASSWORD` - Your email password

### Optional (for SMS)
- `TWILIO_ACCOUNT_SID` - From Twilio dashboard
- `TWILIO_AUTH_TOKEN` - From Twilio dashboard
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number

## Usage Examples

- "Text John saying hello"
- "Email john@example.com saying the meeting is at 3pm"
- "Remind me to call mom in 30 minutes"
- "Send a message to John and Mary saying the meeting moved"

## API Endpoints

- `GET /health` - Health check
- `POST /execute` - Main command execution
- `POST /test_sms` - Test SMS functionality
- `POST /test_email` - Test email functionality
- `GET /list_reminders` - List scheduled reminders

## Architecture

- `config.py` - Configuration management
- `app.py` - Main application
- `services/` - Business logic services
- `handlers/` - Action handlers
- `utils/` - Utility functions
- `routes/` - API and web routes

## License

MIT License