from flask import Flask, request, jsonify
from flask_cors import CORS
from copy_logic import (
    start_copying_session, stop_copying_session,
    get_order_log, get_copier_positions_full,
    get_leads_with_aum, get_realised_pnl, is_active
)
from ltp_store import get_ltp_map

app = Flask(__name__)
CORS(app)

@app.route("/api/start-copy", methods=["POST"])
def start_copy():
    try:
        data = request.json
        success = start_copying_session(
            data["lead_id"], data["copier_key"], data["copier_secret"],
            data["copier_capital"], data["copier_key"][:6],
            data.get("reverse", False)
        )
        return jsonify({"status": "ok" if success else "error"})
    except Exception as e:
        print(f"Start copy error: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/api/stop-copy", methods=["POST"])
def stop_copy():
    stop_copying_session(request.json["copier_key"][:6])
    return jsonify({"status": "stopped"})

@app.route("/api/order-log", methods=["POST"])
def get_orders():
    key = request.json["copier_key"]
    cid = key[:6]
    return jsonify({
        "orders": get_order_log(cid),
        "pnl": get_realised_pnl(cid)
    })

@app.route("/api/copier-positions-full", methods=["POST"])
def copier_positions_full():
    try:
        key, secret = request.json["copier_key"], request.json["copier_secret"]
        return jsonify(get_copier_positions_full(key, secret))
    except:
        return jsonify([])

@app.route("/api/leads", methods=["GET"])
def leads():
    return jsonify(get_leads_with_aum())

@app.route("/api/ltp", methods=["GET"])
def ltp():
    return jsonify(get_ltp_map())

@app.route("/api/is-active", methods=["POST"])
def active():
    return jsonify({ "active": is_active(request.json["copier_key"]) })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned port or fallback to 5000
    app.run(host="0.0.0.0", port=port, debug=False)

