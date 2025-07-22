import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List
from utils.formatters import is_phone_number, is_email_address, format_phone_number

class ActionHandlers:
    """Handle various actions dispatched by the application"""
    
    def __init__(self, twilio_service, email_service, claude_service, reminder_service):
        self.twilio_service = twilio_service
        self.email_service = email_service
        self.claude_service = claude_service
        self.reminder_service = reminder_service
    
    def handle_create_task(self, data: Dict[str, Any]) -> str:
        """Handle task creation"""
        print("[ACTION] Creating task:", data.get("title"), data.get("due_date"))
        return f"Task '{data.get('title')}' scheduled for {data.get('due_date')}."
    
    def handle_create_appointment(self, data: Dict[str, Any]) -> str:
        """Handle appointment creation"""
        print("[ACTION] Creating appointment:", data.get("title"), data.get("due_date"))
        return f"Appointment '{data.get('title')}' booked for {data.get('due_date')}."
    
    def handle_send_message(self, data: Dict[str, Any]) -> str:
        """Handle single message sending"""
        recipient = data.get("recipient", "")
        message = data.get("message", "")
        original_message = data.get("original_message", message)
        
        print(f"[ACTION] Sending message to {recipient}")
        
        if is_phone_number(recipient):
            formatted_phone = format_phone_number(recipient)
            print(f"[ACTION] Detected phone number, processing SMS to {formatted_phone}")
            
            enhanced_message = self.claude_service.enhance_message(original_message)
            result = self.twilio_service.send_sms(formatted_phone, enhanced_message)
            
            if result.get('success'):
                return f"✅ Professional SMS sent to {recipient}!\n\nOriginal: {original_message}\nEnhanced: {enhanced_message}\n\nMessage ID: {result.get('message_sid', 'N/A')}"
            else:
                return f"Failed to send SMS to {recipient}: {result.get('error')}"
        else:
            enhanced_message = self.claude_service.enhance_message(message)
            return f"Enhanced message for {recipient}:\nOriginal: {message}\nEnhanced: {enhanced_message}"
    
    def handle_send_email(self, data: Dict[str, Any]) -> str:
        """Handle single email sending"""
        recipient = data.get("recipient", "")
        message = data.get("message", "")
        subject = data.get("subject", "")
        original_message = data.get("original_message", message)
        
        print(f"[ACTION] Sending email to {recipient}")
        
        if is_email_address(recipient):
            enhanced_message = self.claude_service.enhance_message(original_message)
            
            if not subject:
                subject = self.claude_service.generate_email_subject(enhanced_message)
            
            result = self.email_service.send_email(recipient, subject, enhanced_message)
            
            if result.get('success'):
                return f"✅ Professional email sent to {recipient}!\n\nSubject: {subject}\nOriginal: {original_message}\nEnhanced: {enhanced_message}\n\nSent at: {result.get('timestamp', 'N/A')}"
            else:
                return f"Failed to send email to {recipient}: {result.get('error')}"
        else:
            enhanced_message = self.claude_service.enhance_message(message)
            return f"Enhanced message for {recipient}:\nOriginal: {message}\nEnhanced: {enhanced_message}\n\nNote: {recipient} is not a valid email address"
    
    def handle_send_message_multi(self, data: Dict[str, Any]) -> str:
        """Handle multi-recipient message sending"""
        recipients = data.get("recipients", [])
        message = data.get("message", "")
        original_message = data.get("original_message", message)
        
        if not recipients:
            return "❌ No recipients specified"
        
        result = self.send_sms_to_multiple(recipients, original_message, enhance=True)
        return self._format_multi_response(result, "message")
    
    def handle_send_email_multi(self, data: Dict[str, Any]) -> str:
        """Handle multi-recipient email sending"""
        recipients = data.get("recipients", [])
        message = data.get("message", "")
        subject = data.get("subject", "")
        original_message = data.get("original_message", message)
        
        if not recipients:
            return "❌ No recipients specified"
        
        result = self.send_emails_to_multiple(recipients, subject, original_message, enhance=True)
        return self._format_multi_response(result, "email")
    
    def handle_schedule_sms_reminder(self, data: Dict[str, Any]) -> str:
        """Handle SMS reminder scheduling"""
        recipient = data.get("recipient", "")
        message = data.get("message", "")
        reminder_time_str = data.get("reminder_time", "")
        
        if not recipient:
            return "❌ No recipient specified for SMS reminder"
        
        if not is_phone_number(recipient):
            return f"❌ Invalid phone number format: {recipient}"
        
        try:
            reminder_time = datetime.fromisoformat(reminder_time_str.replace('Z', '+00:00'))
            formatted_phone = format_phone_number(recipient)
            enhanced_message = self.claude_service.enhance_message(message)
            
            result = self.reminder_service.schedule_sms_reminder(formatted_phone, enhanced_message, reminder_time)
            
            if result["success"]:
                return f"✅ SMS reminder scheduled!\n\n📱 To: {recipient}\n⏰ When: {result['message']}\n💬 Message: {enhanced_message}\n🆔 Reminder ID: {result['job_id']}"
            else:
                return f"❌ {result['error']}"
                
        except Exception as e:
            return f"❌ Failed to schedule SMS reminder: {str(e)}"
    
    def handle_schedule_email_reminder(self, data: Dict[str, Any]) -> str:
        """Handle email reminder scheduling"""
        recipient = data.get("recipient", "")
        message = data.get("message", "")
        subject = data.get("subject", "")
        reminder_time_str = data.get("reminder_time", "")
        
        if not recipient:
            return "❌ No recipient specified for email reminder"
        
        if not is_email_address(recipient):
            return f"❌ Invalid email address format: {recipient}"
        
        try:
            reminder_time = datetime.fromisoformat(reminder_time_str.replace('Z', '+00:00'))
            enhanced_message = self.claude_service.enhance_message(message)
            
            if not subject:
                subject = f"Reminder: {self.claude_service.generate_email_subject(enhanced_message)}"
            
            result = self.reminder_service.schedule_email_reminder(recipient, subject, enhanced_message, reminder_time)
            
            if result["success"]:
                return f"✅ Email reminder scheduled!\n\n📧 To: {recipient}\n⏰ When: {result['message']}\n📨 Subject: {subject}\n💬 Message: {enhanced_message}\n🆔 Reminder ID: {result['job_id']}"
            else:
                return f"❌ {result['error']}"
                
        except Exception as e:
            return f"❌ Failed to schedule email reminder: {str(e)}"
    
    def handle_log_conversation(self, data: Dict[str, Any]) -> str:
        """Handle conversation logging"""
        print("[ACTION] Logging conversation:", data.get("notes"))
        return "Conversation log saved."
    def send_sms_to_multiple(self, recipients: List[str], message: str, enhance: bool = True) -> Dict[str, Any]:
        """Send SMS to multiple recipients with threading"""
        enhanced_message = self.claude_service.enhance_message(message) if enhance else message
        
        results = []
        successful_sends = 0
        failed_sends = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_recipient = {
                executor.submit(self._send_single_sms, recipient, enhanced_message): recipient 
                for recipient in recipients
            }
            
            for future in concurrent.futures.as_completed(future_to_recipient):
                recipient = future_to_recipient[future]
                try:
                    result = future.result()
                    result['recipient'] = recipient
                    results.append(result)
                    
                    if result.get('success'):
                        successful_sends += 1
                    else:
                        failed_sends += 1
                        
                except Exception as exc:
                    error_result = {
                        'recipient': recipient,
                        'success': False,
                        'error': f'Exception occurred: {exc}',
                        'type': 'sms'
                    }
                    results.append(error_result)
                    failed_sends += 1
        
        return {
            "success": successful_sends > 0,
            "total_recipients": len(recipients),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "original_message": message,
            "enhanced_message": enhanced_message,
            "results": results,
            "type": "sms_multi"
        }
    
    def send_emails_to_multiple(self, recipients: List[str], subject: str, message: str, enhance: bool = True) -> Dict[str, Any]:
        """Send emails to multiple recipients with threading"""
        enhanced_message = self.claude_service.enhance_message(message) if enhance else message
        
        if not subject:
            subject = self.claude_service.generate_email_subject(enhanced_message)
        
        results = []
        successful_sends = 0
        failed_sends = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_recipient = {
                executor.submit(self._send_single_email, recipient, subject, enhanced_message): recipient 
                for recipient in recipients
            }
            
            for future in concurrent.futures.as_completed(future_to_recipient):
                recipient = future_to_recipient[future]
                try:
                    result = future.result()
                    result['recipient'] = recipient
                    results.append(result)
                    
                    if result.get('success'):
                        successful_sends += 1
                    else:
                        failed_sends += 1
                        
                except Exception as exc:
                    error_result = {
                        'recipient': recipient,
                        'success': False,
                        'error': f'Exception occurred: {exc}',
                        'type': 'email'
                    }
                    results.append(error_result)
                    failed_sends += 1
        
        return {
            "success": successful_sends > 0,
            "total_recipients": len(recipients),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "original_message": message,
            "enhanced_message": enhanced_message,
            "subject": subject,
            "results": results,
            "type": "email_multi"
        }
    
    def send_mixed_messages(self, recipients: List[str], message: str, subject: str = None, enhance: bool = True) -> Dict[str, Any]:
        """Send messages to mixed recipients (SMS for phones, emails for email addresses)"""
        phone_recipients = [r for r in recipients if is_phone_number(r)]
        email_recipients = [r for r in recipients if is_email_address(r)]
        other_recipients = [r for r in recipients if not is_phone_number(r) and not is_email_address(r)]
        
        enhanced_message = self.claude_service.enhance_message(message) if enhance else message
        
        results = []
        successful_sends = 0
        failed_sends = 0
        
        # Send SMS to phone numbers
        if phone_recipients:
            sms_result = self.send_sms_to_multiple(phone_recipients, message, enhance=False)
            results.extend(sms_result.get('results', []))
            successful_sends += sms_result.get('successful_sends', 0)
            failed_sends += sms_result.get('failed_sends', 0)
        
        # Send emails to email addresses
        if email_recipients:
            email_result = self.send_emails_to_multiple(email_recipients, subject, message, enhance=False)
            results.extend(email_result.get('results', []))
            successful_sends += email_result.get('successful_sends', 0)
            failed_sends += email_result.get('failed_sends', 0)
        
        # Log other recipients
        for recipient in other_recipients:
            results.append({
                'recipient': recipient,
                'success': False,
                'error': 'Unrecognized recipient format (not phone or email)',
                'type': 'unknown'
            })
            failed_sends += 1
        
        return {
            "success": successful_sends > 0,
            "total_recipients": len(recipients),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "phone_recipients": len(phone_recipients),
            "email_recipients": len(email_recipients),
            "other_recipients": len(other_recipients),
            "original_message": message,
            "enhanced_message": enhanced_message,
            "subject": subject,
            "results": results,
            "type": "mixed_multi"
        }
    
    def _send_single_sms(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send SMS to a single recipient"""
        if is_phone_number(recipient):
            formatted_phone = format_phone_number(recipient)
            result = self.twilio_service.send_sms(formatted_phone, message)
            result['formatted_recipient'] = formatted_phone
            result['original_recipient'] = recipient
            result['type'] = 'sms'
            return result
        else:
            return {
                "success": False,
                "error": f"Invalid phone number format: {recipient}",
                "original_recipient": recipient,
                "type": 'sms'
            }
    
    def _send_single_email(self, recipient: str, subject: str, message: str) -> Dict[str, Any]:
        """Send email to a single recipient"""
        if is_email_address(recipient):
            result = self.email_service.send_email(recipient, subject, message)
            result['original_recipient'] = recipient
            result['type'] = 'email'
            return result
        else:
            return {
                "success": False,
                "error": f"Invalid email address format: {recipient}",
                "original_recipient": recipient,
                "type": 'email'
            }
    
    def _format_multi_response(self, result: Dict[str, Any], message_type: str) -> str:
        """Format response for multi-recipient operations"""
        if result["success"]:
            success_msg = f"✅ {message_type.title()} sent to {result['successful_sends']}/{result['total_recipients']} recipients!"
            success_msg += f"\n\nOriginal: {result['original_message']}"
            success_msg += f"\nEnhanced: {result['enhanced_message']}"
            
            if result.get('subject'):
                success_msg += f"\nSubject: {result['subject']}"
            
            if result["failed_sends"] > 0:
                success_msg += f"\n\n⚠️ {result['failed_sends']} {message_type}s failed to send"
                
            success_msg += "\n\n📋 Delivery Details:"
            for res in result["results"]:
                status = "✅" if res.get("success") else "❌"
                recipient = res.get("original_recipient", res.get("recipient", "Unknown"))
                success_msg += f"\n{status} {recipient}"
                if not res.get("success"):
                    success_msg += f" - {res.get('error', 'Unknown error')}"
            
            return success_msg
        else:
            return f"❌ Failed to send {message_type}s to all {result['total_recipients']} recipients"
    
    def dispatch_action(self, parsed: Dict[str, Any]) -> str:
        """Dispatch action based on parsed command"""
        action = parsed.get("action")
        
        action_map = {
            "create_task": self.handle_create_task,
            "create_appointment": self.handle_create_appointment,
            "send_message": self.handle_send_message,
            "send_message_multi": self.handle_send_message_multi,
            "send_email": self.handle_send_email,
            "send_email_multi": self.handle_send_email_multi,
            "schedule_sms_reminder": self.handle_schedule_sms_reminder,
            "schedule_email_reminder": self.handle_schedule_email_reminder,
            "log_conversation": self.handle_log_conversation,
        }
        
        handler = action_map.get(action)
        if handler:
            return handler(parsed)
        else:
            return f"Unknown action: {action}"