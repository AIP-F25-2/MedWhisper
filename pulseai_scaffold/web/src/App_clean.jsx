import { useEffect, useRef, useState } from "react";
import "./App.css";

export default function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi! I'm Med-Whisper. Ask a clinical question! (Info only—no diagnosis.)" }
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => {
    if (boxRef.current) {
      boxRef.current.scrollTop = boxRef.current.scrollHeight;
    }
  }, [messages]);

  async function send(e) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { from: "user", text }]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender: "web-user", message: text })
      });
      const data = await res.json();
      setMessages((m) => [...m, { from: "bot", text: data.text || "No response" }]);
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", text: "Error: Could not reach server" }]);
    } finally {
      setBusy(false);
    }
  }

  const quickReplies = [
    "What are the symptoms of flu?",
    "How to prevent COVID-19?",
    "What is a healthy diet?",
    "When should I see a doctor?"
  ];

  return (
    <div className="app">
      <div className="header">
        <h1>🩺 Med-Whisper</h1>
        <p>Your AI Medical Assistant (For informational purposes only)</p>
      </div>
      
      <div className="chat-box" ref={boxRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.from}`}>
            {msg.text}
          </div>
        ))}
      </div>

      <form onSubmit={send} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a medical question..."
          disabled={busy}
          className="input-field"
        />
        <button type="submit" disabled={busy} className="send-btn">
          {busy ? "..." : "Send"}
        </button>
      </form>

      <div className="quick-replies">
        {quickReplies.map((q, idx) => (
          <button
            key={idx}
            className="quick-reply-btn"
            type="button"
            onClick={() => setInput(q)}
            disabled={busy}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}