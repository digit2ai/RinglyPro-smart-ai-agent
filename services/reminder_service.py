from datetime import datetime, timedelta
from typing import Dict, Any, List
import pytz
import re
from dateutil import parser as date_parser
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler import events
from config import Config

# Global service references for job callbacks
_twilio_service = None
_email_service = None

def _send_sms_reminder_job(phone_number: str, message: str, reminder_id: str):
    """Standalone function for SMS reminder job (avoids serialization issues)"""
    try:
        print(f"🚨 JOB EXECUTING: reminder_id={reminder_id}, phone={phone_number}")
        print(f"🚨 TWILIO SERVICE: {_twilio_service}")
        print(f"🚨 MESSAGE: {message}")
        
        print(f"[REMINDER] Sending SMS reminder {reminder_id} to {phone_number}")
        result = _twilio_service.send_sms(phone_number, message)
        
        if result.get('success'):
            print(f"[REMINDER] ✅ SMS reminder {reminder_id} sent successfully")
        else:
            print(f"[REMINDER] ❌ Failed to send SMS reminder {reminder_id}: {result.get('error')}")
            
    except Exception as e:
        print(f"[REMINDER] ❌ Exception sending SMS reminder {reminder_id}: {str(e)}")

def _send_email_reminder_job(email_address: str, subject: str, message: str, reminder_id: str):
    """Standalone function for email reminder job (avoids serialization issues)"""
    try:
        print(f"[REMINDER] Sending email reminder {reminder_id} to {email_address}")
        result = _email_service.send_email(email_address, subject, message)
        
        if result.get('success'):
            print(f"[REMINDER] ✅ Email reminder {reminder_id} sent successfully")
        else:
            print(f"[REMINDER] ❌ Failed to send email reminder {reminder_id}: {result.get('error')}")
            
    except Exception as e:
        print(f"[REMINDER] ❌ Exception sending email reminder {reminder_id}: {str(e)}")

