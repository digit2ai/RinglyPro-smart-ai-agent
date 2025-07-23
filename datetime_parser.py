import re
from datetime import datetime, timedelta
from typing import Optional
import pytz
from dateutil import parser as date_parser
from config import Config

def parse_natural_datetime(text: str) -> Optional[datetime]:
    """Parse natural language datetime expressions"""
    
    # Get current time in the configured timezone
    now = datetime.now(Config.SCHEDULER_TIMEZONE)
    text = text.lower().strip()
    
    print(f"[DEBUG DATETIME] Current time: {now}")
    print(f"[DEBUG DATETIME] Parsing: '{text}'")
    
    # Helper function to ensure timezone consistency
    def make_timezone_aware(dt):
        """Ensure datetime has timezone info"""
        if dt.tzinfo is None:
            return Config.SCHEDULER_TIMEZONE.localize(dt)
        return dt
    
    # Patterns for relative times
    relative_patterns = [
        (r'in (\d+) minutes?', lambda m: now + timedelta(minutes=int(m.group(1)))),
        (r'in (\d+) hours?', lambda m: now + timedelta(hours=int(m.group(1)))),
        (r'in (\d+) days?', lambda m: now + timedelta(days=int(m.group(1)))),
        (r'in (\d+) weeks?', lambda m: now + timedelta(weeks=int(m.group(1)))),
        
        # Handle fractional times
        (r'in (\d+\.?\d*) minutes?', lambda m: now + timedelta(minutes=float(m.group(1)))),
        (r'in (\d+\.?\d*) hours?', lambda m: now + timedelta(hours=float(m.group(1)))),
        
        # "X from now" patterns
        (r'(\d+) minutes? from now', lambda m: now + timedelta(minutes=int(m.group(1)))),
        (r'(\d+) hours? from now', lambda m: now + timedelta(hours=int(m.group(1)))),
        (r'(\d+) days? from now', lambda m: now + timedelta(days=int(m.group(1)))),
        
        # Common shortcuts
        (r'in (?:a |an )?hour', lambda m: now + timedelta(hours=1)),
        (r'in (?:a )?minute', lambda m: now + timedelta(minutes=1)),
        (r'in half (?:an )?hour', lambda m: now + timedelta(minutes=30)),
        (r'in (?:a )?second', lambda m: now + timedelta(seconds=1)),
        
        # Specific time patterns
        (r'tomorrow at (\d{1,2}):?(\d{0,2})\s*(am|pm)?', lambda m: 
         make_timezone_aware((now + timedelta(days=1)).replace(
             hour=_parse_hour(m.group(1), m.group(3)),
             minute=int(m.group(2)) if m.group(2) else 0,
             second=0, microsecond=0, tzinfo=None
         ))),
        
        (r'today at (\d{1,2}):?(\d{0,2})\s*(am|pm)?', lambda m: 
         make_timezone_aware(now.replace(
             hour=_parse_hour(m.group(1), m.group(3)),
             minute=int(m.group(2)) if m.group(2) else 0,
             second=0, microsecond=0, tzinfo=None
         ))),
         
        (r'at (\d{1,2}):?(\d{0,2})\s*(am|pm)?', lambda m: 
         make_timezone_aware(now.replace(
             hour=_parse_hour(m.group(1), m.group(3)),
             minute=int(m.group(2)) if m.group(2) else 0,
             second=0, microsecond=0, tzinfo=None
         ))),
         
        # 24-hour format
        (r'at (\d{1,2}):(\d{2})', lambda m: 
         make_timezone_aware(now.replace(
             hour=int(m.group(1)),
             minute=int(m.group(2)),
             second=0, microsecond=0, tzinfo=None
         ))),
         
        # Just hour (assumes PM for business hours, AM for early hours)
        (r'at (\d{1,2})pm', lambda m: 
         make_timezone_aware(now.replace(
             hour=int(m.group(1)) if int(m.group(1)) == 12 else int(m.group(1)) + 12,
             minute=0, second=0, microsecond=0, tzinfo=None
         ))),
         
        (r'at (\d{1,2})am', lambda m: 
         make_timezone_aware(now.replace(
             hour=int(m.group(1)) % 12,
             minute=0, second=0, microsecond=0, tzinfo=None
         ))),
    ]
    
    # Try relative patterns first
    for pattern, calculator in relative_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                result = calculator(match)
                print(f"[DEBUG DATETIME] Pattern '{pattern}' matched")
                print(f"[DEBUG DATETIME] Calculated result: {result}")
                
                # Ensure result is timezone-aware and in the future
                if result.tzinfo is None:
                    result = Config.SCHEDULER_TIMEZONE.localize(result)
                
                # Validate that result is in the future
                if result <= now:
                    print(f"[DEBUG DATETIME] Result {result} is not in future (now: {now})")
                    # For "today" patterns, try tomorrow instead
                    if "today" in text:
                        result += timedelta(days=1)
                        print(f"[DEBUG DATETIME] Adjusted to tomorrow: {result}")
                    else:
                        print(f"[DEBUG DATETIME] Warning: Scheduled time is in the past!")
                
                print(f"[DEBUG DATETIME] Final result: {result}")
                return result
            except Exception as e:
                print(f"[DEBUG DATETIME] Error calculating relative time: {e}")
                continue
    
    # Try parsing with dateutil
    try:
        parsed = date_parser.parse(text, fuzzy=True)
        if parsed.tzinfo is None:
            parsed = Config.SCHEDULER_TIMEZONE.localize(parsed)
        
        # If parsed time is in the past, assume they mean tomorrow
        if parsed <= now:
            parsed += timedelta(days=1)
            
        return parsed
    except Exception as e:
        print(f"Error parsing datetime with dateutil: {e}")
        
    return None

def _parse_hour(hour_str: str, ampm: Optional[str]) -> int:
    """Parse hour with AM/PM handling"""
    hour = int(hour_str)
    
    if ampm:
        if ampm.lower() == 'pm' and hour != 12:
            hour += 12
        elif ampm.lower() == 'am' and hour == 12:
            hour = 0
    else:
        # No AM/PM specified - use smart defaults
        if hour <= 7:  # 1-7 assume PM (afternoon/evening)
            hour += 12
        elif hour >= 8 and hour <= 11:  # 8-11 could be AM or PM - use context
            current_hour = datetime.now().hour
            if current_hour >= 12:  # It's afternoon, assume PM
                hour += 12
    
    return hour
