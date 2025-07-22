import re
from typing import Dict, Any, Optional
from utils.formatters import parse_recipients, clean_voice_message
from utils.datetime_parser import parse_natural_datetime

class MessageParser:
    """Parse voice commands into structured actions"""
    
    @staticmethod
    def extract_reminder_command(text: str) -> Optional[Dict[str, Any]]:
        """Extract reminder command from voice input"""
        patterns = [
            r'remind me to (.+?) in (.+)',
            r'set (?:a )?reminder to (.+?) at (.+)',
            r'remind me in (.+?) to (.+)',
            r'schedule (?:a )?reminder to (.+?) (.+)',
            r'send me (?:a )?reminder to (.+?) in (.+)',
            r'text me in (.+?) to (.+)',
            r'sms reminder in (.+?) saying (.+)',
        ]
        
        text_lower = text.lower().strip()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Determine message and time based on pattern
                if "in" in pattern and pattern.index("in") < pattern.index("to"):
                    time_str = groups[0].strip()
                    message = groups[1].strip()
                elif "at" in pattern:
                    message = groups[0].strip()
                    time_str = groups[1].strip()
                elif "saying" in pattern:
                    time_str = groups[0].strip()
                    message = groups[1].strip()
                else:
                    message = groups[0].strip()
                    time_str = groups[1].strip()
                
                reminder_time = parse_natural_datetime(time_str)
                
                if reminder_time:
                    message = clean_voice_message(message)
                    
                    return {
                        "action": "schedule_sms_reminder",
                        "message": message,
                        "reminder_time": reminder_time.isoformat(),
                        "time_str": time_str,
                        "original_text": text
                    }
        
        return None
    
    @staticmethod
    def extract_sms_command(text: str) -> Optional[Dict[str, Any]]:
        """Extract SMS command from voice input"""
        patterns = [
            r'send (?:a )?(?:text|message|sms) to (.+?) saying (.+)',
            r'text (.+?) saying (.+)',
            r'message (.+?) saying (.+)',
            r'send (.+?) the message (.+)',
            r'tell (.+?) that (.+)',
            r'text (.+?) (.+)',
        ]
        
        text_lower = text.lower().strip()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                recipient = match.group(1).strip()
                message = match.group(2).strip()
                message = clean_voice_message(message)
                
                return {
                    "action": "send_message",
                    "recipient": recipient,
                    "message": message,
                    "original_message": message
                }
        
        return None
    
    @staticmethod
    def extract_sms_command_multi(text: str) -> Optional[Dict[str, Any]]:
        """Extract multi-recipient SMS command"""
        multi_patterns = [
            r'send (?:a )?(?:text|message|sms) to (.+?) saying (.+)',
            r'text (.+?) saying (.+)',
            r'message (.+?) (?:that|saying) (.+)',
            r'tell (.+?) that (.+)',
        ]
        
        text_lower = text.lower().strip()
        
        for pattern in multi_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                recipients_text = match.group(1).strip()
                message = match.group(2).strip()
                recipients = parse_recipients(recipients_text)
                message = clean_voice_message(message)
                
                if len(recipients) > 1:
                    return {
                        "action": "send_message_multi",
                        "recipients": recipients,
                        "message": message,
                        "original_message": message
                    }
                else:
                    return {
                        "action": "send_message",
                        "recipient": recipients[0] if recipients else recipients_text,
                        "message": message,
                        "original_message": message
                    }
        
        return None
    
    @staticmethod
    def extract_email_command(text: str) -> Optional[Dict[str, Any]]:
        """Extract email command from voice input"""
        patterns = [
            r'send (?:an )?email to (.+?) (?:with subject (.+?) )?saying (.+)',
            r'email (.+?) (?:with subject (.+?) )?saying (.+)',
            r'send (.+?) (?:an )?email (?:with subject (.+?) )?saying (.+)',
            r'email (.+?) that (.+)',
            r'send (?:an )?email to (.+?) (.+)',
        ]
        
        text_lower = text.lower().strip()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) == 3 and groups[1]:  # Has subject
                    recipient = groups[0].strip()
                    subject = groups[1].strip()
                    message = groups[2].strip()
                elif len(groups) == 3:  # No subject in middle
                    recipient = groups[0].strip()
                    subject = None
                    message = groups[2].strip()
                else:  # Simple pattern
                    recipient = groups[0].strip()
                    subject = None
                    message = groups[1].strip()
                
                message = clean_voice_message(message)
                if subject:
                    subject = clean_voice_message(subject)
                
                return {
                    "action": "send_email",
                    "recipient": recipient,
                    "subject": subject,
                    "message": message,
                    "original_message": message
                }
        
        return None
    
    @staticmethod
    def extract_email_command_multi(text: str) -> Optional[Dict[str, Any]]:
        """Extract multi-recipient email command"""
        multi_patterns = [
            r'send (?:an )?email to (.+?) (?:with subject (.+?) )?saying (.+)',
            r'email (.+?) saying (.+)',
            r'send (.+?) (?:an )?email saying (.+)',
        ]
        
        text_lower = text.lower().strip()
        
        for pattern in multi_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) == 3 and groups[1]:  # Has subject
                    recipients_text = groups[0].strip()
                    subject = groups[1].strip()
                    message = groups[2].strip()
                else:  # No subject
                    recipients_text = groups[0].strip()
                    subject = None
                    message = groups[-1].strip()
                
                recipients = parse_recipients(recipients_text)
                message = clean_voice_message(message)
                if subject:
                    subject = clean_voice_message(subject)
                
                if len(recipients) > 1:
                    return {
                        "action": "send_email_multi",
                        "recipients": recipients,
                        "subject": subject,
                        "message": message,
                        "original_message": message
                    }
                else:
                    return {
                        "action": "send_email",
                        "recipient": recipients[0] if recipients else recipients_text,
                        "subject": subject,
                        "message": message,
                        "original_message": message
                    }
        
        return None