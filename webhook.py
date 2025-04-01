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
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

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
            {"role": "system", "content": "You are Medora, a medical assistant chatbot."},
            {"role": "user", "content": message}
        ],
        "max_tokens": 1000
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(DEEPSEEK_API_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            logger.debug(f"DeepSeek API response: {result}")
            return result.get("choices", [{}])[0].get("message", {}).get("content", "Sorry, I couldn't generate a response.")
    except (HTTPError, URLError) as e:
        logger.exception("Error connecting to DeepSeek API")
        return "There was an issue connecting to the medical assistance service. Please try again."
    except Exception as e:
        logger.exception("Unexpected error")
        return "An unexpected error occurred. Please try again."

def async_deepseek_request(session_id, message):
    """Handles the DeepSeek API call asynchronously."""
    response_text = call_deepseek_api(message)
    logger.info(f"Background processing completed for session {session_id}: {response_text}")
    # TODO: Store response for session (e.g., in a database or cache) for retrieval later.

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles webhook requests from Dialogflow."""
    try:
        data = request.get_json()
        logger.debug(f"Received Dialogflow request: {json.dumps(data, indent=2)}")
        
        user_message = data.get("queryResult", {}).get("queryText", "")
        session_id = data.get("session", "unknown_session")

        # Start DeepSeek processing asynchronously
        thread = Thread(target=async_deepseek_request, args=(session_id, user_message))
        thread.start()

        # Send immediate response to Dialogflow
        return jsonify({
            "fulfillmentText": "Thank you for your query! We are processing your request."
        })
    except Exception as e:
        logger.exception("Error processing webhook request")
        return jsonify({"fulfillmentText": "An error occurred while processing your request."})

@app.route("/test", methods=["GET"])
def test_api():
    """Endpoint to check if the webhook is running."""
    return jsonify({"status": "running", "message": "Webhook server is operational"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
