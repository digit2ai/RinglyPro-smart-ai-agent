import re
from typing import List

def is_phone_number(recipient: str) -> bool:
    """Check if recipient looks like a phone number"""
    clean = recipient.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    if clean.startswith("+") and clean[1:].isdigit():
        return True
    if clean.isdigit() and len(clean) >= 10:
        return True
    
    return False

def is_email_address(recipient: str) -> bool:
    """Check if recipient looks like an email address"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, recipient.strip()))

def format_phone_number(phone: str) -> str:
    """Format phone number to E.164 format"""
    clean = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    if not clean.startswith('+'):
        if len(clean) == 10:
            clean = '+1' + clean
        elif len(clean) == 11 and clean.startswith('1'):
            clean = '+' + clean
    
    return clean

def parse_recipients(recipients_text: str) -> List[str]:
    """Parse multiple recipients from text"""
    recipients_text = recipients_text.strip()
    
    # Replace common conjunctions with commas
    recipients_text = re.sub(r'\s+and\s+', ', ', recipients_text)
    recipients_text = re.sub(r'\s+&\s+', ', ', recipients_text)
    recipients_text = re.sub(r'\s*,\s*and\s+', ', ', recipients_text)
    
    recipients = [r.strip() for r in recipients_text.split(',')]
    return [r for r in recipients if r]

def clean_voice_message(message: str) -> str:
    """Clean up voice recognition artifacts"""
    message = message.replace(" period", ".").replace(" comma", ",")
    message = message.replace(" question mark", "?").replace(" exclamation mark", "!")
    return message.strip()