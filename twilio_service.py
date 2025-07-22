from typing import Dict, Any

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

class TwilioService:
    """Twilio SMS service"""
    
    def __init__(self, account_sid: str, auth_token: str, phone_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = phone_number
        self.client = None
        
        if TWILIO_AVAILABLE and account_sid and auth_token:
            try:
                self.client = Client(account_sid, auth_token)
                print("✅ Twilio client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Twilio client: {e}")
        else:
            print("⚠️ Twilio not configured or library missing")
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        if not self.client:
            return {"success": False, "error": "Twilio client not initialized"}
        
        if not self.from_number:
            return {"success": False, "error": "Twilio phone number not configured"}
        
        try:
            message_response = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            
            return {
                "success": True,
                "message_sid": message_response.sid,
                "status": message_response.status,
                "to": to,
                "from": self.from_number,
                "body": message
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to send SMS: {str(e)}"}
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Twilio account information"""
        if not self.client:
            return {"error": "Twilio client not initialized"}
        
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            return {
                "success": True,
                "account_sid": account.sid,
                "friendly_name": account.friendly_name,
                "status": account.status,
                "type": account.type
            }
        except Exception as e:
            return {"error": str(e)}