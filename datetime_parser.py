import re
from datetime import datetime, timedelta
from typing import Optional
import pytz
from dateutil import parser as date_parser
from config import Config

def parse_natural_datetime(text: str) -> Optional[datetime]:
    """Parse natural language datetime expressions"""
    
    now = datetime.now(Config.SCHEDULER_TIMEZONE)
    text = text.lower().strip()
    
    # Patterns for relative times
    relative_patterns = [
        (r'in (\d+) minutes?', lambda m: now + timedelta(minutes=int(m.group(1)))),
        (r'in (\d+) hours?', lambda m: now + timedelta(hours=int(m.group(1)))),
        (r'in (\d+) days?', lambda m: now + timedelta(days=int(m.group(1)))),
        (r'in (\d+) weeks?', lambda m: now + timedelta(weeks=int(m.group(1)))),
        
        (r'(\d+) minutes? from now', lambda m: now + timedelta(minutes=int(m.group(1)))),
        (r'(\d+) hours? from now', lambda m: now + timedelta(hours=int(m.group(1)))),
        (r'(\d+) days? from now', lambda m: now + timedelta(days=int(m.group(1)))),
        
        (r'tomorrow at (\d{1,2}):?(\d{0,2})\s*(am|pm)', lambda m: 
         (now + timedelta(days=1)).replace(
             hour=int(m.group(1)) % 12 + (12 if m.group(3) == 'pm' else 0),
             minute=int(m.group(2)) if m.group(2) else 0,
             second=0, microsecond=0
         )),
        
        (r'today at (\d{1,2}):?(\d{0,2})\s*(am|pm)', lambda m: 
         now.replace(
             hour=int(m.group(1)) % 12 + (12 if m.group(3) == 'pm' else 0),
             minute=int(m.group(2)) if m.group(2) else 0,
             second=0, microsecond=0
         )),
         
        (r'at (\d{1,2}):?(\d{0,2})\s*(am|pm)', lambda m: 
         now.replace(
             hour=int(m.group(1)) % 12 + (12 if m.group(3) == 'pm' else 0),
             minute=int(m.group(2)) if m.group(2) else 0,
             second=0, microsecond=0
         )),
    ]
    
    # Try relative patterns first
    for pattern, calculator in relative_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                result = calculator(match)
                if "today" in text and result < now:
                    result += timedelta(days=1)
                return result
            except Exception as e:
                print(f"Error calculating relative time: {e}")
                continue
    
    # Try parsing with dateutil
    try:
        parsed = date_parser.parse(text, fuzzy=True)
        if parsed.tzinfo is None:
            parsed = Config.SCHEDULER_TIMEZONE.localize(parsed)
        return parsed
    except Exception as e:
        print(f"Error parsing datetime with dateutil: {e}")
        
    return None