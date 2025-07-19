import React, { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [copierApiKey, setCopierApiKey] = useState("");
  const [copierApiSecret, setCopierApiSecret] = useState("");
  const [capital, setCapital] = useState("");
  const [selectedLead, setSelectedLead] = useState(null);
  const [copying, setCopying] = useState(false);
  const [orders, setOrders] = useState([]);
  const [positions, setPositions] = useState([]);
  const [aumList, setAumList] = useState([]);
  const [ltpMap, setLtpMap] = useState({});
  const [realisedPnl, setRealisedPnl] = useState(0);
  const [reverseCopy, setReverseCopy] = useState(false);
  const [apiError, setApiError] = useState(false);

  useEffect(() => {
    fetchAUM();
    checkIfActive();

    const interval = setInterval(() => {
      if (copying) {
        fetchOrders();
        fetchPositions();
        fetchLTPs();
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [copying]);

  const fetchAUM = async () => {
    try {
      const res = await axios.get(`${process.env.REACT_APP_API_URL}/api/leads`);
      setAumList(res.data);
    } catch (err) {
      console.error("Failed to fetch AUM", err);
    }
  };

  const checkIfActive = async () => {
    try {
      if (!copierApiKey) return;
      const res = await axios.post(`${process.env.REACT_APP_API_URL}/api/is-active`, {
        copier_key: copierApiKey,
      });
      if (res.data.active) {
        setCopying(true);
      }
    } catch (err) {
      console.log("Session check failed");
    }
  };

  const fetchOrders = async () => {
    try {
      const res = await axios.post(`${process.env.REACT_APP_API_URL}/api/order-log`, {
        copier_key: copierApiKey,
        copier_secret: copierApiSecret,
      });
      setOrders(res.data.orders || []);
      setRealisedPnl(res.data.pnl || 0);
    } catch {
      setApiError(true);
    }
  };

  const fetchPositions = async () => {
    try {
      const res = await axios.post(`${process.env.REACT_APP_API_URL}/api/copier-positions-full`, {
        copier_key: copierApiKey,
        copier_secret: copierApiSecret,
      });
      setPositions(res.data);
      setApiError(false);
    } catch {
      setApiError(true);
    }
  };

  const fetchLTPs = async () => {
    try {
      const res = await axios.get(`${process.env.REACT_APP_API_URL}/api/ltp`);
      setLtpMap(res.data);
    } catch (err) {
      console.log("LTP fetch failed");
    }
  };

  const handleCopy = async () => {
    try {
      const res = await axios.post(`${process.env.REACT_APP_API_URL}/api/start-copy`, {
        lead_id: selectedLead.id,
        copier_key: copierApiKey,
        copier_secret: copierApiSecret,
        copier_capital: parseFloat(capital),
        reverse: reverseCopy,
      });
      if (res.data.status === "ok") {
        setCopying(true);
      } else {
        alert("Failed to start copy session.");
      }
    } catch (err) {
      alert("Failed to start copy session.");
    }
  };

  const handleStop = async () => {
    await axios.post(`${process.env.REACT_APP_API_URL}/api/stop-copy`, {
      copier_key: copierApiKey,
      copier_secret: copierApiSecret,
    });
    setCopying(false);
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial", paddingBottom: 120 }}>
      <h2>🚀 Crypto Copy Trading</h2>

      {!copying ? (
        <>
          {!selectedLead ? (
            <>
              <h4>Select a Lead Trader</h4>
              {aumList.map((lead) => (
                <div
                  key={lead.id}
                  style={{
                    border: "1px solid #ddd",
                    padding: 10,
                    marginBottom: 10,
                  }}
                >
                  <b>{lead.name}</b>
                  <p>AUM: ${lead.aum}</p>
                  <button onClick={() => setSelectedLead(lead)}>
                    Copy this Trader
                  </button>
                </div>
              ))}
            </>
          ) : (
            <>
              <h4>
                You're copying: <b>{selectedLead.name}</b>
              </h4>
              <p>AUM: ${selectedLead.aum}</p>
              <br />
              <input
                type="text"
                placeholder="Your API Key"
                value={copierApiKey}
                onChange={(e) => setCopierApiKey(e.target.value)}
                style={{ width: "300px", display: "block", marginBottom: 10 }}
              />
              <input
                type="text"
                placeholder="Your API Secret"
                value={copierApiSecret}
                onChange={(e) => setCopierApiSecret(e.target.value)}
                style={{ width: "300px", display: "block", marginBottom: 10 }}
              />
              <input
                type="number"
                placeholder="Capital to deploy (USDT)"
                value={capital}
                onChange={(e) => setCapital(e.target.value)}
                style={{ width: "200px", display: "block", marginBottom: 10 }}
              />
              <label>
                <input
                  type="checkbox"
                  checked={reverseCopy}
                  onChange={(e) => setReverseCopy(e.target.checked)}
                  style={{ marginRight: 6 }}
                />
                Reverse Copy (mirror trades)
              </label>
              <br />
              <button onClick={handleCopy} style={{ marginTop: 10 }}>
                Start Copy Trading
              </button>
              <br />
              <button
                onClick={() => setSelectedLead(null)}
                style={{ marginTop: 10 }}
              >
                🔙 Back to Traders List
              </button>
            </>
          )}
        </>
      ) : (
        <>
          <button
            onClick={handleStop}
            style={{ background: "red", color: "white", marginBottom: 10 }}
          >
            🔴 Stop Copy Trading
          </button>

          {apiError && (
            <div style={{ color: "red" }}>
              ⚠️ Invalid API keys or error fetching data.
            </div>
          )}

          <h3>📈 Live Positions</h3>
          <table border="1" cellPadding="6">
            <thead>
              <tr>
                <th>Pair</th>
                <th>Side</th>
                <th>Leverage</th>
                <th>Qty</th>
                <th>Entry Price</th>
                <th>LTP</th>
                <th>Position Size</th>
                <th>Margin Used</th>
                <th>Margin Type</th>
              </tr>
            </thead>
            <tbody>
              {positions
                .filter((pos) => Math.abs(pos.qty) > 0)
                .map((pos) => {
                  const ltp = ltpMap[pos.pair] || 0;
                  const size = (Math.abs(pos.qty) * ltp).toFixed(2);
                  const marginType = pos.margin_type || "Isolated";
                  return (
                    <tr key={pos.pair}>
                      <td>{pos.pair}</td>
                      <td>{pos.side}</td>
                      <td>{pos.leverage}</td>
                      <td>{pos.qty}</td>
                      <td>{pos.entry_price}</td>
                      <td>{ltp}</td>
                      <td>{size}</td>
                      <td>{pos.margin}</td>
                      <td>{marginType}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>

          <h3>💰 Realised PnL: ${realisedPnl}</h3>

          <h3>📜 Orders Log</h3>
          <ul>
            {orders.map((o, idx) => (
              <li key={idx}>
                [{o.order_id}] {o.side.toUpperCase()} {o.qty} {o.symbol} @{" "}
                {o.price}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

export default App;
