from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import websockets
import json
import os
import random
import string
import datetime
import subprocess
import platform
import webbrowser
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Config
OBS_URI = os.getenv("OBS_URI", "ws://localhost:4460")
EXPECTED_API_KEY = os.getenv("EXPECTED_API_KEY", "default_fallback_key")

# Utility functions
def generate_guest_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_room_name():
    today = datetime.date.today().strftime("%Y%m%d")
    return f"room{today}"

def start_obs_virtual_cam():
    try:
        if platform.system() == "Windows":
            subprocess.Popen([
                r"C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
                "--startvirtualcam"
            ])
        else:
            subprocess.Popen(["obs", "--startvirtualcam"])
        print("📸 OBS Virtual Camera starting...")
        time.sleep(2)
    except Exception as e:
        print("❌ Failed to start OBS Virtual Cam:", e)

def launch_obs_push_link(room_name, push_id="OBSFeed"):
    url = f"https://vdo.ninja/?room={room_name}&push={push_id}&webcam"
    print("🌐 Launching OBS Feed Push URL:", url)
    webbrowser.open(url)

async def update_obs_browser_source(guest_id, input_name, room_name):
    view_url = f"https://vdo.ninja/?room={room_name}&view={guest_id}&solo"
    print(f"🔗 Sending view URL to OBS for {input_name}: {view_url}")

    payload = {
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

    print(f"🌐 Connecting to OBS WebSocket at: {OBS_URI}")

    try:
        async with websockets.connect(OBS_URI) as websocket:
            await websocket.send(json.dumps({
                "op": 1,
                "d": {
                    "rpcVersion": 1
                }
            }))
            print("🔐 Sent Identify payload")

            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                if data.get("op") == 2:
                    print("✅ Successfully identified with OBS")
                    break
                else:
                    print(f"ℹ️ Waiting for Identify: {data}")

            await websocket.send(json.dumps(payload))
            print(f"📤 Payload sent to OBS:\n{json.dumps(payload, indent=2)}")

            while True:
                response_raw = await websocket.recv()
                response = json.loads(response_raw)
                if response.get("op") == 7 and response["d"].get("requestId") == payload["d"]["requestId"]:
                    print(f"✅ OBS confirmed update:\n{json.dumps(response, indent=2)}")
                    break
                else:
                    print(f"🔄 OBS intermediate response:\n{json.dumps(response, indent=2)}")

    except Exception as e:
        print(f"🚫 WebSocket error: {e}")

@app.route("/trigger", methods=["GET"])
def trigger_obs():
    api_key = request.args.get("api_key")
    source_name = request.args.get("source", "VOICE FOSTER")

    if api_key != EXPECTED_API_KEY:
        print("🔒 Unauthorized access attempt")
        return jsonify({"error": "Unauthorized"}), 401

    guest_id = generate_guest_id()
    room_name = generate_room_name()
    print(f"🆕 Generated Guest ID: {guest_id} for source {source_name} in room {room_name}")
    asyncio.run(update_obs_browser_source(guest_id, source_name, room_name))
    start_obs_virtual_cam()
    launch_obs_push_link(room_name)
    return jsonify({"status": "success", "guest_id": guest_id})

@app.route("/form")
def form_foster():
    room = generate_room_name()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Join Your Interview</title>
      <style>
        body {{
          font-family: sans-serif;
          font-size: 2.5rem;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 100vh;
          margin: 0;
          padding: 2rem;
          text-align: center;
        }}
        button {{
          padding: 0.5rem 1.5rem;
          font-size: 2rem;
          cursor: pointer;
        }}
        #result {{
          margin-top: 2rem;
          font-size: 2rem;
        }}
      </style>
    </head>
    <body>
      <h2>🎤 You’re Ready to Join the Interview</h2>
      <p>Click the button below to get your private broadcast link and send it to the studio.</p>
      <form id="generateLinkForm">
        <button type="submit">Generate Interview Link</button>
      </form>
      <p id="result"></p>

      <script>
        const room = "{room}";
        document.getElementById("generateLinkForm").addEventListener("submit", function(e) {{
          e.preventDefault();
          fetch("/trigger?api_key=cnl3_secret_2025&source=VOICE%20FOSTER")
            .then(response => response.json())
            .then(data => {{
              if (data.status === "success") {{
                const pushLink = `https://vdo.ninja/?room=${{room}}&push=${{data.guest_id}}`;
                document.getElementById("result").innerHTML = `
                  ✅ You're live-ready!<br>
                  <a href="${{pushLink}}" target="_blank">${{pushLink}}</a>
                `;
              }} else {{
                document.getElementById("result").innerText = `⚠️ Error: ${{JSON.stringify(data)}}`;
              }}
            }})
            .catch(function(err) {{
              document.getElementById("result").innerText = `❌ Request failed: ${{err}}`;
            }});
        }});
      </script>
    </body>
    </html>
    """

@app.route("/form-jeff")
def form_jeff():
    room = generate_room_name()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Jeff's Interview Entry</title>
      <style>
        body {{
          font-family: sans-serif;
          font-size: 2.5rem;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 100vh;
          margin: 0;
          padding: 2rem;
          text-align: center;
        }}
        button {{
          padding: 0.5rem 1.5rem;
          font-size: 2rem;
          cursor: pointer;
        }}
        #result {{
          margin-top: 2rem;
          font-size: 2rem;
        }}
      </style>
    </head>
    <body>
      <h2>🎙️ Jeff — Your Interview Link</h2>
      <p>Click below to enter the studio as co-host.</p>
      <form id="generateLinkForm">
        <button type="submit">Get My Interview Link</button>
      </form>
      <p id="result"></p>

      <script>
        const room = "{room}";
        document.getElementById("generateLinkForm").addEventListener("submit", function(e) {{
          e.preventDefault();
          fetch("/trigger?api_key=cnl3_secret_2025&source=VOICE%20JEFF")
            .then(response => response.json())
            .then(data => {{
              if (data.status === "success") {{
                const pushLink = `https://vdo.ninja/?room=${{room}}&push=${{data.guest_id}}`;
                document.getElementById("result").innerHTML = `
                  🎧 Link ready for Jeff:<br>
                  <a href="${{pushLink}}" target="_blank">${{pushLink}}</a>
                `;
              }} else {{
                document.getElementById("result").innerText = `⚠️ Error: ${{JSON.stringify(data)}}`;
              }}
            }})
            .catch(function(err) {{
              document.getElementById("result").innerText = `❌ Request failed: ${{err}}`;
            }});
        }});
      </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
