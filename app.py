from flask import Flask
from flask_cors import CORS
import atexit
import os
from datetime import datetime

# Import all components
from config import Config
from services.claude_service import ClaudeService
from services.twilio_service import TwilioService
from services.email_service import EmailService
from services.reminder_service import ReminderService
from handlers.action_handlers import ActionHandlers
from routes.web_routes import web_bp
from routes.pwa_routes import pwa_bp
from routes.api_routes import api_bp, init_api_routes

def create_app():
    """Application factory"""
    app = Flask(__name__)
    CORS(app)
    
    # Initialize services
    claude_service = ClaudeService(Config.CLAUDE_API_KEY)
    twilio_service = TwilioService(
        Config.TWILIO_ACCOUNT_SID,
        Config.TWILIO_AUTH_TOKEN,
        Config.TWILIO_PHONE_NUMBER
    )
    email_service = EmailService(
        Config.SMTP_SERVER,
        Config.SMTP_PORT,
        Config.EMAIL_ADDRESS,
        Config.EMAIL_PASSWORD,
        Config.EMAIL_NAME,
        Config.EMAIL_PROVIDER
    )
    reminder_service = ReminderService(twilio_service, email_service)
    action_handlers = ActionHandlers(twilio_service, email_service, claude_service, reminder_service)
    
    # Register blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(pwa_bp)
    
    # Initialize and register API routes with dependencies
    api_blueprint = init_api_routes(action_handlers, reminder_service, twilio_service, email_service, claude_service)
    app.register_blueprint(api_blueprint)
    
    # Cleanup on app shutdown
    def cleanup_scheduler():
        """Cleanup scheduler on shutdown"""
        reminder_service.shutdown()
    
    atexit.register(cleanup_scheduler)
    
    return app, reminder_service, twilio_service, email_service, claude_service

def print_startup_info(reminder_service, twilio_service, email_service, claude_service):
    """Print startup information"""
    print("🚀 Starting Enhanced Smart AI Agent Flask App with SMS, Email & Reminder Support")
    print(f"📱 Twilio Status: {'✅ Connected' if twilio_service.client else '❌ Not configured'}")
    print(f"📧 Email Status: {'✅ Configured' if email_service.email_address and email_service.email_password else '❌ Not configured'}")
    print(f"🤖 Claude Status: {'✅ Configured' if claude_service.api_key else '❌ Not configured'}")
    print(f"⏰ Scheduler Status: {'✅ Running' if reminder_service.scheduler.running else '❌ Not running'}")
    print(f"🌍 Timezone: {Config.TIMEZONE}")
    print("✨ Features: Multi-Recipient SMS, Multi-Recipient Email, Mixed Messaging, Professional Voice Processing, Message Enhancement, Auto-Subject Generation, Smart Reminders")
    print("🔧 Execution order: Reminders → Email → Multi-Email → SMS → Multi-SMS → Mixed → Claude fallback")
    
    print("\n📋 Voice Command Examples:")
    print("  📱 SMS Commands:")
    print("    • 'Text 8136414177 saying hey how are you'")
    print("    • 'Send a message to John saying the meeting moved'")
    print("    • 'Text John and Mary saying the meeting moved to 3pm'")
    print("  📧 Email Commands:")
    print("    • 'Email john@example.com saying the meeting is at 3pm'")
    print("    • 'Email john@example.com with subject meeting update saying the time changed'")
    print("    • 'Email john@example.com and mary@example.com saying hello everyone'")
    print("  ⏰ Reminder Commands:")
    print("    • 'Remind me to call John in 30 minutes'")
    print("    • 'Set a reminder to pick up groceries at 5pm'")
    print("    • 'Text me in 1 hour to check on the project'")
    print("    • 'Remind me tomorrow at 9am to submit the report'")
    print("    • 'Schedule a reminder to call mom on Friday at 2pm'")
    print("  🔄 Mixed Commands:")
    print("    • 'Send a message to 8136414177 and john@example.com saying hello'")
    print("    • 'Message Mom and dad@example.com that I'll be home late'")
    
    print("\n🔧 Environment Variables Required:")
    print("  CLAUDE_API_KEY=your_claude_api_key")
    print("  TWILIO_ACCOUNT_SID=your_twilio_account_sid")
    print("  TWILIO_AUTH_TOKEN=your_twilio_auth_token")
    print("  TWILIO_PHONE_NUMBER=your_twilio_phone_number")
    print("  EMAIL_ADDRESS=your_email@yourdomain.com")
    print("  EMAIL_PASSWORD=your_email_password")
    print("  EMAIL_PROVIDER=networksolutions (optional)")
    print("  SMTP_SERVER=mail.networksolutions.com (optional)")
    print("  SMTP_PORT=587 (optional)")
    print("  EMAIL_NAME=Your Name (optional)")
    print("  TIMEZONE=America/New_York (optional)")
    
    print("\n⏰ Reminder Features:")
    print("  - Natural language parsing (in 30 minutes, at 5pm, tomorrow at 9am)")
    print("  - Persistent scheduling with SQLite storage")
    print("  - Automatic message enhancement before sending")
    print("  - Timezone-aware scheduling")
    print("  - Voice command support for hands-free scheduling")
    print("  - RESTful API endpoints for programmatic access")
    
    print("\n🔧 Dependencies Required:")
    print("  pip install -r requirements.txt")
    
    print("\n📧 Network Solutions Email Setup:")
    print("  - Use your full email address (user@yourdomain.com) as EMAIL_ADDRESS")
    print("  - Use your email account password (not cPanel password)")
    print("  - Ensure email hosting is active on your Network Solutions plan")
    print("  - Default SMTP: mail.networksolutions.com:587")
    print("  - Alternative: mail.yourdomain.com:587 (replace yourdomain.com)")
    print("  - Test connection with: curl http://localhost:10000/email_info")
    
    print("\n🧪 Testing Endpoints:")
    print("  - GET  /health - Health check with scheduler status")
    print("  - POST /test_sms - Test SMS sending")
    print("  - POST /test_email - Test email sending")
    print("  - GET  /list_reminders - List all scheduled reminders")
    print("  - POST /cancel_reminder - Cancel a reminder")

if __name__ == '__main__':
    app, reminder_service, twilio_service, email_service, claude_service = create_app()
    
    print_startup_info(reminder_service, twilio_service, email_service, claude_service)
    
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
