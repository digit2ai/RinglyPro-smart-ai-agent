import re
from typing import Dict, Any, Optional
from utils.formatters import parse_recipients, clean_voice_message
from utils.datetime_parser import parse_natural_datetime

class MessageParser:
    """Parse voice commands into structured actions"""
    
    @staticmethod
    def _has_timing_keywords(text: str) -> bool:
        """Check if text contains timing keywords that indicate a reminder"""
        timing_keywords = [
            'in ', 'at ', 'tomorrow', 'next ', 'on ', 'this ', 'tonight',
            'later', 'soon', 'minute', 'hour', 'day', 'week', 'month',
            'morning', 'afternoon', 'evening', 'night', 'am', 'pm',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in timing_keywords)
    
    @staticmethod
    def extract_reminder_command(text: str) -> Optional[Dict[str, Any]]:
        """Extract reminder command from voice input"""
        patterns = [
            # "Remind me" patterns
            r'remind me to (.+?) in (.+)',
            r'remind me to (.+?) at (.+)',
            r'remind me to (.+?) tomorrow',
            r'remind me to (.+?) next (.+)',
            r'remind me to (.+?) on (.+)',
            r'remind me in (.+?) to (.+)',
            r'remind me at (.+?) to (.+)',
            r'remind me tomorrow to (.+)',
            r'remind me next (.+?) to (.+)',
            
            # "Text me" / "SMS me" patterns
            r'text me in (.+?) to (.+)',
            r'text me in (.+?) saying (.+)',
            r'text me at (.+?) to (.+)',
            r'text me at (.+?) saying (.+)',
            r'text me tomorrow to (.+)',
            r'text me tomorrow saying (.+)',
            r'text me next (.+?) to (.+)',
            r'text me next (.+?) saying (.+)',
            
            # "Text [number] in/at" patterns  
            r'text (.+?) in (.+?) saying (.+)',
            r'text (.+?) in (.+?) to (.+)',
            r'text (.+?) at (.+?) saying (.+)',
            r'text (.+?) at (.+?) to (.+)',
            r'text (.+?) tomorrow saying (.+)',
            r'text (.+?) tomorrow to (.+)',
            r'text (.+?) next (.+?) saying (.+)',
            r'text (.+?) next (.+?) to (.+)',
            
            # General reminder patterns
            r'set (?:a )?reminder to (.+?) at (.+)',
            r'set (?:a )?reminder to (.+?) in (.+)',
            r'set (?:a )?reminder to (.+?) tomorrow',
            r'set (?:a )?reminder to (.+?) next (.+)',
            r'schedule (?:a )?reminder to (.+?) at (.+)',
            r'schedule (?:a )?reminder to (.+?) in (.+)',
            r'send me (?:a )?reminder to (.+?) in (.+)',
            r'sms reminder in (.+?) saying (.+)',
        ]
        
        text_lower = text.lower().strip()
        print(f"[DEBUG] Trying to extract reminder from: '{text_lower}'")
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                groups = match.groups()
                print(f"[DEBUG] Pattern {i} matched: '{pattern}' -> groups: {groups}")
                
                # Handle different pattern structures
                if len(groups) == 3:  # 3-group patterns like "text [recipient] in [time] saying [message]"
                    recipient = groups[0].strip()
                    time_str = groups[1].strip()
                    message = groups[2].strip()
                elif len(groups) == 2:
                    # Determine order based on pattern keywords
                    if "remind me to (.+?) in (.+)" in pattern:
                        # Pattern: "remind me to [message] in [time]"
                        message = groups[0].strip()
                        time_str = groups[1].strip()
                        recipient = "me"
                        print(f"[DEBUG] Using 'remind me to X in Y' logic: message='{message}', time='{time_str}'")
                    elif "remind me in (.+?) to (.+)" in pattern:
                        # Pattern: "remind me in [time] to [message]"
                        time_str = groups[0].strip()
                        message = groups[1].strip()
                        recipient = "me"
                        print(f"[DEBUG] Using 'remind me in X to Y' logic: time='{time_str}', message='{message}'")
                    elif "to (.+?) at (.+)" in pattern:
                        # Pattern: "set reminder to [message] at [time]"
                        message = groups[0].strip()
                        time_str = groups[1].strip()
                        recipient = "me"
                    elif "to (.+?) in (.+)" in pattern:
                        # Pattern: "set reminder to [message] in [time]"
                        message = groups[0].strip()
                        time_str = groups[1].strip()
                        recipient = "me"
                    elif "saying" in pattern:
                        time_str = groups[0].strip()
                        message = groups[1].strip()
                        recipient = "me"
                    else:
                        message = groups[0].strip()
                        time_str = groups[1].strip()
                        recipient = "me"
                else:
                    continue  # Skip patterns we can't parse
                
                print(f"[DEBUG] Final parsing: recipient='{recipient}', message='{message}', time_str='{time_str}'")
                
                reminder_time = parse_natural_datetime(time_str)
                
                if reminder_time:
                    message = clean_voice_message(message)
                    
                    return {
                        "action": "schedule_sms_reminder",
                        "recipient": recipient,
                        "message": message,
                        "reminder_time": reminder_time.isoformat(),
                        "time_str": time_str,
                        "original_text": text
                    }
                else:
                    print(f"[DEBUG] Failed to parse datetime from: '{time_str}'")
        
        print(f"[DEBUG] No reminder patterns matched for: '{text_lower}'")
        return None
    
    @staticmethod
    def extract_sms_command(text: str) -> Optional[Dict[str, Any]]:
        """Extract SMS command from voice input (IMMEDIATE only, no timing)"""
        text_lower = text.lower().strip()
        
        # CRITICAL: Skip if this looks like ANY kind of reminder command
        reminder_indicators = [
            'remind me', 'text me in', 'text me at', 'set a reminder', 
            'schedule a reminder', 'in minutes', 'in hours', 'at pm', 'at am',
            'tomorrow', 'next week', 'next month', 'later today'
        ]
        
        for indicator in reminder_indicators:
            if indicator in text_lower:
                return None
        
        # Also skip if pattern contains "in X" or "at X" timing
        if re.search(r'\b(?:in|at)\s+\d+\s*(?:minutes?|hours?|seconds?|days?)\b', text_lower):
            return None
            
        if re.search(r'\b(?:in|at)\s+\d{1,2}:?\d{0,2}\s*(?:am|pm)?\b', text_lower):
            return None
        
        patterns = [
            r'send (?:a )?(?:text|message|sms) to (.+?) saying (.+)',
            r'message (.+?) saying (.+)',
            r'send (.+?) the message (.+)',
            r'tell (.+?) that (.+)',
        ]
        
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
        # Skip if this looks like a reminder command
        if MessageParser._has_timing_keywords(text):
            return None
            
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
                
                # Double-check: if recipients contains timing words, skip this
                if MessageParser._has_timing_keywords(recipients_text):
                    continue
                    
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
