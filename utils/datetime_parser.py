import re
from datetime import datetime, timedelta
from typing import Optional
import pytz
from dateutil import parser as date_parser
from config import Config

def parse_natural_datetime(text: str) -> Optional[datetime]:
    """Parse natural language datetime expressions"""
    
    print("🔥🔥🔥 DATETIME PARSER CALLED WITH:", text)
    print("🔥🔥🔥 FILE: utils/datetime_parser.py")
    
    # Get current time in the configured timezone
    now = datetime.now(Config.SCHEDULER_TIMEZONE)
    text = text.lower().strip()
    
    print(f"[DEBUG DATETIME] Current time: {now}")
    print(f"[DEBUG DATETIME] Parsing: '{text}'")
    
    # Simple relative time patterns with direct calculation
    # Handle "in X minutes" specifically
    if re.search(r'in (\d+) minutes?', text):
        match = re.search(r'in (\d+) minutes?', text)
        minutes = int(match.group(1))
        result = now + timedelta(minutes=minutes)
        print(f"[DEBUG DATETIME] 'in {minutes} minutes' -> {result}")
        return result
    
    # Handle "in X hours"
    if re.search(r'in (\d+) hours?', text):
        match = re.search(r'in (\d+) hours?', text)
        hours = int(match.group(1))
        result = now + timedelta(hours=hours)
        print(f"[DEBUG DATETIME] 'in {hours} hours' -> {result}")
        return result
    
    # Handle "in X days"
    if re.search(r'in (\d+) days?', text):
        match = re.search(r'in (\d+) days?', text)
        days = int(match.group(1))
        result = now + timedelta(days=days)
        print(f"[DEBUG DATETIME] 'in {days} days' -> {result}")
        return result
    
    # Handle common shortcuts
    if 'in a minute' in text or 'in 1 minute' in text:
        result = now + timedelta(minutes=1)
        print(f"[DEBUG DATETIME] 'in a minute' -> {result}")
        return result
        
    if 'in an hour' in text or 'in 1 hour' in text:
        result = now + timedelta(hours=1)
        print(f"[DEBUG DATETIME] 'in an hour' -> {result}")
        return result
    
    if 'in half an hour' in text:
        result = now + timedelta(minutes=30)
        print(f"[DEBUG DATETIME] 'in half an hour' -> {result}")
        return result
    
    # Handle specific times like "at 3pm", "tomorrow at 9am"
    time_patterns = [
        (r'tomorrow at (\d{1,2}):?(\d{0,2})\s*(am|pm)?', lambda m: 
         _calculate_tomorrow_time(now, m.group(1), m.group(2), m.group(3))),
        
        (r'today at (\d{1,2}):?(\d{0,2})\s*(am|pm)?', lambda m: 
         _calculate_today_time(now, m.group(1), m.group(2), m.group(3))),
         
        (r'at (\d{1,2}):?(\d{0,2})\s*(am|pm)?', lambda m: 
         _calculate_time_today(now, m.group(1), m.group(2), m.group(3))),
    ]
    
    # Try specific time patterns
    for pattern, calculator in time_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                result = calculator(match)
                print(f"[DEBUG DATETIME] Time pattern matched -> {result}")
                return result
            except Exception as e:
                print(f"[DEBUG DATETIME] Error with time pattern: {e}")
                continue
    
    # Try parsing with dateutil as fallback
    try:
        parsed = date_parser.parse(text, fuzzy=True)
        if parsed.tzinfo is None:
            parsed = Config.SCHEDULER_TIMEZONE.localize(parsed)
        
        # If parsed time is in the past, assume they mean tomorrow
        if parsed <= now:
            parsed += timedelta(days=1)
            
        print(f"[DEBUG DATETIME] Dateutil parsed -> {parsed}")
        return parsed
    except Exception as e:
        print(f"[DEBUG DATETIME] Dateutil parsing failed: {e}")
        
    print(f"[DEBUG DATETIME] No patterns matched for: '{text}'")
    return None

def _calculate_tomorrow_time(now: datetime, hour_str: str, minute_str: str, ampm: Optional[str]) -> datetime:
    """Calculate time for tomorrow"""
    hour = int(hour_str)
    minute = int(minute_str) if minute_str else 0
    
    if ampm:
        if ampm.lower() == 'pm' and hour != 12:
            hour += 12
        elif ampm.lower() == 'am' and hour == 12:
            hour = 0
    
    tomorrow = now + timedelta(days=1)
    result = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return result

def _calculate_today_time(now: datetime, hour_str: str, minute_str: str, ampm: Optional[str]) -> datetime:
    """Calculate time for today"""
    hour = int(hour_str)
    minute = int(minute_str) if minute_str else 0
    
    if ampm:
        if ampm.lower() == 'pm' and hour != 12:
            hour += 12
        elif ampm.lower() == 'am' and hour == 12:
            hour = 0
    
    result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If time has passed today, move to tomorrow
    if result <= now:
        result += timedelta(days=1)
    
    return result

def _calculate_time_today(now: datetime, hour_str: str, minute_str: str, ampm: Optional[str]) -> datetime:
    """Calculate time for today (or tomorrow if past)"""
    return _calculate_today_time(now, hour_str, minute_str, ampm)

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