class ReminderService:
    """Service for scheduling and managing reminders"""
    
    def __init__(self, twilio_service, email_service):
        global _twilio_service, _email_service
        self.twilio_service = twilio_service
        self.email_service = email_service
        # Set global references for job callbacks
        _twilio_service = twilio_service
        _email_service = email_service
        self.scheduler = None
        self._setup_scheduler()
    
    def _setup_scheduler(self):
        """Initialize the background scheduler"""
        # Use memory storage instead of SQLite for Render compatibility
        jobstores = {
            'default': 'memory'  # Changed from SQLAlchemyJobStore to memory
        }
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        job_defaults = {
            'coalesce': True,  # Combine multiple pending executions
            'max_instances': 1  # Only one instance per job
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores, 
            executors=executors, 
            job_defaults=job_defaults, 
            timezone=pytz.UTC  # Use UTC timezone to match server
        )
        
        # Add error handling and job recovery
        self.scheduler.add_listener(self._job_listener, events.EVENT_JOB_ERROR | events.EVENT_JOB_EXECUTED)
        
        self.scheduler.start()
        print("✅ Reminder scheduler started with memory storage")
    
    def parse_natural_datetime(self, text: str) -> datetime:
        """Parse natural language datetime expressions"""
        
        # Current time in UTC (matching your scheduler timezone)
        now = datetime.now(pytz.UTC)
        
        # Clean the text
        text = text.lower().strip()
        
        # Patterns for relative times
        relative_patterns = [
            # "in 5 minutes", "in 1 hour", "in 2 days"
            (r'in (\d+) minutes?', lambda m: now + timedelta(minutes=int(m.group(1)))),
            (r'in (\d+) hours?', lambda m: now + timedelta(hours=int(m.group(1)))),
            (r'in (\d+) days?', lambda m: now + timedelta(days=int(m.group(1)))),
            (r'in (\d+) weeks?', lambda m: now + timedelta(weeks=int(m.group(1)))),
            
            # "5 minutes from now", "1 hour from now"
            (r'(\d+) minutes? from now', lambda m: now + timedelta(minutes=int(m.group(1)))),
            (r'(\d+) hours? from now', lambda m: now + timedelta(hours=int(m.group(1)))),
            (r'(\d+) days? from now', lambda m: now + timedelta(days=int(m.group(1)))),
            
            # "tomorrow at 3pm", "today at 5:30pm"
            (r'tomorrow at (\d{1,2}):?(\d{0,2})\s*(am|pm)', self._parse_tomorrow_time),
            (r'today at (\d{1,2}):?(\d{0,2})\s*(am|pm)', self._parse_today_time),
            (r'at (\d{1,2}):?(\d{0,2})\s*(am|pm)', self._parse_today_time),
            
            # Day-specific patterns
            (r'on (monday|tuesday|wednesday|thursday|friday|saturday|sunday) at (\d{1,2}):?(\d{0,2})\s*(am|pm)', self._parse_day_time),
            (r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday) at (\d{1,2}):?(\d{0,2})\s*(am|pm)', self._parse_day_time),
            
            # Simple day references
            (r'tomorrow', lambda m: now + timedelta(days=1)),
            (r'next week', lambda m: now + timedelta(weeks=1)),
            
            # Fractional times
            (r'in (\d+\.?\d*) hours?', lambda m: now + timedelta(hours=float(m.group(1)))),
            (r'in a half hour', lambda m: now + timedelta(minutes=30)),
            (r'in an hour', lambda m: now + timedelta(hours=1)),
        ]
        
        # Try relative patterns first
        for pattern, calculator in relative_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    result = calculator(match)
                    # Ensure timezone aware
                    if result.tzinfo is None:
                        result = result.replace(tzinfo=pytz.UTC)
                    
                    # If the time is in the past and it's a "today" reference, move to tomorrow
                    if "today" in text and result < now:
                        result += timedelta(days=1)
                    
                    print(f"📅 Parsed '{text}' as: {result}")
                    return result
                except Exception as e:
                    print(f"Error calculating relative time: {e}")
                    continue
        
        # Try parsing with dateutil for absolute dates
        try:
            parsed = date_parser.parse(text, fuzzy=True)
            # Make timezone aware
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=pytz.UTC)
            
            # If the parsed time is in the past, assume next occurrence
            if parsed < now:
                # Try adding a day for time-only references
                if parsed.date() == now.date():
                    parsed += timedelta(days=1)
            
            print(f"📅 Parsed '{text}' with dateutil as: {parsed}")
            return parsed
        except Exception as e:
            print(f"Dateutil parsing failed for '{text}': {e}")
            
        print(f"⚠️ Could not parse datetime from: '{text}'")
        return None
    
    def _parse_tomorrow_time(self, match):
        """Parse tomorrow at specific time"""
        now = datetime.now(pytz.UTC)
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)
        
        # Convert to 24-hour format
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        
        return (now + timedelta(days=1)).replace(
            hour=hour, minute=minute, second=0, microsecond=0, tzinfo=pytz.UTC
        )
    
    def _parse_today_time(self, match):
        """Parse today at specific time"""
        now = datetime.now(pytz.UTC)
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)
        
        # Convert to 24-hour format
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        
        result = now.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=pytz.UTC)
        
        # If time has passed today, schedule for tomorrow
        if result <= now:
            result += timedelta(days=1)
        
        return result
    
    def _parse_day_time(self, match):
        """Parse specific day at specific time"""
        now = datetime.now(pytz.UTC)
        
        # Handle different group patterns
        if len(match.groups()) == 4:  # "on monday at 3pm"
            day_name = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3)) if match.group(3) else 0
            ampm = match.group(4)
        else:  # "monday at 3pm"
            day_name = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3)) if match.group(3) else 0
            ampm = match.group(4)
        
        # Convert to 24-hour format
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        
        # Find next occurrence of the day
        days_ahead = self._days_until_weekday(day_name)
        target_date = now + timedelta(days=days_ahead)
        
        return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=pytz.UTC)
    
    def _days_until_weekday(self, day_name: str) -> int:
        """Calculate days until target weekday"""
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        now = datetime.now(pytz.UTC)
        target_day = days[day_name.lower()]
        current_day = now.weekday()
        
        days_ahead = target_day - current_day
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        return days_ahead
    
    def extract_reminder_command(self, text: str) -> Dict[str, Any]:
        """Extract reminder command from natural language text"""
        
        # Patterns for reminder commands
        patterns = [
            # "remind me to call John in 30 minutes"
            (r'remind me to (.+?) in (.+)', 'remind_in'),
            # "set a reminder to call John at 3pm"  
            (r'set (?:a )?reminder to (.+?) at (.+)', 'remind_at'),
            # "remind me in 1 hour to call John"
            (r'remind me in (.+?) to (.+)', 'remind_in_alt'),
            # "schedule a reminder to call John tomorrow at 3pm"
            (r'schedule (?:a )?reminder to (.+?) (.+)', 'schedule_reminder'),
            # "send me a reminder to call John in 30 minutes"
            (r'send me (?:a )?reminder to (.+?) in (.+)', 'send_reminder_in'),
            # "text me in 1 hour to call John"
            (r'text me in (.+?) to (.+)', 'text_reminder'),
            # "sms reminder in 30 minutes saying call John"
            (r'sms reminder in (.+?) saying (.+)', 'sms_reminder'),
            # "remind me at 5pm to call John"
            (r'remind me at (.+?) to (.+)', 'remind_at_alt'),
            # "notification in 2 hours about meeting"
            (r'notification in (.+?) about (.+)', 'notification'),
        ]
        
        text_lower = text.lower().strip()
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Determine message and time based on pattern type
                if pattern_type in ['remind_in', 'send_reminder_in']:
                    message = groups[0].strip()
                    time_str = groups[1].strip()
                elif pattern_type in ['remind_at', 'schedule_reminder']:
                    message = groups[0].strip()
                    time_str = groups[1].strip()
                elif pattern_type in ['remind_in_alt', 'text_reminder']:
                    time_str = groups[0].strip()
                    message = groups[1].strip()
                elif pattern_type in ['sms_reminder', 'notification']:
                    time_str = groups[0].strip()
                    message = groups[1].strip()
                elif pattern_type == 'remind_at_alt':
                    time_str = groups[0].strip()
                    message = groups[1].strip()
                else:
                    # Default: first group is message, second is time
                    message = groups[0].strip()
                    time_str = groups[1].strip()
                
                # Parse the time
                reminder_time = self.parse_natural_datetime(time_str)
                
                if reminder_time:
                    # Clean up voice recognition artifacts
                    message = self._clean_voice_message(message)
                    
                    return {
                        "action": "schedule_sms_reminder",
                        "message": message,
                        "reminder_time": reminder_time.isoformat(),
                        "time_str": time_str,
                        "original_text": text,
                        "pattern_type": pattern_type
                    }
        
        return None
    
    def _clean_voice_message(self, message: str) -> str:
        """Clean up voice recognition artifacts"""
        message = message.replace(" period", ".").replace(" comma", ",")
        message = message.replace(" question mark", "?").replace(" exclamation mark", "!")
        return message.strip()
    
    def schedule_sms_reminder(self, phone_number: str, message: str, reminder_time: datetime) -> Dict[str, Any]:
        """Schedule an SMS reminder"""
        try:
            # Validate future time
            now = datetime.now(Config.SCHEDULER_TIMEZONE)
            if reminder_time <= now:
                return {"success": False, "error": "Reminder time must be in the future"}
            
            # Create unique job ID
            job_id = f"sms_reminder_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(phone_number + message) % 10000}"
            
            # Schedule the reminder using standalone function
            self.scheduler.add_job(
                func=_send_sms_reminder_job,
                trigger="date",
                run_date=reminder_time,
                args=[phone_number, message, job_id],
                id=job_id,
                name=f"SMS Reminder: {message[:50]}..."
            )
            
            return {
                "success": True,
                "job_id": job_id,
                "reminder_time": reminder_time.isoformat(),
                "message": f"SMS reminder scheduled for {reminder_time.strftime('%Y-%m-%d at %I:%M %p %Z')}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to schedule SMS reminder: {str(e)}"}
    
    def schedule_email_reminder(self, email_address: str, subject: str, message: str, reminder_time: datetime) -> Dict[str, Any]:
        """Schedule an email reminder"""
        try:
            # Validate future time
            now = datetime.now(Config.SCHEDULER_TIMEZONE)
            if reminder_time <= now:
                return {"success": False, "error": "Reminder time must be in the future"}
            
            # Create unique job ID
            job_id = f"email_reminder_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(email_address + message) % 10000}"
            
            # Schedule the reminder using standalone function
            self.scheduler.add_job(
                func=_send_email_reminder_job,
                trigger="date",
                run_date=reminder_time,
                args=[email_address, subject, message, job_id],
                id=job_id,
                name=f"Email Reminder: {subject[:50]}..."
            )
            
            return {
                "success": True,
                "job_id": job_id,
                "reminder_time": reminder_time.isoformat(),
                "message": f"Email reminder scheduled for {reminder_time.strftime('%Y-%m-%d at %I:%M %p %Z')}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to schedule email reminder: {str(e)}"}
    
    def list_reminders(self) -> Dict[str, Any]:
        """List all scheduled reminders"""
        try:
            jobs = self.scheduler.get_jobs()
            reminders = []
            
            for job in jobs:
                if job.id.startswith('sms_reminder_') or job.id.startswith('email_reminder_'):
                    reminders.append({
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                        "trigger": str(job.trigger),
                        "type": "sms" if job.id.startswith('sms_reminder_') else "email"
                    })
            
            return {
                "success": True,
                "total_reminders": len(reminders),
                "reminders": reminders
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list reminders: {str(e)}"}
    
    def cancel_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """Cancel a scheduled reminder"""
        try:
            self.scheduler.remove_job(reminder_id)
            return {"success": True, "message": f"Reminder {reminder_id} cancelled successfully"}
        except Exception as e:
            return {"success": False, "error": f"Failed to cancel reminder: {str(e)}"}
    
    def _job_listener(self, event):
        """Listen for job events to debug execution"""
        if event.exception:
            print(f"🚨 JOB ERROR: {event.job_id} - {event.exception}")
        else:
            print(f"✅ JOB EXECUTED: {event.job_id}")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            if self.scheduler:
                self.scheduler.shutdown()
                print("🔄 Reminder scheduler shutdown successfully")
        except Exception as e:
            print(f"⚠️ Error shutting down scheduler: {e}")
