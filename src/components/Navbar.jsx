import React, { useState, useEffect } from 'react';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';

const Navbar = () => {
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isSignupOpen, setIsSignupOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Check for logged-in user on component mount and when localStorage changes
  useEffect(() => {
    const checkUser = () => {
      const userData = localStorage.getItem('user');
      if (userData) {
        try {
          setUser(JSON.parse(userData));
        } catch (e) {
          console.error('Error parsing user data:', e);
          localStorage.removeItem('user');
        }
      } else {
        setUser(null);
      }
    };

    checkUser();
    
    // Listen for storage changes (when user logs in from another tab/window)
    window.addEventListener('storage', checkUser);
    
    // Custom event for when user logs in/out in same window
    window.addEventListener('userLogin', checkUser);
    window.addEventListener('userLogout', checkUser);

    return () => {
      window.removeEventListener('storage', checkUser);
      window.removeEventListener('userLogin', checkUser);
      window.removeEventListener('userLogout', checkUser);
    };
  }, []);

  const openLogin = () => {
    setIsLoginOpen(true);
    setIsSignupOpen(false);
  };

  const openSignup = () => {
    setIsSignupOpen(true);
    setIsLoginOpen(false);
  };

  const closeLogin = () => setIsLoginOpen(false);
  const closeSignup = () => setIsSignupOpen(false);

  const handleLogout = () => {
    localStorage.removeItem('user');
    setUser(null);
    setShowUserMenu(false);
    // Dispatch event to notify other components
    window.dispatchEvent(new Event('userLogout'));
  };

  return (
    <>
      <header className="sticky top-0 z-50 bg-[#014A93] text-white">
        <div className="w-full mx-auto px-[50px] h-[140px] flex items-center justify-between">
          <a href="#home" className="flex items-center gap-3">
            <img src="/LOGO.png" alt="PulseAI logo" className="h-[116px] w-[116px] rounded-md object-contain" />
          </a>
          <nav className="hidden md:flex items-center gap-10 text-[18px]">
            <a href="#home" className="hover:text-white/80">Home</a>
            <a href="#howitworks" className="hover:text-white/80">Features</a>
            <a href="#team" className="hover:text-white/80">Team</a>
          </nav>
          <div className="hidden md:flex items-center gap-4 text-[18px]">
            {user ? (
              // User is logged in - show user profile menu
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white font-semibold">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <span className="text-white">{user.full_name || user.email}</span>
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {showUserMenu && (
                  <>
                    {/* Backdrop to close menu when clicking outside */}
                    <div 
                      className="fixed inset-0 z-40" 
                      onClick={() => setShowUserMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl py-2 z-50">
                      <div className="px-4 py-3 border-b border-gray-200">
                        <p className="text-sm font-semibold text-gray-900">{user.full_name || 'User'}</p>
                        <p className="text-sm text-gray-500 truncate">{user.email}</p>
                      </div>
                      <a
                        href="#profile"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setShowUserMenu(false)}
                      >
                        View Profile
                      </a>
                      <a
                        href="#settings"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setShowUserMenu(false)}
                      >
                        Settings
                      </a>
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
            ) : (
              // User is not logged in - show login/signup buttons
              <>
                <button 
                  onClick={openSignup}
                  className="px-5 py-2 rounded-lg bg-[#2B6FDF] text-white hover:bg-[#2a63c4] transition-colors"
                >
                  Get Started
                </button>
                <button 
                  onClick={openLogin}
                  type="button" 
                  className="px-5 py-2 rounded-lg border border-white text-white hover:bg-white/10 transition-colors"
                >
                  Login
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Login and Signup Modals */}
      <LoginForm isOpen={isLoginOpen} onClose={closeLogin} onSwitchToSignup={openSignup} />
      <SignupForm isOpen={isSignupOpen} onClose={closeSignup} onSwitchToLogin={openLogin} />
    </>
  );
};

export default Navbar;


