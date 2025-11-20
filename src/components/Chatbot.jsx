import React, { useState, useRef, useEffect, useCallback } from 'react';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hi! I'm MedWhisper AI Assistant. Ask me any clinical question. (This is for information only—not medical diagnosis.)",
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isUploadingAudio, setIsUploadingAudio] = useState(false);
  const [audioPermissionDenied, setAudioPermissionDenied] = useState(false);
  const [lastSeenMessageId, setLastSeenMessageId] = useState(1); // Track the last seen message
  const [position, setPosition] = useState({ 
    x: window.innerWidth - 400, // Position to show full chat window (380px width + margin)
    y: window.innerHeight - 620 // Position to show full chat window (600px height + margin)
  });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const chatContainerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const API_BASE = 'https://e66adf64e3a5.ngrok-free.app';
  const FALLBACK_API_BASE = 'http://localhost:8010'; // Fallback to local backend if direct connection fails
  const TEXT_ENDPOINT = '/qa';
  const VOICE_ENDPOINT = '/voice-qa';
  const DEFAULT_LANGUAGE = 'en';
  const DEFAULT_USER_ROLE = 'student';
  // Quick reply suggestions
  const quickReplies = [
    "What are the symptoms of flu?",
    "How to prevent COVID-19?",
    "What is a healthy diet?",
    "When should I see a doctor?",
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle drag functionality
  const handleMouseDown = (e) => {
    if (e.target.closest('button')) return; // Don't drag if clicking on buttons
    setIsDragging(true);
    const rect = chatContainerRef.current?.getBoundingClientRect();
    if (rect) {
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
    e.preventDefault();
  };

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    
    const newX = e.clientX - dragOffset.x;
    const newY = e.clientY - dragOffset.y;
    
    // Keep within viewport bounds - ensure full chat window is visible
    const maxX = window.innerWidth - 380; // Chat window width (380px)
    const maxY = window.innerHeight - 600; // Chat window height (600px)
    
    setPosition({
      x: Math.max(0, Math.min(newX, maxX)),
      y: Math.max(0, Math.min(newY, maxY)),
    });
  }, [isDragging, dragOffset]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Add global mouse event listeners for dragging
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragOffset, handleMouseMove, handleMouseUp]);

  // Handle window resize to keep chat window in bounds
  useEffect(() => {
    const handleResize = () => {
      const maxX = window.innerWidth - 380;
      const maxY = window.innerHeight - 600;
      
      setPosition(prev => ({
        x: Math.min(prev.x, maxX),
        y: Math.min(prev.y, maxY)
      }));
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const extractBotReply = (data) => {
    if (!data || typeof data !== 'object') return null;

    return (
      data?.rag?.response ||
      data?.rag?.answer ||
      data?.response ||
      data?.message ||
      data?.text?.response ||
      data?.text?.answer ||
      data?.text ||
      data?.transcript ||
      null
    );
  };

  const fetchTextResponse = async (baseUrl, question) => {
    const response = await fetch(`${baseUrl}${TEXT_ENDPOINT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        language: DEFAULT_LANGUAGE,
        patient_id: null,
        include_timeline: false,
        include_differential: false,
        user_role: DEFAULT_USER_ROLE,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Text API ${baseUrl}${TEXT_ENDPOINT} returned ${response.status}: ${errorText}`);
    }

    return response.json();
  };

  const uploadVoiceResponse = async (baseUrl, formData) => {
    const response = await fetch(`${baseUrl}${VOICE_ENDPOINT}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Voice API ${baseUrl}${VOICE_ENDPOINT} returned ${response.status}: ${errorText}`);
    }

    return response.json();
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      let data;
      let usedFallback = false;
      try {
        data = await fetchTextResponse(API_BASE, messageText);
      } catch (primaryError) {
        console.warn('Primary text API failed, switching to fallback:', primaryError);
        usedFallback = true;
        data = await fetchTextResponse(FALLBACK_API_BASE, messageText);
      }

      const botReply = extractBotReply(data);

      const botMessage = {
        id: Date.now() + 1,
        text: botReply || "Sorry, I couldn't process that question.",
        sender: 'bot',
        timestamp: new Date(),
      };

      if (usedFallback) {
        botMessage.meta = 'fallback';
      }

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);

      let errorText = 'Sorry, I am currently unable to respond. Please check your connection and try again.';

      if (error.message.includes('Unable to connect to any backend server')) {
        errorText = 'Backend server is not running. Please start the FastAPI backend on port 8010 or review README_Guide.md.';
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorText = 'Network error: Unable to connect to the server. Please check your internet connection and ensure the backend is running.';
      } else if (error.message.includes('CORS')) {
        errorText = 'Connection blocked. Please check your browser settings or try again.';
      } else if (error.message.includes('API ')) {
        errorText = `Server error: ${error.message}. Please ensure the backend server is running and try again.`;
      }

      const errorMessage = {
        id: Date.now() + 1,
        text: errorText,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const sendVoiceMessage = async (audioBlob) => {
    if (!audioBlob) return;

    const userVoiceMessage = {
      id: Date.now(),
      text: '🎤 Voice message sent.',
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userVoiceMessage]);
    setIsTyping(true);
    setIsUploadingAudio(true);

    const formData = new FormData();
    const voiceFile = new File([audioBlob], `voice-query-${Date.now()}.webm`, { type: audioBlob.type || 'audio/webm' });
    formData.append('file', voiceFile);
    formData.append('language', DEFAULT_LANGUAGE);
    formData.append('user_role', DEFAULT_USER_ROLE);
    formData.append('include_timeline', 'false');
    formData.append('include_differential', 'false');

    try {
      let response;
      let usedFallback = false;

      try {
        response = await uploadVoiceResponse(API_BASE, formData);
      } catch (primaryError) {
        console.warn('Primary voice API failed, switching to fallback:', primaryError);
        usedFallback = true;
        response = await uploadVoiceResponse(FALLBACK_API_BASE, formData);
      }

      const botReply = extractBotReply(response);

      const botMessage = {
        id: Date.now() + 1,
        text: botReply || "Sorry, I couldn't process that voice question.",
        sender: 'bot',
        timestamp: new Date(),
      };

      if (usedFallback) {
        botMessage.meta = 'fallback';
      }

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending voice message:', error);

      let errorText = 'Voice processing failed. Please try again or use text input.';

      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorText = 'Network error: Unable to upload audio. Please check your internet connection and ensure the backend is running.';
      } else if (error.message.includes('CORS')) {
        errorText = 'Voice connection blocked. Please check browser settings or try again.';
      } else if (error.message.includes('Voice API')) {
        errorText = `Voice server error: ${error.message}. See README_Guide.md for setup instructions.`;
      }

      const errorMessage = {
        id: Date.now() + 1,
        text: errorText,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
      setIsUploadingAudio(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };

  const handleQuickReply = (reply) => {
    sendMessage(reply);
  };


  const toggleChat = () => {
    const newIsOpen = !isOpen;
    setIsOpen(newIsOpen);
    
    // When opening the chat, mark all current messages as seen
    if (newIsOpen && messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      setLastSeenMessageId(latestMessage.id);
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const handleToggleRecording = async () => {
    if (isRecording && mediaRecorderRef.current) {
      setIsRecording(false);
      mediaRecorderRef.current.stop();
      return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const errorMessage = {
        id: Date.now(),
        text: 'Voice input is not supported in this browser. Please use a modern browser that supports microphone access.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        setIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
        mediaRecorderRef.current = null;

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];

        if (audioBlob.size > 0) {
          sendVoiceMessage(audioBlob);
        } else {
          console.warn('Recorded audio blob is empty.');
        }
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setAudioPermissionDenied(false);
    } catch (error) {
      console.error('Unable to access microphone:', error);
      setAudioPermissionDenied(true);
      const errorMessage = {
        id: Date.now(),
        text: 'Microphone access denied. Please enable permissions in your browser settings to use voice input.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stream?.getTracks?.().forEach((track) => track.stop());
        mediaRecorderRef.current = null;
      }
    };
  }, []);

  return (
    <div 
      ref={chatContainerRef}
      className="fixed z-50"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'default',
      }}
    >
      {/* Chat Window */}
      <div
        className={`mb-4 bg-white rounded-2xl shadow-2xl transition-all duration-300 transform ${
          isOpen 
            ? 'translate-x-0 translate-y-0 scale-100 opacity-100' 
            : 'translate-x-full translate-y-full scale-0 opacity-0'
        }`}
        style={{
          width: '380px',
          height: '600px',
          transformOrigin: 'bottom right',
        }}
        onMouseDown={handleMouseDown}
      >
        {/* Chat Header */}
        <div className="bg-gradient-to-r from-[#014A93] to-[#2B6FDF] text-white p-4 rounded-t-2xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-[#014A93]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                  />
                </svg>
              </div>
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></div>
            </div>
            <div>
              <h3 className="font-semibold text-lg">MedWhisper AI</h3>
              <p className="text-xs text-white/80">Online • Ready to help</p>
            </div>
          </div>
          <button
            onClick={toggleChat}
            className="text-white/80 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Messages Container */}
        <div className="h-[calc(100%-180px)] overflow-y-auto p-4 bg-gray-50">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`mb-4 flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                  message.sender === 'user'
                    ? 'bg-gradient-to-r from-[#014A93] to-[#2B6FDF] text-white rounded-br-none'
                    : 'bg-white text-gray-800 shadow-md rounded-bl-none'
                }`}
              >
                <p className="text-sm leading-relaxed">{message.text}</p>
                <p className={`text-xs mt-1 ${message.sender === 'user' ? 'text-white/70' : 'text-gray-500'}`}>
                  {formatTime(message.timestamp)}
                </p>
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start mb-4">
              <div className="bg-white text-gray-800 shadow-md rounded-2xl rounded-bl-none px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Replies */}
        {messages.length === 1 && !isTyping && !isUploadingAudio && (
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-2">Quick questions:</p>
            <div className="flex flex-wrap gap-2">
              {quickReplies.slice(0, 2).map((reply, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickReply(reply)}
                  className="text-xs px-3 py-1.5 bg-white border border-[#014A93]/30 text-[#014A93] rounded-full hover:bg-[#014A93] hover:text-white transition-colors"
                >
                  {reply}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-200 rounded-b-2xl">
          <form onSubmit={handleSubmit} className="flex gap-2 items-center">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-[#014A93] focus:border-transparent text-sm"
            />

            {/* Voice Button */}
            <button
              type="button"
              onClick={handleToggleRecording}
              disabled={isTyping || isUploadingAudio}
              aria-pressed={isRecording}
              className={`relative flex items-center justify-center p-2.5 rounded-full border transition-all ${
                isRecording
                  ? 'border-red-500 text-red-600 bg-red-50 animate-pulse'
                  : 'border-gray-300 text-[#014A93] hover:bg-[#014A93] hover:text-white'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={
                audioPermissionDenied
                  ? 'Microphone permission denied. Please enable microphone access.'
                  : isRecording
                    ? 'Stop recording'
                    : 'Start voice input'
              }
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isRecording ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 1a3 3 0 00-3 3v6a3 3 0 006 0V4a3 3 0 00-3-3zM19 10a7 7 0 01-14 0m7 7v6m-4 0h8"
                  />
                )}
              </svg>
              {isUploadingAudio && (
                <span className="absolute -bottom-2 text-[10px] uppercase tracking-wide text-[#014A93]">
                  Sending...
                </span>
              )}
            </button>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!inputMessage.trim() || isTyping || isUploadingAudio}
              className="bg-gradient-to-r from-[#014A93] to-[#2B6FDF] text-white p-2.5 rounded-full hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
          
        </div>
      </div>

      {/* Floating Chat Button */}
      <button
        onClick={toggleChat}
        className={`bg-gradient-to-r from-[#014A93] to-[#2B6FDF] text-white w-16 h-16 rounded-full shadow-2xl hover:shadow-3xl transition-all transform hover:scale-110 flex items-center justify-center group ${
          isDragging ? 'cursor-grabbing' : 'cursor-pointer'
        }`}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 1000,
        }}
      >
        {isOpen ? (
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <div className="relative">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white animate-pulse"></div>
          </div>
        )}
      </button>

      {/* Notification Badge - only show unseen bot messages */}
      {!isOpen && (() => {
        const unseenBotMessages = messages.filter(m => m.sender === 'bot' && m.id > lastSeenMessageId);
        return unseenBotMessages.length > 0 && (
          <div 
            className="absolute bg-red-500 text-white text-xs w-6 h-6 rounded-full flex items-center justify-center font-bold animate-bounce"
            style={{
              top: '-8px',
              right: '-8px',
              position: 'fixed',
              zIndex: 1001,
            }}
          >
            {unseenBotMessages.length}
          </div>
        );
      })()}
    </div>
  );
};

export default Chatbot;

