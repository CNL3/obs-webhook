from flask import Flask, request, jsonify
import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from .env
OBS_HOST = os.getenv("OBS_HOST", "localhost")
OBS_PORT = int(os.getenv("OBS_PORT", "4455"))
BROWSER_SOURCE_NAME = os.getenv("SOURCE_NAME", "FOSTER NINJA")
EXPECTED_API_KEY = os.getenv("API_KEY", "default_fallback_key")

# Async function to send command to OBS
async def update_obs_browser_source(guest_id):
    url = f"https://vdo.ninja/?view={guest_id}&solo"
    payload = {
        "op": 6,
        "d": {
            "requestType": "SetInputSettings",
            "requestId": f"set-browser-source-{guest_id}",
            "requestData": {
                "inputName": BROWSER_SOURCE_NAME,
                "inputSettings": {
                    "url": url
                },
                "overlay": False
            }
        }
    }

    uri = f"ws://{OBS_HOST}:{OBS_PORT}"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(payload))
            response = await websocket.recv()
            print(f"OBS Response: {response}")
    except Exception as e:
        print(f"WebSocket error: {e}")

# Route for GET /trigger
@app.route("/trigger", methods=["GET"])
def trigger():
    api_key = request.args.get("api_key")
    guest_id = request.args.get("guest_id")

    if api_key != EXPECTED_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    if not guest_id:
        return jsonify({"error": "Missing guest_id"}), 400

    asyncio.run(update_obs_browser_source(guest_id))
    return jsonify({"status": "success", "guest_id": guest_id})

# Start Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
