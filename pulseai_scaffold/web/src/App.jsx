import { useEffect, useRef, useState } from "react";
import "./app.css";  // import the new CSS

export default function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi! I’m Med-Whisper. Ask a clinical question. (Info only—no diagnosis.)" }
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
      const replies = Array.isArray(data?.replies) && data.replies.length ? data.replies : ["Sorry, I couldn’t answer that."];
      setMessages((m) => [...m, ...replies.map((t) => ({ from: "bot", text: t }))]);
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", text: "Sorry, I couldn’t reach the server." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat-container">
      <h1>PulseAI Chatbot</h1>
      <div ref={boxRef} className="messages-box">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.from}`}>
            <div className="bubble">{m.text}</div>
          </div>
        ))}
      </div>
      <div className="note">
        Educational use only. Not medical advice.
      </div>
      <form onSubmit={send} className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={busy ? "Thinking..." : "Type your question"}
          disabled={busy}
        />
        <button type="submit" disabled={busy}>
          {busy ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
