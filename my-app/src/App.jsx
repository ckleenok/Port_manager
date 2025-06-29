import { useState } from "react";
import axios from "axios";
import { supabase } from "./supabaseClient";

export default function App() {
  const [ticker, setTicker] = useState("");
  const [results, setResults] = useState([]);

  const handleAddTicker = async () => {
    if (!ticker) return;
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    try {
      const res = await axios.post(`${apiUrl}/api/analyze`, {
        tickers: [ticker]
      });
      setResults(prev => [...prev, ...res.data.results]);
      setTicker("");
    } catch (err) {
      alert("API 호출 실패: " + err.message);
    }
  };

  const saveResults = async () => {
    for (const row of results) {
      await supabase.from("results").insert([row]);
    }
    alert("저장 완료!");
  };

  const handleRemove = (idx) => {
    setResults(results.filter((_, i) => i !== idx));
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>Stock Analyzer</h1>
      <div style={{ marginBottom: 16 }}>
        <input
          value={ticker}
          onChange={e => setTicker(e.target.value)}
          placeholder="Enter Ticker"
        />
        <button onClick={handleAddTicker} style={{ marginLeft: 8 }}>Add Ticker</button>
        <button onClick={saveResults} style={{ marginLeft: 8 }}>Save Results</button>
      </div>
      <table border="1" cellPadding="6" cellSpacing="0" style={{ width: "100%", background: "#222", color: "#fff" }}>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Company Name</th>
            <th>Current Price</th>
            <th>MACD</th>
            <th>BB Position</th>
            <th>Action</th>
            <th>Delete</th>
          </tr>
        </thead>
        <tbody>
          {results.map((row, idx) => (
            <tr key={row.ticker + idx}>
              <td>{row.ticker}</td>
              <td>{row.company_name}</td>
              <td>{row.current_price}</td>
              <td>{row.macd}</td>
              <td>{row.bb_position}</td>
              <td>{row.action}</td>
              <td><button onClick={() => handleRemove(idx)}>🗑️</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
