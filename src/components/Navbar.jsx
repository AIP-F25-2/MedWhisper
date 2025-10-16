import React from 'react';

const Navbar = () => {
  return (
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
          <a href="#GetStarted" className="px-5 py-2 rounded-lg bg-[#2B6FDF] text-white hover:bg-[#2a63c4]">Get Started</a>
          <button type="button" className="px-5 py-2 rounded-lg border border-white text-white hover:bg-white/10">Login</button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;


