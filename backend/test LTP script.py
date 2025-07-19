import hmac
import hashlib
import base64
import json
import time
import requests

# Enter your API Key and Secret here. If you don't have one, you can generate it from the website.
key = "ba8f06e71568294c37c6f4adb8daf7af53b7cf869f144213"
secret = "57440a96f3d443acf0c95d07a83ff4342b204ef9f8563b3567cb1ac82f4ac633"

# python3
secret_bytes = bytes(secret, encoding='utf-8')

# Generating a timestamp
timeStamp = int(round(time.time() * 1000))

body = {
        "timestamp":timeStamp , # EPOCH timestamp in seconds
        "order": {
        "side": "sell", # buy OR sell
        "pair": "B-1000PEPE_USDT", # instrument.string
        "order_type": "market_order", # market_order OR limit_order 
        "stop_price": "0.2962", #numeric value
        "total_quantity": 600, #numerice value
        "leverage": 10, #numerice value
        "notification": "email_notification", # no_notification OR email_notification OR push_notification
        "time_in_force": "good_till_cancel", # good_till_cancel OR fill_or_kill OR immediate_or_cancel
        "hidden": False, # True or False
        "post_only": False, # True or False
        }
        }

json_body = json.dumps(body, separators = (',', ':'))

signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

url = "https://api.coindcx.com/exchange/v1/derivatives/futures/orders/create"

headers = {
    'Content-Type': 'application/json',
    'X-AUTH-APIKEY': key,
    'X-AUTH-SIGNATURE': signature
}

response = requests.post(url, data = json_body, headers = headers)
data = response.json()
print(data)