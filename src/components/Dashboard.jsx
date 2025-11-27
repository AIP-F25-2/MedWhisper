import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hi! I'm your PulseAI Copilot. How would you like to interact?",
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isUploadingAudio, setIsUploadingAudio] = useState(false);
  const [audioPermissionDenied, setAudioPermissionDenied] = useState(false);
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const navigate = useNavigate();

  // API Configuration - Same as Chatbot.jsx
  const API_BASE = 'https://e66adf64e3a5.ngrok-free.app';
  const FALLBACK_API_BASE = 'http://localhost:8010';
  const TEXT_ENDPOINT = '/qa';
  const VOICE_ENDPOINT = '/voice-qa';
  const DEFAULT_LANGUAGE = 'en';
  const DEFAULT_USER_ROLE = 'student';

  useEffect(() => {
    const checkUser = () => {
      const userData = localStorage.getItem('user');
      if (userData) {
        try {
          setUser(JSON.parse(userData));
        } catch (e) {
          console.error('Error parsing user data:', e);
          localStorage.removeItem('user');
          navigate('/');
        }
      } else {
        navigate('/');
      }
    };

    checkUser();
    window.addEventListener('userLogout', checkUser);
    window.addEventListener('storage', checkUser);

    return () => {
      window.removeEventListener('userLogout', checkUser);
      window.removeEventListener('storage', checkUser);
    };
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('user');
    window.dispatchEvent(new Event('userLogout'));
    navigate('/');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleQueryClick = (query) => {
    setInputValue(query);
    // Auto-submit when clicking a query
    setTimeout(() => {
      handleSubmit(null, query);
    }, 100);
  };

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

    // Hide welcome message and cards when first message is sent
    if (showWelcome) {
      setShowWelcome(false);
    }

    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
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

    // Hide welcome message when voice message is sent
    if (showWelcome) {
      setShowWelcome(false);
    }

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

  const handleSubmit = (e, queryText = null) => {
    if (e) {
      e.preventDefault();
    }
    const messageToSend = queryText || inputValue.trim();
    if (messageToSend) {
      sendMessage(messageToSend);
      setInputValue('');
    }
  };

  if (!user) {
    return null; // Will redirect
  }

  return (
    <div className={`min-h-screen flex flex-col border-l-[10px] border-r-[10px] ${darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-[#014A93]'}`}>
      {/* Header */}
      <header className={`${darkMode ? 'bg-gray-800' : 'bg-[#014A93]'} text-white px-6 py-4 flex items-center justify-between`}>
        {/* Logo */}
        <div className="flex items-center gap-3">
          <img 
            src="/LOGO.png" 
            alt="PulseAI Logo" 
            className="w-10 h-10 object-contain"
          />
          <span className="text-xl font-bold">PulseAI</span>
        </div>

        {/* Right side icons */}
        <div className="flex items-center gap-4">
          {/* Dark Mode Toggle */}
          <button 
            onClick={() => setDarkMode(!darkMode)}
            className="w-10 h-10 flex items-center justify-center hover:bg-white/10 rounded-lg transition-colors"
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {darkMode ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

          {/* Bell icon */}
          <button className="w-10 h-10 flex items-center justify-center hover:bg-white/10 rounded-lg transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>

          {/* Person/Profile icon */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="w-10 h-10 flex items-center justify-center hover:bg-white/10 rounded-lg transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </button>
            {showUserMenu && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowUserMenu(false)}
                />
                <div className={`absolute right-0 mt-2 w-48 rounded-lg shadow-xl py-2 z-50 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                  <div className={`px-4 py-2 border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                    <p className={`text-sm font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{user.full_name || 'User'}</p>
                    <p className={`text-xs truncate ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{user.email}</p>
                  </div>
                  <a href="#profile" className={`block px-4 py-2 text-sm ${darkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'}`} onClick={() => setShowUserMenu(false)}>Profile</a>
                  <a href="#settings" className={`block px-4 py-2 text-sm ${darkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'}`} onClick={() => setShowUserMenu(false)}>Settings</a>
                  <button
                    onClick={handleLogout}
                    className={`block w-full text-left px-4 py-2 text-sm text-red-600 ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                  >
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex">
        {/* Left Sidebar - Clinical Queries */}
        <aside className={`w-80 p-6 overflow-y-auto border-r ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="space-y-8">
            {/* Common Clinical Queries */}
            <div>
              <h2 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Common Clinical Queries</h2>
              <ul className="space-y-2">
                <li>
                  <button
                    onClick={() => handleQueryClick('Acute pain')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Acute pain
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Fever spikes')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Fever spikes
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Breathing difficulty')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Breathing difficulty
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Abnormal labs alert')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Abnormal labs alert
                  </button>
                </li>
              </ul>
            </div>

            {/* Within 1 Week */}
            <div>
              <h2 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Within 1 Week</h2>
              <ul className="space-y-2">
                <li>
                  <button
                    onClick={() => handleQueryClick('Radiology interpretation')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Radiology interpretation
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Lab trend analysis')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Lab trend analysis
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Timeline summary')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Timeline summary
                  </button>
                </li>
              </ul>
            </div>

            {/* Within 30 Days */}
            <div>
              <h2 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Within 30 Days</h2>
              <ul className="space-y-2">
                <li>
                  <button
                    onClick={() => handleQueryClick('Medication summaries')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Medication summaries
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Chronic case overview')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Chronic case overview
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Hospital visit summaries')}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center gap-2 ${darkMode ? 'text-gray-300 hover:text-blue-400 hover:bg-gray-700' : 'text-gray-700 hover:text-[#014A93] hover:bg-blue-50'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></span>
                    Hospital visit summaries
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </aside>

        {/* Main Content Panel */}
        <main className={`flex-1 flex flex-col overflow-hidden ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
          {/* Chat Messages Area */}
          <div className="flex-1 overflow-y-auto px-8 py-6">
            {showWelcome && messages.length === 1 ? (
              <>
                {/* Welcome Message */}
                <div className="mb-6">
                  <div className={`rounded-lg p-6 max-w-2xl ${darkMode ? 'bg-gray-800' : 'bg-blue-50'}`}>
                    <p className={`text-lg ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                      {messages[0].text}
                    </p>
                  </div>
                </div>

                {/* Interaction Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
                  {/* Speaking Card */}
                  <div className={`border-2 rounded-lg p-6 hover:border-[#014A93] hover:shadow-lg transition-all cursor-pointer ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                    <div className="flex flex-col items-center text-center">
                      <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${darkMode ? 'bg-gray-700' : 'bg-blue-100'}`}>
                        <svg className={`w-8 h-8 ${darkMode ? 'text-blue-400' : 'text-[#014A93]'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                      </div>
                      <h3 className={`text-lg font-semibold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Speaking</h3>
                      <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Ask aloud or describe a patient's condition.</p>
                    </div>
                  </div>

                  {/* Upload Clinical Records Card */}
                  <div className={`border-2 rounded-lg p-6 hover:border-[#014A93] hover:shadow-lg transition-all cursor-pointer ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                    <div className="flex flex-col items-center text-center">
                      <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${darkMode ? 'bg-gray-700' : 'bg-blue-100'}`}>
                        <svg className={`w-8 h-8 ${darkMode ? 'text-blue-400' : 'text-[#014A93]'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      </div>
                      <h3 className={`text-lg font-semibold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Upload Clinical Records</h3>
                      <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Upload lab reports, radiology images, notes, or PDFs</p>
                    </div>
                  </div>

                  {/* Typing Card */}
                  <div className={`border-2 rounded-lg p-6 hover:border-[#014A93] hover:shadow-lg transition-all cursor-pointer ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                    <div className="flex flex-col items-center text-center">
                      <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${darkMode ? 'bg-gray-700' : 'bg-blue-100'}`}>
                        <svg className={`w-8 h-8 ${darkMode ? 'text-blue-400' : 'text-[#014A93]'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </div>
                      <h3 className={`text-lg font-semibold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Typing</h3>
                      <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Type any clinical or patient question.</p>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              /* Chat Messages */
              <div className="space-y-4 max-w-4xl">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-3xl rounded-lg px-4 py-3 ${
                        message.sender === 'user'
                          ? 'bg-[#014A93] text-white'
                          : darkMode
                          ? 'bg-gray-800 text-gray-200'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                      <p className={`text-xs mt-1 ${message.sender === 'user' ? 'text-blue-100' : darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        {new Date(message.timestamp).toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                ))}
                {isTyping && (
                  <div className="flex justify-start">
                    <div className={`rounded-lg px-4 py-3 ${darkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
                      <div className="flex space-x-2">
                        <div className={`w-2 h-2 rounded-full animate-bounce ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`}></div>
                        <div className={`w-2 h-2 rounded-full animate-bounce ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`} style={{ animationDelay: '0.2s' }}></div>
                        <div className={`w-2 h-2 rounded-full animate-bounce ${darkMode ? 'bg-gray-500' : 'bg-gray-400'}`} style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Field at Bottom */}
          <div className="px-8 pb-8">
            <form onSubmit={handleSubmit} className="max-w-5xl">
              <div className={`relative flex items-center border-2 rounded-lg px-4 py-3 focus-within:border-[#014A93] transition-colors ${darkMode ? 'bg-gray-800 border-gray-700 focus-within:bg-gray-800' : 'bg-gray-50 border-gray-200 focus-within:bg-white'}`}>
                {/* Microphone icon on left */}
                <button
                  type="button"
                  onClick={handleToggleRecording}
                  disabled={isTyping || isUploadingAudio}
                  aria-pressed={isRecording}
                  className={`relative mr-3 transition-colors rounded-full p-2 ${
                    isRecording
                      ? 'bg-red-500 text-white animate-pulse'
                      : darkMode
                      ? 'text-gray-400 hover:text-blue-400 hover:bg-gray-700'
                      : 'text-gray-400 hover:text-[#014A93] hover:bg-gray-200'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                  title={
                    audioPermissionDenied
                      ? 'Microphone permission denied. Please enable microphone access.'
                      : isRecording
                      ? 'Stop recording'
                      : 'Start voice input'
                  }
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {isRecording ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    )}
                  </svg>
                  {isUploadingAudio && (
                    <span className={`absolute -bottom-2 left-1/2 transform -translate-x-1/2 text-[10px] uppercase tracking-wide ${darkMode ? 'text-blue-400' : 'text-[#014A93]'}`}>
                      Sending...
                    </span>
                  )}
                </button>

                {/* Input field */}
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Input your question here..."
                  disabled={isRecording}
                  className={`flex-1 bg-transparent border-none outline-none placeholder-gray-400 ${darkMode ? 'text-gray-200' : 'text-gray-900'} disabled:opacity-50`}
                />

                {/* Submit arrow on right */}
                <button
                  type="submit"
                  disabled={!inputValue.trim() || isTyping || isUploadingAudio || isRecording}
                  className={`ml-3 transition-colors ${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-[#014A93] hover:text-blue-700'} disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
              </div>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
