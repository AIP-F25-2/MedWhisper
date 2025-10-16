import React, { useState } from 'react';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';

const Navbar = () => {
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isSignupOpen, setIsSignupOpen] = useState(false);

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

  return (
    <>
      <header className="sticky top-0 z-50 bg-[#014A93] text-white">
        <div className="w-full mx-auto px-[50px] h-[140px] flex items-center justify-between mt-[20px]">
          <a href="#home" className="flex items-center gap-3">
            <img src="/LOGO.png" alt="PulseAI logo" className="h-[116px] w-[116px] rounded-md object-contain" />
          </a>
          <nav className="hidden md:flex items-center gap-10 text-[18px]">
            <a href="#home" className="hover:text-white/80">Home</a>
            <a href="#features" className="hover:text-white/80">Features</a>
            <a href="#team" className="hover:text-white/80">Team</a>
          </nav>
          <div className="hidden md:flex items-center gap-4 text-[18px]">
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


