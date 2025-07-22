import os
import pytz

class Config:
    """Application configuration"""
    
    # Claude AI
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    
    # Twilio SMS
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Email Configuration (Network Solutions defaults)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "mail.networksolutions.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_NAME = os.getenv("EMAIL_NAME", "Smart AI Agent")
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "networksolutions").lower()
    
    # Application Settings
    TIMEZONE = os.getenv("TIMEZONE", "America/New_York")
    PORT = int(os.getenv("PORT", 10000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Scheduler Configuration
    SCHEDULER_JOBSTORE_URL = "sqlite:///jobs.sqlite"
    SCHEDULER_TIMEZONE = pytz.timezone(TIMEZONE)