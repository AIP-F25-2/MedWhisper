import { useEffect, useRef, useState } from "react";
import "./app.css";

export default function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi! I'm Med-Whisper. Ask a clinical question, send an image, or use voice input. (Info only—no diagnosis.)" }
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [typing, setTyping] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const boxRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const fileInputRef = useRef(null);

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
      const res = await fetch("http://127.0.0.1:8002/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender: "user", message: text })
      });
      
      const data = await res.json();
      const reply = data?.text || "Sorry, I couldn't answer that.";
      setMessages((m) => [...m, { from: "bot", text: reply }]);
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", text: "Sorry, I couldn’t reach the server." }]);
    } finally {
      setBusy(false);
      setTyping("");
    }
  }

  async function sendImage(file, message = "Please analyze this medical image") {
    if (!file || busy) return;
    setBusy(true);
    setMessages((m) => [...m, { from: "user", text: `📷 Image: ${message}`, image: URL.createObjectURL(file) }]);
    setTyping("");

    try {
      // Convert image to base64
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64Data = reader.result;
        
        const res = await fetch("http://127.0.0.1:8002/chat/image", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            sender: "user",
            message: message || "Analyze this medical image",
            image_data: base64Data
          })
        });
        
        const data = await res.json();
        let reply = data?.text || "Sorry, I couldn't analyze the image.";
        setMessages((m) => [...m, { from: "bot", text: reply }]);
        setBusy(false);
        setTyping("");
      };
      reader.readAsDataURL(file);
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", text: "Sorry, I couldn't process the image." }]);
      setBusy(false);
      setTyping("");
    }
  }

  async function startVoiceRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      const audioChunks = [];
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await sendVoice(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error starting recording:", err);
      alert("Could not access microphone. Please check permissions.");
    }
  }

  function stopVoiceRecording() {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }

  async function sendVoice(audioBlob) {
    setBusy(true);
    setMessages((m) => [...m, { from: "user", text: "🎤 Voice message..." }]);
    setTyping("");

    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'voice.wav');
      formData.append('sender', 'user');

      const res = await fetch("http://127.0.0.1:8002/chat/voice", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      let reply = data?.text || "Sorry, I couldn't process your voice message.";
      setMessages((m) => [...m, { from: "bot", text: reply }]);
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", text: "Sorry, I couldn't process your voice message." }]);
    } finally {
      setBusy(false);
      setTyping("");
    }
  }

  function handleImageUpload() {
    fileInputRef.current.click();
  }

  function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const message = "Please analyze this medical image";
      sendImage(file, message);
    } else if (file) {
      alert("Please select an image file.");
    }
    e.target.value = '';
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
              <div className="bubble">
                {m.image && (
                  <div className="message-image">
                    <img src={m.image} alt="Uploaded" style={{maxWidth: '200px', borderRadius: '8px'}} />
                  </div>
                )}
                {m.text}
              </div>
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
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept="image/*"
            onChange={handleFileSelect}
          />
          <button 
            type="button" 
            className={`icon-btn ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
            disabled={busy}
            title={isRecording ? "Stop recording" : "Start voice recording"}
          >
            <span role="img" aria-label="Microphone">🎤</span>
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={busy ? "Thinking..." : "Type your question"}
            disabled={busy}
          />
          <button 
            type="button" 
            className="icon-btn" 
            onClick={handleImageUpload}
            disabled={busy}
            title="Upload image"
          >
            <span role="img" aria-label="Camera">📷</span>
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
