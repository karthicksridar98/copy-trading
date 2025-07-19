import hmac, hashlib, json, time, requests, threading
from math import floor
from functools import lru_cache
from ltp_store import get_ltp
from traders import LEAD_TRADERS

copiers = {}
order_logs = {}

POSITION_URL = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions"
ORDER_URL = "https://api.coindcx.com/exchange/v1/derivatives/futures/orders/create"
WALLET_URL = "https://api.coindcx.com/exchange/v1/derivatives/futures/wallets"

@lru_cache(maxsize=128)
def get_quantity_increment(pair):
    try:
        url = f"https://api.coindcx.com/exchange/v1/derivatives/futures/data/instrument?pair={pair}&margin_currency_short_name=USDT"
        data = requests.get(url).json()
        return float(data["instrument"]["quantity_increment"])
    except:
        return 1.0

def sign_request(body, secret):
    json_body = json.dumps(body, separators=(',', ':'))
    signature = hmac.new(secret.encode(), json_body.encode(), hashlib.sha256).hexdigest()
    return json_body, signature

def post_signed(url, body, key, secret):
    json_body, signature = sign_request(body, secret)
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': key,
        'X-AUTH-SIGNATURE': signature
    }
    return requests.post(url, data=json_body, headers=headers)

def get_wallet_balance(key, secret):
    try:
        ts = int(time.time() * 1000)
        body = { "timestamp": ts }
        json_body, sig = sign_request(body, secret)
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': key,
            'X-AUTH-SIGNATURE': sig
        }
        res = requests.get(WALLET_URL, data=json_body, headers=headers).json()
        for w in res:
            if w["currency_short_name"] == "USDT":
                return float(w["balance"]) + float(w["locked_balance"])
    except:
        return None

def get_positions(key, secret):
    body = {
        "timestamp": int(time.time() * 1000),
        "page": "1",
        "size": "50",
        "margin_currency_short_name": ["USDT"]
    }
    try:
        res = post_signed(POSITION_URL, body, key, secret)
        return res.json()
    except:
        return []

def extract_positions_map(positions):
    return {p["pair"]: float(p["active_pos"]) for p in positions}

def place_market_order(api_key, api_secret, pair, side, qty, copier_id):
    step = get_quantity_increment(pair)
    qty = floor(abs(qty) / step) * step
    if qty == 0:
        return
    body = {
        "timestamp": int(time.time() * 1000),
        "order": {
            "side": side,
            "pair": pair,
            "order_type": "market_order",
            "total_quantity": qty,
            "leverage": 10,
            "notification": "email_notification",
            "time_in_force": "good_till_cancel",
            "hidden": False,
            "post_only": False
        }
    }
    try:
        response = post_signed(ORDER_URL, body, api_key, api_secret)
        data = response.json()

        # Fix here: handle list response
        if isinstance(data, list) and len(data) > 0:
            order_info = data[0]
        else:
            order_info = {}

        order_id = order_info.get("id", "unknown")
        executed_price = float(order_info.get("price", 0.0))

        if copier_id not in order_logs:
            order_logs[copier_id] = []

        order_logs[copier_id].append({
            "order_id": order_id,
            "symbol": pair,
            "side": side,
            "qty": qty,  
            "price": executed_price,
            "timestamp": int(time.time())
        })

        print(f"✅ Order stored: {order_id} | {side.upper()} {qty} {pair} @ {executed_price}")

    except Exception as e:
        print(f"❌ Error storing order log for copier {copier_id}: {e}")

def start_copying_session(lead_id, copier_key, copier_secret, capital, copier_id, reverse=False):
    if copier_id in copiers:
        return False
    lead = LEAD_TRADERS.get(lead_id)
    if not lead:
        return False
    lead_key, lead_secret = lead["api_key"], lead["api_secret"]
    lead_wallet = get_wallet_balance(lead_key, lead_secret)
    if not lead_wallet or lead_wallet <= 0:
        return False
    scaling = capital / lead_wallet
    copiers[copier_id] = {
        "lead_id": lead_id,
        "copier_key": copier_key,
        "copier_secret": copier_secret,
        "capital": capital,
        "scaling_factor": scaling,
        "reverse": reverse
    }
    LEAD_TRADERS[lead_id]["aum"] += capital

    def sync_loop():
        last = extract_positions_map(get_positions(lead_key, lead_secret))
        for symbol, qty in last.items():
            action = "sell" if (qty > 0 and reverse) or (qty < 0 and not reverse) else "buy"
            place_market_order(copier_key, copier_secret, symbol, action, qty * scaling, copier_id)
        while copier_id in copiers:
            time.sleep(1)
            curr = extract_positions_map(get_positions(lead_key, lead_secret))
            for symbol in set(curr) | set(last):
                diff = curr.get(symbol, 0) - last.get(symbol, 0)
                if abs(diff) > 0.0001:
                    action = "sell" if (diff > 0 and reverse) or (diff < 0 and not reverse) else "buy"
                    place_market_order(copier_key, copier_secret, symbol, action, diff * scaling, copier_id)
            last = curr

    threading.Thread(target=sync_loop).start()
    return True

def stop_copying_session(copier_id):
    if copier_id in copiers:
        lead_id = copiers[copier_id]["lead_id"]
        LEAD_TRADERS[lead_id]["aum"] -= copiers[copier_id]["capital"]
        del copiers[copier_id]

def get_order_log(copier_id):
    return order_logs.get(copier_id, [])

def get_realised_pnl(copier_id):
    orders = order_logs.get(copier_id, [])
    buy_total = sum(o["qty"] * o["price"] for o in orders if o["side"] == "buy")
    sell_total = sum(o["qty"] * o["price"] for o in orders if o["side"] == "sell")
    return round(sell_total - buy_total, 6)

def get_copier_positions_full(key, secret):
    try:
        pos = get_positions(key, secret)
    except:
        return []
    result = []
    for p in pos:
        qty = float(p["active_pos"])
        if abs(qty) < 0.0001:
            continue
        pair = p["pair"]
        result.append({
            "pair": pair,
            "side": "LONG" if qty > 0 else "SHORT",
            "leverage": p.get("leverage", 0),
            "qty": qty,
            "entry_price": p.get("avg_price", 0),
            "ltp": get_ltp(pair),
            "position_size": round(abs(qty) * get_ltp(pair), 2),
            "margin": round(p.get("locked_user_margin", 0), 2),
            "margin_type": p.get("margin_type") or "Isolated"
        })
    return result

def get_leads_with_aum():
    leads = []
    for id, info in LEAD_TRADERS.items():
        wallet = get_wallet_balance(info["api_key"], info["api_secret"]) or 0
        copier_total = sum(c["capital"] for cid, c in copiers.items() if c["lead_id"] == id)
        leads.append({
            "id": id,
            "name": info["name"],
            "aum": round(wallet + copier_total, 2)
        })
    return leads

def is_active(copier_key):
    return copier_key[:6] in copiers
