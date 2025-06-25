from flask import Flask, request, jsonify
import asyncio
import websockets
import json
import os
import random
import string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from .env or Render envVars
OBS_HOST = os.getenv("OBS_HOST", "localhost")
OBS_PORT = int(os.getenv("OBS_PORT", "4455"))
BROWSER_SOURCE_NAME = os.getenv("BROWSER_SOURCE_NAME", "FOSTER NINJA")
EXPECTED_API_KEY = os.getenv("EXPECTED_API_KEY", "default_fallback_key")

# Helper to generate a unique guest ID
def generate_guest_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

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

# API route for triggering OBS source update manually
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

# HTML form route to submit guest ID manually
@app.route("/form")
def obs_form():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Trigger OBS</title></head>
    <body>
      <h2>Trigger OBS.Ninja Source</h2>
      <form id="obsTriggerForm">
        <label for="guestId">Guest ID:</label>
        <input type="text" id="guestId" name="guestId" required><br><br>
        <button type="submit">Trigger OBS Update</button>
      </form>
      <p id="status"></p>
      <script>
        document.getElementById("obsTriggerForm").addEventListener("submit", function(e) {
          e.preventDefault();
          const guestId = document.getElementById("guestId").value.trim();
          const apiKey = "cnl3_secret_2025";
          const url = `/trigger?guest_id=${encodeURIComponent(guestId)}&api_key=${apiKey}`;
          fetch(url)
            .then(response => response.json())
            .then(data => {
              document.getElementById("status").innerText = `✅ Triggered: ${data.status}`;
            })
            .catch(error => {
              document.getElementById("status").innerText = `❌ Error: ${error}`;
            });
        });
      </script>
    </body>
    </html>
    """

# Interview endpoint: generate link, push to OBS, and return the link to user
@app.route("/interview", methods=["GET"])
def interview():
    guest_id = generate_guest_id()
    try:
        asyncio.run(update_obs_browser_source(guest_id))
    except Exception as e:
        return jsonify({"error": f"OBS error: {str(e)}"}), 500

    guest_url = f"https://vdo.ninja/?view={guest_id}&solo"
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Your Interview Link</title></head>
    <body>
        <h2>🎤 You're Ready to Join the Interview</h2>
        <p>Click below to open your live video feed in OBS.Ninja:</p>
        <a href="{guest_url}" target="_blank">{guest_url}</a>
        <p>This link has already been pushed to OBS for your appearance.</p>
    </body>
    </html>
    """

# Note: No app.run() — Gunicorn handles this in production
