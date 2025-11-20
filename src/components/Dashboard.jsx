import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const navigate = useNavigate();

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

  const handleQueryClick = (query) => {
    setInputValue(query);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      // Handle submission - can integrate with chatbot API
      console.log('Submitting query:', inputValue);
      // Reset input after submission
      setInputValue('');
    }
  };

  if (!user) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="bg-[#014A93] text-white px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
            {/* Robot head with plus sign icon */}
            <svg className="w-6 h-6 text-[#014A93]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="2" fill="none" />
            </svg>
          </div>
          <span className="text-xl font-bold">PulseAI</span>
        </div>

        {/* Right side icons */}
        <div className="flex items-center gap-4">
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
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl py-2 z-50">
                  <div className="px-4 py-2 border-b border-gray-200">
                    <p className="text-sm font-semibold text-gray-900">{user.full_name || 'User'}</p>
                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                  </div>
                  <a href="#profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" onClick={() => setShowUserMenu(false)}>Profile</a>
                  <a href="#settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" onClick={() => setShowUserMenu(false)}>Settings</a>
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
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
        <aside className="w-80 bg-white border-r border-gray-200 p-6 overflow-y-auto">
          <div className="space-y-8">
            {/* Common Clinical Queries */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Common Clinical Queries</h2>
              <ul className="space-y-2">
                <li>
                  <button
                    onClick={() => handleQueryClick('Acute pain')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Acute pain
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Fever spikes')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Fever spikes
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Breathing difficulty')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Breathing difficulty
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Abnormal labs alert')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Abnormal labs alert
                  </button>
                </li>
              </ul>
            </div>

            {/* Within 1 Week */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Within 1 Week</h2>
              <ul className="space-y-2">
                <li>
                  <button
                    onClick={() => handleQueryClick('Radiology interpretation')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Radiology interpretation
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Lab trend analysis')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Lab trend analysis
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Timeline summary')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Timeline summary
                  </button>
                </li>
              </ul>
            </div>

            {/* Within 30 Days */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Within 30 Days</h2>
              <ul className="space-y-2">
                <li>
                  <button
                    onClick={() => handleQueryClick('Medication summaries')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Medication summaries
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Chronic case overview')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Chronic case overview
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => handleQueryClick('Hospital visit summaries')}
                    className="w-full text-left text-gray-700 hover:text-[#014A93] hover:bg-blue-50 px-3 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                    Hospital visit summaries
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </aside>

        {/* Main Content Panel */}
        <main className="flex-1 flex flex-col bg-white">
          {/* Welcome Message */}
          <div className="p-8">
            <div className="bg-blue-50 rounded-lg p-6 max-w-2xl">
              <p className="text-lg text-gray-800">
                Hi, I'm your PulseAI Copilot. How would you like to interact?
              </p>
            </div>
          </div>

          {/* Interaction Cards */}
          <div className="px-8 pb-8 flex-1">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
              {/* Speaking Card */}
              <div className="bg-white border-2 border-gray-200 rounded-lg p-6 hover:border-[#014A93] hover:shadow-lg transition-all cursor-pointer">
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-[#014A93]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Speaking</h3>
                  <p className="text-sm text-gray-600">Ask aloud or describe a patient's condition.</p>
                </div>
              </div>

              {/* Upload Clinical Records Card */}
              <div className="bg-white border-2 border-gray-200 rounded-lg p-6 hover:border-[#014A93] hover:shadow-lg transition-all cursor-pointer">
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-[#014A93]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Clinical Records</h3>
                  <p className="text-sm text-gray-600">Upload lab reports, radiology images, notes, or PDFs</p>
                </div>
              </div>

              {/* Typing Card */}
              <div className="bg-white border-2 border-gray-200 rounded-lg p-6 hover:border-[#014A93] hover:shadow-lg transition-all cursor-pointer">
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-[#014A93]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Typing</h3>
                  <p className="text-sm text-gray-600">Type any clinical or patient question.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Input Field at Bottom */}
          <div className="px-8 pb-8">
            <form onSubmit={handleSubmit} className="max-w-5xl">
              <div className="relative flex items-center bg-gray-50 border-2 border-gray-200 rounded-lg px-4 py-3 focus-within:border-[#014A93] focus-within:bg-white transition-colors">
                {/* Microphone icon on left */}
                <button
                  type="button"
                  className="mr-3 text-gray-400 hover:text-[#014A93] transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </button>

                {/* Input field */}
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Input your question here..."
                  className="flex-1 bg-transparent border-none outline-none text-gray-900 placeholder-gray-400"
                />

                {/* Submit arrow on right */}
                <button
                  type="submit"
                  className="ml-3 text-[#014A93] hover:text-blue-700 transition-colors"
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
