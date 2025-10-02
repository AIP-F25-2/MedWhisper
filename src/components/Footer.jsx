import React from 'react';

const Footer = () => {
  return (
    <footer className="mt-16 border-t border-slate-200">
      <div className="w-full mx-auto px-[50px] py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-slate-600">
          <img src="/LOGO.png" alt="PulseAI logo" className="h-8 w-8 rounded-md object-contain" />
          <span>© {new Date().getFullYear()} PulseAI</span>
        </div>
        <nav className="text-sm text-slate-600 flex items-center gap-4">
          <a href="#features" className="hover:text-brand-600">Features</a>
          <a href="#team" className="hover:text-brand-600">Team</a>
          <button type="button" className="hover:text-brand-600">Privacy</button>
        </nav>
      </div>
    </footer>
  );
};

export default Footer;


