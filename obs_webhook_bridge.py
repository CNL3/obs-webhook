from flask import Flask, request, jsonify
import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from .env or Render envVars
OBS_HOST = os.getenv("OBS_HOST", "localhost")
OBS_PORT = int(os.getenv("OBS_PORT", "4460"))  # Updated port
BROWSER_SOURCE_NAME = os.getenv("BROWSER_SOURCE_NAME", "VOICE FOSTER")  # Updated source name
EXPECTED_API_KEY = os.getenv("EXPECTED_API_KEY", "default_fallback_key")

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

# API route for triggering OBS source update
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

# HTML form route to submit guest ID
@app.route("/form")
def obs_form():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Join the Interview</title></head>
    <body style="font-family: sans-serif; padding: 2rem;">
      <h2>🎤 You're Ready to Join the Interview</h2>
      <p>Enter your name or ID:</p>
      <form id="obsTriggerForm">
        <input type="text" id="guestId" name="guestId" required style="padding: 0.5rem; width: 300px;"><br><br>
        <button type="submit" style="padding: 0.5rem 1rem;">Generate Interview Link</button>
      </form>
      <p id="status" style="margin-top: 1rem;"></p>
      <script>
        document.getElementById("obsTriggerForm").addEventListener("submit", function(e) {
          e.preventDefault();
          const guestId = document.getElementById("guestId").value.trim();
          const apiKey = "cnl3_secret_2025";
          const url = `/trigger?guest_id=${encodeURIComponent(guestId)}&api_key=${apiKey}`;
          fetch(url)
            .then(response => response.json())
            .then(data => {
              if (data.status === "success") {
                const ninjaLink = `https://vdo.ninja/?view=${guestId}&solo`;
                document.getElementById("status").innerHTML = `
                  ✅ Link generated!<br>
                  <a href="${ninjaLink}" target="_blank">${ninjaLink}</a>
                `;
              } else {
                document.getElementById("status").innerText = `⚠️ Error: ${JSON.stringify(data)}`;
              }
            })
            .catch(error => {
              document.getElementById("status").innerText = `❌ Error: ${error}`;
            });
        });
      </script>
    </body>
    </html>
    """
