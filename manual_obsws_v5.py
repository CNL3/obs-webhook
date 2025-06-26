import json
import websocket
import threading
import time

# WebSocket settings
HOST = "localhost"
PORT = 4460
URL = f"ws://{HOST}:{PORT}"

# Message ID counter
message_id = 1

def on_message(ws, message):
    global message_id
    print("📩 Message from OBS:", message)
    data = json.loads(message)

    # When handshake response is received (op 0), send Identify
    if data.get("op") == 0:
        identify = {
            "op": 1,
            "d": {
                "rpcVersion": 1,
                "eventSubscriptions": 0  # Change to 1 or more if you want events
            }
        }
        ws.send(json.dumps(identify))

    # Optional: after Identify is successful (op 2), send a test request like GetVersion
    if data.get("op") == 2:
        test_request = {
            "op": 6,
            "d": {
                "requestType": "GetVersion",
                "requestId": f"req-{message_id}"
            }
        }
        ws.send(json.dumps(test_request))
        message_id += 1

def on_error(ws, error):
    print("❌ WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("🔌 WebSocket closed:", close_status_code, close_msg)

def on_open(ws):
    print("✅ Connected to OBS WebSocket")

def main():
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        URL,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ws.close()

if __name__ == "__main__":
    main()
