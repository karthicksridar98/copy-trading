import socketio
import hmac
import hashlib
import json
import asyncio
from datetime import datetime
from ltp_store import update_ltp

# === CONFIG ===
socketEndpoint = 'wss://stream.coindcx.com'
key = "ba8f06e71568294c37c6f4adb8daf7af53b7cf869f144213"
secret = "57440a96f3d443acf0c95d07a83ff4342b204ef9f8563b3567cb1ac82f4ac633"

sio = socketio.AsyncClient()

def get_auth_payload(channel_name):
    body = {"channel": channel_name}
    json_body = json.dumps(body, separators=(',', ':'))
    signature = hmac.new(secret.encode(), json_body.encode(), hashlib.sha256).hexdigest()
    return {
        "channelName": channel_name,
        "authSignature": signature,
        "apiKey": key
    }

# === PING ===
async def ping_task():
    while True:
        await asyncio.sleep(25)
        try:
            await sio.emit('ping', {'data': 'Ping message'})
        except Exception as e:
            print(f"❌ Ping failed: {e}")

# === CONNECT EVENT ===
@sio.event
async def connect():
    print("✅ Connected to CoinDCX")
    print("🕐 Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    await sio.emit("join", get_auth_payload("coindcx"))
    await sio.emit("join", {"channelName": "currentPrices@futures@rt"})

# === HANDLE LTP EVENT ===
@sio.on('currentPrices@futures#update')
async def on_current_prices(response_raw):
    try:
        response = json.loads(response_raw)
        prices = response.get("prices", {})
        for pair, data in prices.items():
            if "mp" in data:
                update_ltp(pair, float(data["mp"]))
    except Exception as e:
        print("❌ Error parsing LTP socket response")
        print("Raw:", response_raw)
        print("Error:", e)


# === ERROR HANDLING ===
@sio.event
async def connect_error(data):
    print("❌ Connection failed:", data)

@sio.event
async def disconnect():
    print("🔌 Disconnected from CoinDCX")

# === MAIN LOOP ===
async def main():
    try:
        await sio.connect(socketEndpoint, transports=["websocket"])
        asyncio.create_task(ping_task())
        await sio.wait()
    except Exception as e:
        print("❌ Socket error:", e)

if __name__ == '__main__':
    asyncio.run(main())
