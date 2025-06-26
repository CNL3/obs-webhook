from flask import Flask, request, jsonify
from flask_cors import CORS
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
CORS(app)

# Configuration
OBS_HOST = os.getenv("OBS_HOST", "localhost")
OBS_PORT = int(os.getenv("OBS_PORT", "4460"))
BROWSER_SOURCE_NAME = os.getenv("SOURCE_NAME", "VOICE FOSTER")
EXPECTED_API_KEY = os.getenv("API_KEY", "default_fallback_key")

def generate_guest_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Update OBS browser source with guest view URL
async def update_obs_browser_source(guest_id):
    view_url = f"https://vdo.ninja/?view={guest_id}&solo"
    print(f"🔗 Sending view URL to OBS: {view_url}")

    payload = {
        "op": 6,
        "d": {
            "requestType": "SetInputSettings",
            "requestId": f"set-browser-source-{guest_id}",
            "requestData": {
                "inputName": BROWSER_SOURCE_NAME,
                "inputSettings": {
                    "url": view_url
                },
                "overlay": False
            }
        }
    }

    if OBS_HOST.startswith("ws://") or OBS_HOST.startswith("wss://"):
        uri = OBS_HOST
    else:
        uri = f"ws://{OBS_HOST}:{OBS_PORT}"

    print(f"🌐 Connecting to OBS WebSocket at: {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(payload))
            print(f"📤 Payload sent to OBS:\n{json.dumps(payload, indent=2)}")
            response = await websocket.recv()
            print(f"✅ OBS Response: {response}")
    except Exception as e:
        print(f"🚫 WebSocket error: {e}")

# Simple form page for generating the push/view link
@app.route("/form")
def form_page():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Join Your Interview</title></head>
    <body style="font-family: sans-serif; padding: 2rem;">
      <h2>🎤 You’re Ready to Join the Interview</h2>
      <p>Click the button below to get your private broadcast link and send it to the studio.</p>
      <form id="generateLinkForm">
        <button type="submit" style="padding: 0.5rem 1rem;">Generate Interview Link</button>
      </form>
      <p id="result" style="margin-top: 1rem;"></p>

      <script>
        document.getElementById("generateLinkForm").addEventListener("submit", function(e) {
          e.preventDefault();
          fetch("/trigger?api_key=cnl3_secret_2025")
            .then(response => response.json())
            .then(data => {
              if (data.status === "success") {
                const pushLink = "https://vdo.ninja/?push=" + data.guest_id;
                document.getElementById("result").innerHTML = `
                  ✅ You're live-ready!<br>
                  <a href="${pushLink}" target="_blank">${pushLink}</a>
                `;
              } else {
                document.getElementById("result").innerText = "⚠️ Error: " + JSON.stringify(data);
              }
            })
            .catch(function(err) {
              document.getElementById("result").innerText = "❌ Request failed: " + err;
            });
        });
      </script>
    </body>
    </html>
    """

# API endpoint for generating guest ID and updating OBS
@app.route("/trigger", methods=["GET"])
def trigger_obs():
    api_key = request.args.get("api_key")

    if api_key != EXPECTED_API_KEY:
        print("🔒 Unauthorized access attempt")
        return jsonify({"error": "Unauthorized"}), 401

    guest_id = generate_guest_id()
    print(f"🆕 Generated Guest ID: {guest_id}")
    asyncio.run(update_obs_browser_source(guest_id))
    return jsonify({"status": "success", "guest_id": guest_id})
