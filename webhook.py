from dotenv import load_dotenv
load_dotenv()
import os
import json
import logging
from flask import Flask, request, jsonify
import urllib.request
from urllib.error import URLError, HTTPError
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# DeepSeek API endpoint and key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(f"Loaded API Key: {DEEPSEEK_API_KEY}")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Update if needed

if not DEEPSEEK_API_KEY:
    logger.error("DeepSeek API key is missing! Make sure to set it in your environment variables.")

def call_deepseek_api(message, image_url=None):
    """Call the DeepSeek API with the user message and optional image URL."""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are Medora, a medical assistant chatbot. Provide medical information, symptom guidance, and general healthcare advice, but always remind users to consult a doctor."},
            {"role": "user", "content": message}
        ],
        "max_tokens": 1000
    }

    if image_url:
        payload["messages"][1]["content"] = [
            {"type": "text", "text": message},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(DEEPSEEK_API_URL, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            logger.debug(f"DeepSeek API response: {result}")

            response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return response_text if response_text else "Sorry, I couldn't generate a response."

    except HTTPError as e:
        logger.exception(f"HTTP Error: {e.code} {e.reason}")
        return f"Error connecting to DeepSeek API: {e.code}"

    except URLError as e:
        logger.exception(f"URL Error: {e.reason}")
        return "Network issue while connecting to DeepSeek API. Please try again."

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return "An unexpected error occurred. Please try again."

def process_deepseek_in_background(message, image_url=None):
    """Run DeepSeek API call in a background thread."""
    response_text = call_deepseek_api(message, image_url)
    # Here, you can save the result to a database, message queue, or another system to notify the user later.
    logger.info(f"Background task completed. Response: {response_text}")

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles webhook requests from Dialogflow."""
    try:
        # Get the incoming request data from Dialogflow
        data = request.get_json()
        logger.debug(f"Received Dialogflow request: {json.dumps(data, indent=2)}")

        user_message = data.get("queryResult", {}).get("queryText", "")
        
        # Start the DeepSeek API call in a background thread
        thread = Thread(target=process_deepseek_in_background, args=(user_message,))
        thread.start()

        # Send an immediate response to Dialogflow
        return jsonify({
            "fulfillmentText": "Thank you for your query! We are processing your request."
        })

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return jsonify({"fulfillmentText": "An error occurred while processing your request."})

@app.route("/test", methods=["GET"])
def test_api():
    """Endpoint to check if the webhook is running."""
    return jsonify({"status": "running", "message": "Webhook server is operational"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
