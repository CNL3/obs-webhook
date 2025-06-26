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

# Config
OBS_HOST = os.getenv("OBS_HOST", "localhost")
OBS_PORT = int(os.getenv("OBS_PORT", "4460"))
EXPECTED_API_KEY = os.getenv("API_KEY", "default_fallback_key")
OBS_PASSWORD = os.getenv("OBS_PASSWORD", "")  # Optional password if OBS requires it

def generate_guest_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def update_obs_browser_source(guest_id, input_name):
    view_url = f"https://vdo.ninja/?view={guest_id}&solo"
    print(f"🔗 Sending view URL to OBS for {input_name}: {view_url}")

    identify_payload = {
        "op": 1,
        "d": {
            "rpcVersion": 1,
            "authentication": {
                "password": OBS_PASSWORD
            }
        }
    }

    set_input_payload = {
        "op": 6,
        "d": {
            "requestType": "SetInputSettings",
            "requestId": f"set-browser-source-{guest_id}",
            "requestData": {
                "inputName": input_name,
                "inputSettings": {
                    "url": view_url
                },
                "overlay": False
            }
        }
    }

    uri = OBS_HOST if OBS_HOST.startswith("ws") else f"ws://{OBS_HOST}:{OBS_PORT}"
    print(f"🌐 Connecting to OBS WebSocket at: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            # Step 1: Identify
            await websocket.send(json.dumps(identify_payload))
            print("🔐 Sent Identify payload")

            # Step 2: Wait for "Identified"
            while True:
                resp = await websocket.recv()
                response = json.loads(resp)
                if response.get("op") == 2:
                    print("✅ Successfully identified with OBS")
                    break
                else:
                    print(f"ℹ️ Waiting for 'Identified', got: {json.dumps(response, indent=2)}")

            # Step 3: Send SetInputSettings
            await websocket.send(json.dumps(set_input_payload))
            print(f"📤 Payload sent to OBS:\n{json.dumps(set_input_payload, indent=2)}")

            # Step 4: Await Confirmation
            while True:
                response_raw = await websocket.recv()
                response = json.loads(response_raw)
                if response.get("op") == 7 and response["d"].get("requestId", "").startswith("set-browser-source-"):
                    print(f"✅ OBS confirmed update:\n{json.dumps(response, indent=2)}")
                    break
                else:
                    print(f"ℹ️ Intermediate OBS message:\n{json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"🚫 WebSocket error: {e}")

@app.route("/form")
def form_foster():
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
          fetch("/trigger?api_key=cnl3_secret_2025&source=VOICE%20FOSTER")
            .then(response => response.json())
            .then(data => {
              if (data.status === "success") {
                const pushLink = `https://vdo.ninja/?push=${data.guest_id}`;
                document.getElementById("result").innerHTML = `
                  ✅ You're live-ready!<br>
                  <a href="${pushLink}" target="_blank">${pushLink}</a>
                `;
              } else {
                document.getElementById("result").innerText = `⚠️ Error: ${JSON.stringify(data)}`;
              }
            })
            .catch(function(err) {
              document.getElementById("result").innerText = `❌ Request failed: ${err}`;
            });
        });
      </script>
    </body>
    </html>
    """

@app.route("/form-jeff")
def form_jeff():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Jeff's Interview Entry</title></head>
    <body style="font-family: sans-serif; padding: 2rem;">
      <h2>🎙️ Jeff — Your Interview Link</h2>
      <p>Click below to enter the studio as co-host.</p>
      <form id="generateLinkForm">
        <button type="submit" style="padding: 0.5rem 1rem;">Get My Interview Link</button>
      </form>
      <p id="result" style="margin-top: 1rem;"></p>

      <script>
        document.getElementById("generateLinkForm").addEventListener("submit", function(e) {
          e.preventDefault();
          fetch("/trigger?api_key=cnl3_secret_2025&source=VOICE%20JEFF")
            .then(response => response.json())
            .then(data => {
              if (data.status === "success") {
                const pushLink = `https://vdo.ninja/?push=${data.guest_id}`;
                document.getElementById("result").innerHTML = `
                  🎧 Link ready for Jeff:<br>
                  <a href="${pushLink}" target="_blank">${pushLink}</a>
                `;
              } else {
                document.getElementById("result").innerText = `⚠️ Error: ${JSON.stringify(data)}`;
              }
            })
            .catch(function(err) {
              document.getElementById("result").innerText = `❌ Request failed: ${err}`;
            });
        });
      </script>
    </body>
    </html>
    """

@app.route("/trigger", methods=["GET"])
def trigger_obs():
    api_key = request.args.get("api_key")
    source_name = request.args.get("source", "VOICE FOSTER")  # fallback default

    if api_key != EXPECTED_API_KEY:
        print("🔒 Unauthorized access attempt")
        return jsonify({"error": "Unauthorized"}), 401

    guest_id = generate_guest_id()
    print(f"🆕 Generated Guest ID: {guest_id} for source {source_name}")
    asyncio.run(update_obs_browser_source(guest_id, source_name))
    return jsonify({"status": "success", "guest_id": guest_id})
