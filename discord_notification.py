import requests
from config import Config
from datetime import datetime
import json
import os

def notify_to_discord(message, error = None, image_path = None, type = 1):
        if type == 1:
            url = Config.FORM_SUBMISSION_WEBHOOK_URL
        else:
            url = Config.DISCORD_WEBHOOK_URL
        data = {
            "content": "✅ " + message if not error else "❌ " + message,
            "embeds": []
        }

        if error:
            data['embeds'].append({
                "title": " ❌ Error",
                "description": error,
                "color": 0xff0000,
                "timestamp": datetime.now().isoformat()
            })
    
        if image_path:
            requests.post(url, data={'payload_json': json.dumps(data)}, files={"file": open(image_path, "rb")})
            os.remove(image_path)
        else:
            requests.post(url, data={'payload_json': json.dumps(data)})


def notify_to_discord_with_failed_content(content, checks_failed, data, checks, type = 1):
            try:
                # Prepare the embed data
                contentdata = "🔍 Integrity check for URL automation" if type != 1 else "🔍 Integrity check for form automation"
                webhook_data = {
                    "content": contentdata,
                    "embeds": [{
                        "title": f"{'✅ Passed' if checks_failed == False else '❌ Failed'} Tests",
                        "color": 0x00ff00 if checks_failed == False else 0xff0000,
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "title": "URL Tested" if type == 1 else "Form Tested",
                        "description": data,
                        "color": 0x00ff00 if checks_failed == False else 0xff0000,
                        "timestamp": datetime.now().isoformat()
                    }
                    ]
                }
                for check in checks:
                    webhook_data["embeds"].append({
                        "title": "Test Result",
                        "description": check,
                        "color": 0x00ff00 if checks_failed == False else 0xff0000,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Create a temporary file with the content
                if checks_failed == True:
                    files = {
                        'file': ('content.html', content, 'text/html')
                    }
                else:
                    files = {}
                
                url = Config.FORM_SUBMISSION_WEBHOOK_URL if type == 1 else Config.DISCORD_WEBHOOK_URL
                response = requests.post(
                    url, 
                    data={'payload_json': json.dumps(webhook_data)},
                    files=files
                )
                response.raise_for_status()  # Raise exception for bad status codes
                print("Webhook sent successfully")
            except requests.exceptions.RequestException as e:
                print(f"Failed to send webhook: {e}")