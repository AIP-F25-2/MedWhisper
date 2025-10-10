import { useEffect, useRef, useState } from "react";
import "./app.css";

export default function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi! I’m Med-Whisper. Ask a clinical question. (Info only—no diagnosis.)" }
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [typing, setTyping] = useState("");
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
    setTyping("");

    try {
      // Streaming support: fallback to normal fetch if not streaming
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender: "web-user", message: text })
      });
      // If backend supports streaming, use response.body
      if (res.body && res.body.getReader) {
        const reader = res.body.getReader();
        let botText = "";
        const decoder = new TextDecoder();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          botText += decoder.decode(value);
          // Always show only clean text
          let cleanText = botText;
          if (cleanText.trim().startsWith("{")) {
            try {
              const parsed = JSON.parse(cleanText);
              if (parsed && typeof parsed === "object" && parsed.text) {
                cleanText = parsed.text;
              }
            } catch {
              // Not JSON, use as is
            }
          }
          setTyping(cleanText);
        }
        // Final clean up for display
        let finalText = botText;
        if (finalText.trim().startsWith("{")) {
          try {
            const parsed = JSON.parse(finalText);
            if (parsed && typeof parsed === "object" && parsed.text) {
              finalText = parsed.text;
            }
          } catch {
            // Not JSON, use as is
          }
        }
        setMessages((m) => [...m, { from: "bot", text: finalText }]);
        setTyping("");
      } else {
        // Fallback: normal JSON response
        const data = await res.json();
        // Use the new backend format: { text: reply }
        let reply = "";
        if (typeof data?.text === "string") {
          reply = data.text;
        } else if (typeof data === "string") {
          reply = data;
        } else {
          reply = "Sorry, I couldn’t answer that.";
        }
        setMessages((m) => [...m, { from: "bot", text: reply }]);
      }
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", text: "Sorry, I couldn’t reach the server." }]);
    } finally {
      setBusy(false);
      setTyping("");
    }
  }

  return (
    <div className="app-bg">
      <div className="chat-header">
        <h1>PulseAI Chatbot</h1>
      </div>
      <div className="chat-container">
        <div ref={boxRef} className="messages-box">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.from} fade-in`}>
              <div className="avatar">
                {m.from === "bot" ? (
                  <span role="img" aria-label="Bot">🤖</span>
                ) : (
                  <span role="img" aria-label="User">🧑</span>
                )}
              </div>
              <div className="bubble">{m.text}</div>
            </div>
          ))}
          {typing && (
            <div className="message bot fade-in">
              <div className="avatar">
                <span role="img" aria-label="Bot">🤖</span>
              </div>
              <div className="bubble">{typing}<span className="typing-cursor">|</span></div>
            </div>
          )}
        </div>
        <div className="note">
          This chatbot is for informational and educational purposes only. It does not provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical concerns.
        </div>
        <form onSubmit={send} className="chat-input">
          <button type="button" className="icon-btn" tabIndex={-1} title="Voice input (coming soon)" disabled>
            <span role="img" aria-label="Microphone">🎤</span>
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={busy ? "Thinking..." : "Type your question"}
            disabled={busy}
          />
          <button type="button" className="icon-btn" tabIndex={-1} title="Emoji picker (coming soon)" disabled>
            <span role="img" aria-label="Emoji">😊</span>
          </button>
          <button type="submit" className="send-btn" disabled={busy}>
            {busy ? "..." : "Send"}
          </button>
        </form>
        <div className="quick-replies">
          {['What are the symptoms of flu?', 'How to prevent COVID-19?', 'What is a healthy diet?', 'When should I see a doctor?'].map((q, idx) => (
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
    </div>
  );
}
