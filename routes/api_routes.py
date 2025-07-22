from flask import Blueprint, request, jsonify
from datetime import datetime
import re
from utils.formatters import is_phone_number, is_email_address, parse_recipients
from services.message_parser import MessageParser

api_bp = Blueprint('api', __name__)

def init_api_routes(action_handlers, reminder_service, twilio_service, email_service, claude_service):
    """Initialize API routes with dependency injection"""
    
    @api_bp.route('/execute', methods=['POST'])
    def execute():
        """Main command execution endpoint"""
        try:
            data = request.json
            prompt = data.get("text", "")
            
            # FIRST: Try reminder commands
            reminder_command = MessageParser.extract_reminder_command(prompt)
            if reminder_command:
                print(f"[VOICE REMINDER] Detected reminder command: {reminder_command}")
                dispatch_result = action_handlers.handle_schedule_sms_reminder(reminder_command)
                return jsonify({
                    "response": dispatch_result,
                    "claude_output": reminder_command
                })
            
            # SECOND: Try email commands
            email_command = MessageParser.extract_email_command(prompt)
            if email_command:
                print(f"[VOICE EMAIL] Detected email command: {email_command}")
                dispatch_result = action_handlers.handle_send_email(email_command)
                return jsonify({
                    "response": dispatch_result,
                    "claude_output": email_command
                })
            
            # THIRD: Try multi-recipient email commands
            multi_email_command = MessageParser.extract_email_command_multi(prompt)
            if multi_email_command:
                print(f"[VOICE EMAIL MULTI] Detected multi-recipient email: {multi_email_command}")
                if multi_email_command["action"] == "send_email_multi":
                    dispatch_result = action_handlers.handle_send_email_multi(multi_email_command)
                else:
                    dispatch_result = action_handlers.handle_send_email(multi_email_command)
                return jsonify({
                    "response": dispatch_result,
                    "claude_output": multi_email_command
                })
            
            # FOURTH: Try SMS commands
            sms_command = MessageParser.extract_sms_command(prompt)
            if sms_command:
                print(f"[VOICE SMS] Detected SMS command: {sms_command}")
                dispatch_result = action_handlers.handle_send_message(sms_command)
                return jsonify({
                    "response": dispatch_result,
                    "claude_output": sms_command
                })
            
            # FIFTH: Try multi-recipient SMS
            multi_sms_command = MessageParser.extract_sms_command_multi(prompt)
            if multi_sms_command:
                print(f"[VOICE SMS MULTI] Detected multi-recipient SMS: {multi_sms_command}")
                if multi_sms_command["action"] == "send_message_multi":
                    dispatch_result = action_handlers.handle_send_message_multi(multi_sms_command)
                else:
                    dispatch_result = action_handlers.handle_send_message(multi_sms_command)
                return jsonify({
                    "response": dispatch_result,
                    "claude_output": multi_sms_command
                })
            
            # SIXTH: Check for mixed message commands
            if "message" in prompt.lower() or "send" in prompt.lower():
                mixed_patterns = [
                    r'(?:send|message) (.+?) (?:saying|that) (.+)',
                    r'(?:tell|notify) (.+?) (?:that|about) (.+)',
                ]
                
                for pattern in mixed_patterns:
                    match = re.search(pattern, prompt.lower(), re.IGNORECASE)
                    if match:
                        recipients_text = match.group(1).strip()
                        message = match.group(2).strip()
                        recipients = parse_recipients(recipients_text)
                        
                        has_phone = any(is_phone_number(r) for r in recipients)
                        has_email = any(is_email_address(r) for r in recipients)
                        
                        if has_phone or has_email:
                            print(f"[MIXED MESSAGING] Detected mixed recipients: {recipients}")
                            result = action_handlers.send_mixed_messages(recipients, message, enhance=True)
                            
                            if result["success"]:
                                response_msg = f"✅ Mixed messages sent to {result['successful_sends']}/{result['total_recipients']} recipients!"
                                response_msg += f"\n\n📱 SMS: {result['phone_recipients']} recipients"
                                response_msg += f"\n📧 Email: {result['email_recipients']} recipients"
                                if result['other_recipients'] > 0:
                                    response_msg += f"\n❓ Other: {result['other_recipients']} recipients"
                                
                                response_msg += f"\n\nOriginal: {result['original_message']}"
                                response_msg += f"\nEnhanced: {result['enhanced_message']}"
                                
                                if result["failed_sends"] > 0:
                                    response_msg += f"\n\n⚠️ {result['failed_sends']} messages failed"
                                
                                response_msg += "\n\n📋 Delivery Details:"
                                for res in result["results"]:
                                    status = "✅" if res.get("success") else "❌"
                                    recipient = res.get("original_recipient", res.get("recipient", "Unknown"))
                                    msg_type = res.get("type", "unknown").upper()
                                    response_msg += f"\n{status} {recipient} ({msg_type})"
                                    if not res.get("success"):
                                        response_msg += f" - {res.get('error', 'Unknown error')}"
                                
                                return jsonify({
                                    "response": response_msg,
                                    "claude_output": {
                                        "action": "mixed_messaging",
                                        "recipients": recipients,
                                        "message": message,
                                        "result": result
                                    }
                                })
            
            # SEVENTH: Fall back to Claude for other commands
            result = claude_service.parse_command(prompt)
            
            if "error" in result:
                return jsonify({"response": result["error"]}), 500

            dispatch_result = action_handlers.dispatch_action(result)
            return jsonify({
                "response": dispatch_result,
                "claude_output": result
            })

        except Exception as e:
            return jsonify({"response": f"Unexpected error: {str(e)}"}), 500

    @api_bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        twilio_status = "configured" if twilio_service.client else "not configured"
        email_status = "configured" if email_service.email_address and email_service.email_password else "not configured"
        
        try:
            scheduled_jobs = len(reminder_service.scheduler.get_jobs())
            scheduler_status = "running"
        except Exception as e:
            scheduled_jobs = 0
            scheduler_status = f"error: {str(e)}"
        
        return jsonify({
            "status": "healthy",
            "twilio_status": twilio_status,
            "email_status": email_status,
            "scheduler_status": scheduler_status,
            "scheduled_jobs": scheduled_jobs,
            "claude_configured": bool(claude_service.api_key),
            "features": [
                "voice_sms", "voice_email", "multi_recipient_sms", 
                "multi_recipient_email", "mixed_messaging", "message_enhancement", 
                "professional_formatting", "auto_subject_generation", 
                "sms_reminders", "email_reminders", "natural_language_scheduling"
            ]
        })

    @api_bp.route('/test_sms', methods=['POST'])
    def test_sms():
        """Test single SMS endpoint"""
        data = request.json
        to = data.get('to')
        message = data.get('message', 'Test message from Smart AI Agent')
        enhance = data.get('enhance', True)
        
        if not to:
            return jsonify({"error": "Phone number 'to' is required"}), 400
        
        if enhance:
            enhanced_message = claude_service.enhance_message(message)
            result = twilio_service.send_sms(to, enhanced_message)
            result['original_message'] = message
            result['enhanced_message'] = enhanced_message
        else:
            result = twilio_service.send_sms(to, message)
        
        return jsonify(result)

    @api_bp.route('/test_email', methods=['POST'])
    def test_email():
        """Test single email endpoint"""
        data = request.json
        to = data.get('to')
        subject = data.get('subject', '')
        message = data.get('message', 'Test email from Smart AI Agent')
        enhance = data.get('enhance', True)
        
        if not to:
            return jsonify({"error": "Email address 'to' is required"}), 400
        
        if enhance:
            enhanced_message = claude_service.enhance_message(message)
            if not subject:
                subject = claude_service.generate_email_subject(enhanced_message)
            result = email_service.send_email(to, subject, enhanced_message)
            result['original_message'] = message
            result['enhanced_message'] = enhanced_message
            result['generated_subject'] = subject
        else:
            if not subject:
                subject = "Test Email from Smart AI Agent"
            result = email_service.send_email(to, subject, message)
        
        return jsonify(result)

    @api_bp.route('/list_reminders', methods=['GET'])
    def list_reminders():
        """List all scheduled reminders"""
        result = reminder_service.list_reminders()
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify({"error": result["error"]}), 500

    @api_bp.route('/cancel_reminder', methods=['POST'])
    def cancel_reminder():
        """Cancel a scheduled reminder"""
        data = request.json
        reminder_id = data.get('reminder_id', '')
        
        if not reminder_id:
            return jsonify({"error": "reminder_id is required"}), 400
        
        result = reminder_service.cancel_reminder(reminder_id)
        if result["success"]:
            return jsonify({"response": f"✅ {result['message']}"})
        else:
            return jsonify({"error": result["error"]}), 500

    return api_bp