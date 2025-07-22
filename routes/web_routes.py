from flask import Blueprint

web_bp = Blueprint('web', __name__)

@web_bp.route("/")
def index():
    """Main web interface"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart AI Agent</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
        }
        button {
            padding: 15px 25px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #45a049;
        }
        #response {
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 8px;
            min-height: 200px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .examples {
            margin: 20px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Smart AI Agent</h1>
        <p style="text-align: center;">AI-powered SMS, Email & Reminder Assistant</p>
        
        <div class="input-group">
            <input type="text" id="command" placeholder="Try: 'Text John saying hello' or 'Email john@example.com saying meeting at 3pm'" />
            <button onclick="sendCommand()">Send</button>
        </div>
        
        <div class="examples">
            <strong>📱 SMS Examples:</strong><br>
            • "Text 8136414177 saying hey how are you"<br>
            • "Text John and Mary saying the meeting moved to 3pm"<br><br>
            
            <strong>📧 Email Examples:</strong><br>
            • "Email john@example.com saying the meeting is at 3pm"<br>
            • "Email john@example.com and mary@example.com saying hello everyone"<br><br>
            
            <strong>⏰ Reminder Examples:</strong><br>
            • "Remind me to call John in 30 minutes"<br>
            • "Set a reminder to pick up groceries at 5pm"
        </div>
        
        <div id="response">🎯 Ready to send professional messages, emails & reminders! Enter a command above to get started.</div>
    </div>

    <script>
        function sendCommand() {
            const input = document.getElementById('command');
            const output = document.getElementById('response');
            const userText = input.value.trim();

            if (!userText) {
                output.textContent = "⚠️ Please enter a command.";
                return;
            }

            output.textContent = "Processing with AI...";

            fetch("/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: userText })
            })
            .then(res => res.json())
            .then(data => {
                output.textContent = "✅ " + (data.response || "Done!");
                input.value = "";
            })
            .catch(err => {
                output.textContent = "❌ Error: " + err.message;
            });
        }

        document.getElementById('command').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
    </script>
</body>
</html>
'''
