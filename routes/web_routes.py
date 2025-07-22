from flask import Blueprint, render_template_string

web_bp = Blueprint('web', __name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Smart AI Agent+ (Reminders)</title>
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#007bff">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="AI Agent+">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {
      box-sizing: border-box;
      -webkit-tap-highlight-color: transparent;
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: linear-gradient(to bottom, #2f2f2f 0%, #f9fafb 100%);
      margin: 0;
      padding: 1rem;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      color: #212529;
      padding-top: env(safe-area-inset-top);
      padding-bottom: env(safe-area-inset-bottom);
    }

    .container {
      width: 100%;
      max-width: 600px;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      margin-top: 2rem;
    }

    h1 {
      font-size: 2.2rem;
      margin: 0;
      text-align: center;
      font-weight: 700;
      color: white;
      letter-spacing: -0.025em;
      text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .subtitle {
      font-size: 1rem;
      color: rgba(255,255,255,0.9);
      text-align: center;
      margin-bottom: 2rem;
      font-weight: 400;
      line-height: 1.5;
    }

    .feature-badge {
      background: rgba(255,255,255,0.2);
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 500;
      display: inline-block;
      margin: 0 auto 1rem;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,0.3);
    }

    .input-container {
      background: rgba(255,255,255,0.95);
      border-radius: 16px;
      padding: 1.5rem;
      border: 1px solid rgba(255,255,255,0.2);
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      backdrop-filter: blur(10px);
    }

    .input-group {
      display: flex;
      gap: 0.75rem;
      align-items: center;
    }

    input {
      flex: 1;
      padding: 16px 20px;
      font-size: 16px;
      border: 2px solid #e9ecef;
      border-radius: 12px;
      background: white;
      outline: none;
      color: #212529;
      font-family: 'Inter', sans-serif;
      transition: all 0.3s ease;
    }

    input:focus {
      border-color: #007bff;
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
      transform: translateY(-1px);
    }

    input::placeholder {
      color: #6c757d;
      font-weight: 400;
    }

    button {
      padding: 16px 28px;
      font-size: 16px;
      font-weight: 600;
      border: none;
      border-radius: 12px;
      background: linear-gradient(45deg, #007bff, #0056b3);
      color: white;
      cursor: pointer;
      min-width: 90px;
      transition: all 0.3s ease;
      font-family: 'Inter', sans-serif;
      box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
    }

    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 123, 255, 0.4);
    }

    button:active {
      transform: translateY(0);
    }

    .response-container {
      background: rgba(255,255,255,0.95);
      border-radius: 16px;
      padding: 1.5rem;
      border: 1px solid rgba(255,255,255,0.2);
      min-height: 300px;
      flex: 1;
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      backdrop-filter: blur(10px);
    }

    .response-text {
      font-size: 14px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-wrap: break-word;
      color: #495057;
      font-family: 'Inter', sans-serif;
      font-weight: 400;
    }

    .voice-controls {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 1rem;
      margin-top: 1rem;
    }

    .mic-button {
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: linear-gradient(45deg, #dc3545, #c82333);
      border: none;
      color: white;
      font-size: 28px;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
      box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4);
    }

    .mic-button:hover {
      transform: scale(1.05);
      box-shadow: 0 8px 24px rgba(220, 53, 69, 0.5);
    }

    .mic-button.recording {
      background: linear-gradient(45deg, #28a745, #20c997);
      animation: pulse 1.5s infinite;
      box-shadow: 0 6px 20px rgba(40, 167, 69, 0.5);
    }

    .mic-button.recording::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 100%;
      height: 100%;
      background: rgba(255,255,255,0.3);
      border-radius: 50%;
      transform: translate(-50%, -50%) scale(0);
      animation: ripple 1.5s infinite;
    }

    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.05); }
      100% { transform: scale(1); }
    }

    @keyframes ripple {
      0% { transform: translate(-50%, -50%) scale(0); opacity: 1; }
      100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
    }

    .voice-status {
      font-size: 0.9rem;
      color: #212529;
      text-align: center;
      margin-top: 0.75rem;
      min-height: 22px;
      font-weight: 500;
      text-shadow: none;
    }

    @media (max-width: 480px) {
      .container {
        max-width: 100%;
        margin-top: 1rem;
        gap: 1rem;
      }
      
      body {
        padding: 0.75rem;
      }
      
      h1 {
        font-size: 1.8rem;
      }
      
      .subtitle {
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
      }
      
      .mic-button {
        width: 64px;
        height: 64px;
        font-size: 24px;
      }
      
      .input-container, .response-container {
        padding: 1.25rem;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Smart AI Agent+</h1>
    <div class="subtitle">Speak naturally - AI handles SMS, Email & Reminders professionally</div>
    <div class="feature-badge">✨ Multi-Recipient Messages, Emails & Smart Reminders</div>
    
    <div class="input-container">
      <div class="input-group">
        <input type="text" id="command" placeholder="Try: 'Text John saying hello' or 'Remind me to call mom in 30 minutes'" />
        <button onclick="sendCommand()">Send</button>
      </div>
    </div>

    <div class="response-container">
      <div class="response-text" id="response">🎯 Ready to send professional messages, emails & reminders! 

📱 SMS Examples:
• "Text 8136414177 saying hey how are you"
• "Text John and Mary saying the meeting moved to 3pm"

📧 Email Examples:
• "Email john@example.com saying the meeting is at 3pm"
• "Email john@example.com and mary@example.com saying hello everyone"

⏰ Reminder Examples:
• "Remind me to call John in 30 minutes"
• "Set a reminder to pick up groceries at 5pm"
• "Text me in 1 hour to check on the project"
• "Remind me tomorrow at 9am to submit the report"

🔄 Mixed Examples:
• "Send a message to 8136414177 and john@example.com saying hello"

Use the microphone button below or type your command.</div>
    </div>

    <div class="voice-controls">
      <button class="mic-button" id="micButton" onclick="toggleVoiceRecording()">
        🎤
      </button>
    </div>
    <div class="voice-status" id="voiceStatus"></div>
  </div>

  <script>
    let deferredPrompt;
    let recognition;
    let isRecording = false;
    let voiceSupported = false;

    function initSpeechRecognition() {
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 3;
        
        recognition.onstart = function() {
          isRecording = true;
          document.getElementById('micButton').classList.add('recording');
          document.getElementById('voiceStatus').textContent = '🎤 Listening... Speak naturally!';
          document.getElementById('command').placeholder = 'Listening...';
        };
        
        recognition.onresult = function(event) {
          let transcript = '';
          let isFinal = false;
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
              transcript += event.results[i][0].transcript;
              isFinal = true;
            } else {
              document.getElementById('command').value = event.results[i][0].transcript;
            }
          }
          
          if (isFinal) {
            document.getElementById('command').value = transcript.trim();
            document.getElementById('voiceStatus').textContent = `📝 Captured: "${transcript.trim()}"`;
            
            setTimeout(() => {
              document.getElementById('voiceStatus').textContent = 'Processing with AI...';
              sendCommand();
            }, 1500);
          }
        };
        
        recognition.onerror = function(event) {
          console.error('Speech recognition error:', event.error);
          document.getElementById('voiceStatus').textContent = '❌ Voice input error';
          stopRecording();
        };
        
        recognition.onend = function() {
          stopRecording();
        };
        
        voiceSupported = true;
        document.getElementById('voiceStatus').textContent = 'Tap microphone to speak your message or reminder';
      } else {
        document.getElementById('voiceStatus').textContent = '⚠️ Voice input not supported in this browser';
        document.getElementById('micButton').style.display = 'none';
      }
    }

    function toggleVoiceRecording() {
      if (!voiceSupported) return;
      
      if (isRecording) {
        recognition.stop();
      } else {
        try {
          document.getElementById('command').value = '';
          recognition.start();
        } catch (error) {
          console.error('Failed to start speech recognition:', error);
          document.getElementById('voiceStatus').textContent = '❌ Failed to start voice input';
        }
      }
    }

    function stopRecording() {
      isRecording = false;
      document.getElementById('micButton').classList.remove('recording');
      document.getElementById('command').placeholder = 'Try: "Text John saying hello" or "Remind me to call mom in 30 minutes"';
      
      if (document.getElementById('voiceStatus').textContent.includes('Listening')) {
        document.getElementById('voiceStatus').textContent = 'Tap microphone to speak your message or reminder';
      }
    }

    function sendCommand() {
      const input = document.getElementById('command');
      const output = document.getElementById('response');
      const userText = input.value.trim();

      if (!userText) {
        output.textContent = "⚠️ Please enter a command or use voice input.";
        return;
      }

      output.textContent = "Processing with AI and enhancing message...";

      fetch("/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userText })
      })
      .then(res => res.json())
      .then(data => {
        output.textContent = "✅ " + (data.response || "Done!") + "\\n\\n📋 Raw Response:\\n" + JSON.stringify(data.claude_output, null, 2);
        input.value = "";
        document.getElementById('voiceStatus').textContent = voiceSupported ? 'Tap microphone to speak your message or reminder' : '';
      })
      .catch(err => {
        output.textContent = "❌ Error: " + err.message;
        document.getElementById('voiceStatus').textContent = voiceSupported ? 'Tap microphone to speak your message or reminder' : '';
      });
    }

    document.getElementById('command').addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        sendCommand();
      }
    });

    window.addEventListener('load', initSpeechRecognition);
  </script>
</body>
</html>
"""

@web_bp.route("/")
def index():
    """Main web interface"""
    return render_template_string(HTML_TEMPLATE)
