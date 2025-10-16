import React, { useState, useRef, useEffect } from 'react';

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
  const [lastSeenMessageId, setLastSeenMessageId] = useState(1); // Track the last seen message
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const API_BASE = 'http://localhost:8001';
  const userId = 'web-user-' + Math.random().toString(36).substr(2, 9);

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
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender: userId,
          message: messageText,
        }),
      });

      const data = await response.json();
      const botReply = data.replies && data.replies[0] ? data.replies[0] : "Sorry, I couldn't process that.";

      const botMessage = {
        id: Date.now() + 1,
        text: botReply,
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I am currently unable to respond. Please make sure the backend server is running.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
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

  return (
    <div className="fixed bottom-4 right-2 z-50">
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
        {messages.length === 1 && !isTyping && (
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
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-[#014A93] focus:border-transparent text-sm"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isTyping}
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
        className="bg-gradient-to-r from-[#014A93] to-[#2B6FDF] text-white w-16 h-16 rounded-full shadow-2xl hover:shadow-3xl transition-all transform hover:scale-110 flex items-center justify-center group"
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
          <div className="absolute top-0 right-0 bg-red-500 text-white text-xs w-6 h-6 rounded-full flex items-center justify-center font-bold animate-bounce">
            {unseenBotMessages.length}
          </div>
        );
      })()}
    </div>
  );
};

export default Chatbot;

