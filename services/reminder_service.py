from datetime import datetime, timedelta
from typing import Dict, Any, List
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from config import Config

# Global service references for job callbacks
_twilio_service = None
_email_service = None

def _send_sms_reminder_job(phone_number: str, message: str, reminder_id: str):
    """Standalone function for SMS reminder job (avoids serialization issues)"""
    try:
        print(f"[REMINDER] 🔥 Executing SMS job {reminder_id} at {datetime.now()}")
        print(f"[REMINDER] Global _twilio_service status: {_twilio_service is not None}")
        print(f"[REMINDER] Sending SMS reminder {reminder_id} to {phone_number}")
        
        if _twilio_service is None:
            print(f"[REMINDER] ❌ CRITICAL: _twilio_service is None when job executed!")
            return
            
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
        print(f"[REMINDER] 🔥 Executing Email job {reminder_id} at {datetime.now()}")
        print(f"[REMINDER] Global _email_service status: {_email_service is not None}")
        print(f"[REMINDER] Sending email reminder {reminder_id} to {email_address}")
        
        if _email_service is None:
            print(f"[REMINDER] ❌ CRITICAL: _email_service is None when job executed!")
            return
            
        result = _email_service.send_email(email_address, subject, message)
        
        if result.get('success'):
            print(f"[REMINDER] ✅ Email reminder {reminder_id} sent successfully")
        else:
            print(f"[REMINDER] ❌ Failed to send email reminder {reminder_id}: {result.get('error')}")
            
    except Exception as e:
        print(f"[REMINDER] ❌ Exception sending email reminder {reminder_id}: {str(e)}")

def _test_scheduler_job():
    """Test function to verify scheduler is working"""
    print(f"🔥🔥🔥 TEST JOB EXECUTED SUCCESSFULLY at {datetime.now()}")
    print(f"🔥🔥🔥 Scheduler is working! Global services status:")
    print(f"🔥🔥🔥 _twilio_service: {_twilio_service is not None}")
    print(f"🔥🔥🔥 _email_service: {_email_service is not None}")

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
        jobstores = {
            'default': SQLAlchemyJobStore(url=Config.SCHEDULER_JOBSTORE_URL)
        }
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores, 
            executors=executors, 
            job_defaults=job_defaults, 
            timezone=Config.SCHEDULER_TIMEZONE
        )
        self.scheduler.start()
        print("✅ Reminder scheduler started")
    
    def test_scheduler(self, delay_seconds: int = 10) -> Dict[str, Any]:
        """Test if the scheduler is working by scheduling a simple test job"""
        try:
            run_time = datetime.now(Config.SCHEDULER_TIMEZONE) + timedelta(seconds=delay_seconds)
            job_id = f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🧪 Scheduling test job {job_id} to run in {delay_seconds} seconds at {run_time}")
            
            self.scheduler.add_job(
                func=_test_scheduler_job,
                trigger="date",
                run_date=run_time,
                id=job_id,
                name="Scheduler Test Job"
            )
            
            return {
                "success": True,
                "job_id": job_id,
                "test_time": run_time.isoformat(),
                "message": f"Test job scheduled for {run_time.strftime('%Y-%m-%d at %I:%M:%S %p %Z')}. Watch logs for execution."
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to schedule test job: {str(e)}"}
    
    def test_scheduler(self, delay_seconds: int = 10) -> Dict[str, Any]:
        """Test if the scheduler is working by scheduling a simple test job"""
        try:
            run_time = datetime.now(Config.SCHEDULER_TIMEZONE) + timedelta(seconds=delay_seconds)
            job_id = f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🧪 Scheduling test job {job_id} to run in {delay_seconds} seconds at {run_time}")
            
            self.scheduler.add_job(
                func=_test_scheduler_job,
                trigger="date",
                run_date=run_time,
                id=job_id,
                name="Scheduler Test Job"
            )
            
            return {
                "success": True,
                "job_id": job_id,
                "test_time": run_time.isoformat(),
                "message": f"Test job scheduled for {run_time.strftime('%Y-%m-%d at %I:%M:%S %p %Z')}. Watch logs for execution."
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to schedule test job: {str(e)}"}

    def schedule_sms_reminder(self, phone_number: str, message: str, reminder_time: datetime) -> Dict[str, Any]:
        """Schedule an SMS reminder"""
        try:
            # Validate future time
            now = datetime.now(Config.SCHEDULER_TIMEZONE)
            if reminder_time <= now:
                return {"success": False, "error": "Reminder time must be in the future"}
            
            # Create unique job ID
            job_id = f"sms_reminder_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(phone_number + message) % 10000}"
            
            print(f"📱 Scheduling SMS job {job_id} for {reminder_time}")
            
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
            
            print(f"📧 Scheduling Email job {job_id} for {reminder_time}")
            
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
                if job.id.startswith('sms_reminder_') or job.id.startswith('email_reminder_') or job.id.startswith('test_job_'):
                    job_type = "test" if job.id.startswith('test_job_') else ("sms" if job.id.startswith('sms_reminder_') else "email")
                    reminders.append({
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                        "trigger": str(job.trigger),
                        "type": job_type
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
    
    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            if self.scheduler:
                self.scheduler.shutdown()
                print("🔄 Reminder scheduler shutdown successfully")
        except Exception as e:
            print(f"⚠️ Error shutting down scheduler: {e}")
