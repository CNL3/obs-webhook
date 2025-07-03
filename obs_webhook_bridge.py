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
