import { useEffect, useRef, useState } from "react";
import "./app.css";

export default function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi! I'm Med-Whisper. Ask a clinical question, upload an image, or use voice input! (Info only—no diagnosis.)" }
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [typing, setTyping] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const boxRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (boxRef.current) {
      boxRef.current.scrollTop = boxRef.current.scrollHeight;
    }
  }, [messages]);

  async function send(e) {
    e?.preventDefault();
    const text = input.trim();
    if ((!text && !selectedImage) || busy) return;
    
    setInput("");
    setBusy(true);
    setTyping("");

    // Handle image upload
    if (selectedImage) {
      const reader = new FileReader();
      reader.onload = async () => {
        const imageData = reader.result;
        setMessages((m) => [...m, { 
          from: "user", 
          text: text || "Uploaded an image", 
          image: imageData 
        }]);

        try {
          const res = await fetch("/api/chat/image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
              sender: "web-user", 
              message: text || "What can you tell me about this image?",
              image_data: imageData
            })
          });
          const data = await res.json();
          setMessages((m) => [...m, { from: "bot", text: data.text || "Sorry, I couldn't process the image." }]);
        } catch (err) {
          setMessages((m) => [...m, { from: "bot", text: "Sorry, I couldn't process the image." }]);
        } finally {
          setBusy(false);
          setSelectedImage(null);
        }
      };
      reader.readAsDataURL(selectedImage);
      return;
    }

    // Handle text message
    setMessages((m) => [...m, { from: "user", text }]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender: "web-user", message: text })
      });
      
      const data = await res.json();
      let reply = "";
      if (typeof data?.text === "string") {
        reply = data.text;
      } else if (typeof data === "string") {
        reply = data;
      } else {
        reply = "Sorry, I couldn't answer that.";
      }
      setMessages((m) => [...m, { from: "bot", text: reply }]);
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", text: "Sorry, I couldn't reach the server." }]);
    } finally {
      setBusy(false);
      setTyping("");
    }
  }

  // Voice recording functions
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        await sendVoiceMessage(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err) {
      alert("Microphone access denied or not available.");
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
    }
  }

  async function sendVoiceMessage(audioBlob) {
    setBusy(true);
    setMessages((m) => [...m, { from: "user", text: "🎤 Voice message sent..." }]);

    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'voice.wav');
      formData.append('sender', 'web-user');

      const res = await fetch("/api/chat/voice", {
        method: "POST",
        body: formData
      });
      
      const data = await res.json();
      setMessages((m) => [...m, { from: "bot", text: data.text || "Sorry, I couldn't process your voice message." }]);
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", text: "Sorry, I couldn't process your voice message." }]);
    } finally {
      setBusy(false);
    }
  }

  // Image handling functions
  function handleImageSelect(e) {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
    }
  }

  function removeSelectedImage() {
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  function handleVoiceClick() {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }

  return (
    <div className="app-bg">
      <div className="chat-header">
        <h1>PulseAI Chatbot</h1>
        <div className="header-features">
          <span className="feature-indicator">💬 Text</span>
          <span className="feature-indicator">🖼️ Images</span>
          <span className="feature-indicator">🎤 Voice</span>
        </div>
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
                    <img src={m.image} alt="Uploaded" style={{maxWidth: '200px', borderRadius: '8px', marginBottom: '8px'}} />
                  </div>
                )}
                <div className="message-text">{m.text}</div>
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
        
        {/* Image Preview */}
        {selectedImage && (
          <div className="image-preview">
            <img src={URL.createObjectURL(selectedImage)} alt="Selected" style={{maxHeight: '100px', borderRadius: '8px'}} />
            <button onClick={removeSelectedImage} className="remove-image-btn">❌</button>
            <span className="image-name">{selectedImage.name}</span>
          </div>
        )}
        
        <div className="note">
          This chatbot is for informational and educational purposes only. It does not provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical concerns.
        </div>
        
        <form onSubmit={send} className="chat-input">
          {/* Voice button */}
          <button 
            type="button" 
            className={`icon-btn voice-btn ${isRecording ? 'recording' : ''}`}
            onClick={handleVoiceClick}
            title={isRecording ? "Stop recording" : "Start voice recording"}
            disabled={busy && !isRecording}
          >
            <span role="img" aria-label="Microphone">
              {isRecording ? "🔴" : "🎤"}
            </span>
          </button>
          
          {/* Image upload button */}
          <button 
            type="button" 
            className="icon-btn" 
            onClick={() => fileInputRef.current?.click()}
            title="Upload image"
            disabled={busy}
          >
            <span role="img" aria-label="Image">🖼️</span>
          </button>
          
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              busy ? "Processing..." : 
              selectedImage ? "Describe your image (optional)" : 
              isRecording ? "Recording..." : 
              "Type your question, upload image, or use voice"
            }
            disabled={busy}
          />
          
          <button type="submit" className="send-btn" disabled={busy && !isRecording}>
            {busy ? "..." : selectedImage ? "Send Image" : "Send"}
          </button>
          
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            style={{display: 'none'}}
          />
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