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
        // Only display the main reply text, ignore raw/extra info
        let reply = "";
        if (Array.isArray(data?.replies) && data.replies.length) {
          reply = data.replies[0];
        } else if (typeof data === "string") {
          // If reply looks like JSON, try to extract the text value
          try {
            const parsed = JSON.parse(data);
            if (parsed && typeof parsed === "object" && parsed.text) {
              reply = parsed.text;
            } else {
              reply = data;
            }
          } catch {
            reply = data;
          }
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
    <div className="chat-container">
      <h1>PulseAI Chatbot</h1>
      <div ref={boxRef} className="messages-box">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.from}`}>
            <div className="bubble">{m.text}</div>
          </div>
        ))}
        {typing && (
          <div className="message bot">
            <div className="bubble">{typing}<span className="typing-cursor">|</span></div>
          </div>
        )}
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
