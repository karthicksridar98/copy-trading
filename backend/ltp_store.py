import json
import os

LTP_FILE = "ltp.json"

def update_ltp(pair, price):
    ltp_map = {}
    if os.path.exists(LTP_FILE):
        with open(LTP_FILE, "r") as f:
            try:
                ltp_map = json.load(f)
            except:
                pass
    ltp_map[pair] = price
    with open(LTP_FILE, "w") as f:
        json.dump(ltp_map, f)

def get_ltp(pair):
    if not os.path.exists(LTP_FILE):
        return 0
    try:
        with open(LTP_FILE, "r") as f:
            ltp_map = json.load(f)
            return float(ltp_map.get(pair, 0))
    except:
        return 0

def get_ltp_map():
    if not os.path.exists(LTP_FILE):
        return {}
    try:
        with open(LTP_FILE, "r") as f:
            return json.load(f)
    except:
        return {}
