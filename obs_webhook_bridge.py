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
EXPECTED_API_KEY = os.getenv("API_KEY", "default_fallback_key")

# Define available targets and their associated OBS browser source names
BROWSER_SOURCES = {
    "foster": "VOICE FOSTER",
    "jeff": "VOICE JEFF"
}

def generate_guest_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def update_obs_browser_source(source_name, guest_id):
    view_url = f"https://vdo.ninja/?view={guest_id}&solo"
    print(f"🔗 Sending view URL to OBS: {view_url} -> {source_name}")

    payload = {
        "op": 6,
        "d": {
            "requestType": "SetInputSettings",
            "requestId": f"set-{source_name.replace(' ', '-').lower()}-{guest_id}",
            "requestData": {
                "inputName": source_name,
                "inputSettings": {
                    "url": view_url,
                    "restartWhenActive": True
                },
                "overlay": False
            }
        }
    }

    uri = OBS_HOST if OBS_HOST.startswith("ws://") or OBS_HOST.startswith("wss://") else f"ws://{OBS_HOST}:{OBS_PORT}"
    print(f"🌐 Connecting to OBS WebSocket at: {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            hello = await websocket.recv()
            print(f"👋 OBS Hello: {hello}")
            await websocket.send(json.dumps({ "op": 1, "d": { "rpcVersion": 1 }}))
            await websocket.recv()  # acknowledge

            await websocket.send(json.dumps(payload))
            print(f"📤 Sent to OBS: {json.dumps(payload, indent=2)}")
            print(f"✅ OBS Response: {await websocket.recv()}")
    except Exception as e:
        print(f"🚫 WebSocket error: {e}")

@app.route("/form")
def form_page():
    target = request.args.get("target", "foster").lower()
    if target not in BROWSER_SOURCES:
        return f"❌ Invalid target '{target}'", 400

    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Join Your Interview</title></head>
    <body style="font-family: sans-serif; padding: 2rem;">
      <h2>🎤 Ready to Join as {target.capitalize()}</h2>
      <p>Click the button to generate your link and send it to the studio for {target.upper()}.</p>
      <form id="generateLinkForm">
        <button type="submit" style="padding: 0.5rem 1rem;">Generate Interview Link</button>
      </form>
      <p id="result" style="margin-top: 1rem;"></p>

      <script>
        document.getElementById("generateLinkForm").addEventListener("submit", function(e) {{
          e.preventDefault();
          fetch("/trigger?api_key=cnl3_secret_2025&target={target}")
            .then(response => response.json())
            .then(data => {{
              if (data.status === "success") {{
                const pushLink = `https://vdo.ninja/?push=${{data.guest_id}}`;
                document.getElementById("result").innerHTML = `
                  ✅ You're live-ready as {target.upper()}!<br>
                  <a href="${{pushLink}}" target="_blank">${{pushLink}}</a>
                `;
              }} else {{
                document.getElementById("result").innerText = `⚠️ Error: ${{JSON.stringify(data)}}`;
              }}
            }})
            .catch(err => {{
              document.getElementById("result").innerText = `❌ Request failed: ${err}`;
            }});
        }});
      </script>
    </body>
    </html>
    """

@app.route("/trigger", methods=["GET"])
def trigger_obs():
    api_key = request.args.get("api_key")
    target = request.args.get("target", "foster").lower()

    if api_key != EXPECTED_API_KEY:
        print("🔒 Unauthorized access")
        return jsonify({"error": "Unauthorized"}), 401

    if target not in BROWSER_SOURCES:
        print(f"⚠️ Unknown target: {target}")
        return jsonify({"error": f"Unknown target '{target}'"}), 400

    guest_id = generate_guest_id()
    print(f"🆕 Generated Guest ID for {target}: {guest_id}")
    asyncio.run(update_obs_browser_source(BROWSER_SOURCES[target], guest_id))
    return jsonify({"status": "success", "guest_id": guest_id})
