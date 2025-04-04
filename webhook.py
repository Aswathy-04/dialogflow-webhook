from dotenv import load_dotenv
load_dotenv()
import os
import json
import logging
from flask import Flask, request, jsonify
import urllib.request
from urllib.error import URLError, HTTPError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# DeepSeek API endpoint and key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(f"Loaded API Key: {DEEPSEEK_API_KEY}")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

if not DEEPSEEK_API_KEY:
    logger.error("DeepSeek API key is missing! Make sure to set it in your environment variables.")

def call_deepseek_api(message, image_url=None):
    """Call the DeepSeek API synchronously and return the response immediately."""
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

            return response_text if response_text else "I'm sorry, I couldn't generate a response."

    except HTTPError as e:
        logger.exception(f"HTTP Error: {e.code} {e.reason}")
        return f"Error connecting to DeepSeek API: {e.code}"

    except URLError as e:
        logger.exception(f"URL Error: {e.reason}")
        return "Network issue while connecting to DeepSeek API. Please try again."

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return "An unexpected error occurred. Please try again."

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles webhook requests from Dialogflow and provides an instant, relevant response."""
    try:
        # Get user query from Dialogflow
        data = request.get_json()
        logger.debug(f"Received Dialogflow request: {json.dumps(data, indent=2)}")

        user_message = data.get("queryResult", {}).get("queryText", "")

        # Get the actual response from DeepSeek **before responding to Dialogflow**
        deepseek_response = call_deepseek_api(user_message)

        # Return **actual answer** to Dialogflow instantly
        return jsonify({
            "fulfillmentText": deepseek_response
        })

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return jsonify({"fulfillmentText": "An error occurred while processing your request."})

@app.route("/test", methods=["GET"])
def test_api():
    """Endpoint to check if the webhook is running."""
    return jsonify({"status": "running", "message": "Webhook server is operational"})

if __name__ == "__main__":
    # Dynamically set the port using environment variable or default to 3000 for local development
    port = int(os.environ.get("PORT", 3000))  # Defaults to 3000 if not set
    app.run(host="0.0.0.0", port=port, debug=True)
