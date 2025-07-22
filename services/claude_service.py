import requests
import json
from typing import Dict, Any

class ClaudeService:
    """Claude AI service for message enhancement and command parsing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    
    def _call_claude(self, prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        """Make API call to Claude"""
        try:
            body = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1000,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }

            response = requests.post(self.base_url, headers=self.headers, data=json.dumps(body))
            response_json = response.json()
            
            if "content" in response_json:
                return {"success": True, "content": response_json["content"][0]["text"]}
            else:
                return {"success": False, "error": "Claude response missing content"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def enhance_message(self, message: str) -> str:
        """Enhance a message using Claude AI"""
        prompt = f"""
        You are a professional communication assistant. Enhance this message to be clear, 
        professional, and grammatically correct while preserving the original meaning:
        
        Original message: "{message}"
        
        Respond with ONLY the enhanced message, nothing else.
        """
        
        result = self._call_claude(prompt)
        if result["success"]:
            return result["content"].strip()
        else:
            print(f"Message enhancement failed: {result['error']}")
            return message
    
    def generate_email_subject(self, message: str) -> str:
        """Generate email subject using Claude AI"""
        prompt = f"""
        Generate a professional, concise email subject line for this message content. 
        The subject should be clear, specific, and under 50 characters.
        
        Message content: "{message}"
        
        Respond with ONLY the subject line, nothing else.
        """
        
        result = self._call_claude(prompt)
        if result["success"]:
            return result["content"].strip()
        else:
            return "Message from Smart AI Agent"
    
    def parse_command(self, prompt: str) -> Dict[str, Any]:
        """Parse user command into structured action"""
        instruction_prompt = """
        You are an intelligent assistant. Respond ONLY with valid JSON using one of the supported actions.

        Supported actions:
        - create_task, create_appointment, send_message, send_message_multi
        - send_email, send_email_multi, schedule_sms_reminder, schedule_email_reminder
        - log_conversation, enhance_message

        Response structure:
        {
          "action": "action_name",
          "title": "...",
          "due_date": "YYYY-MM-DDTHH:MM:SS",
          "reminder_time": "YYYY-MM-DDTHH:MM:SS",
          "recipient": "Name, phone number, or email",
          "recipients": ["Name1", "Name2"],
          "message": "Body of the message",
          "subject": "Email subject",
          "notes": "Optional details"
        }

        Only include fields relevant to the action. Do not add extra commentary.
        """
        
        full_prompt = f"{instruction_prompt}\n\nUser: {prompt}"
        result = self._call_claude(full_prompt)
        
        if result["success"]:
            try:
                return json.loads(result["content"])
            except json.JSONDecodeError:
                return {"error": "Failed to parse Claude response as JSON"}
        else:
            return {"error": result["error"]}