import React from 'react';

const CtaBanner = () => {
  return (
    <section className="py-16 sm:py-24 bg-white">
      <div className="w-full mx-auto px-[50px] text-center">
        <h2 className="text-3xl sm:text-5xl font-semibold text-slate-900">24/7 health support at your fingertips</h2>
        <p className="mt-4 max-w-4xl mx-auto text-lg text-slate-600">
          Our medical chatbot provides instant, reliable health information whenever you need it.
          No waiting, no appointments, just immediate assistance.
        </p>
        <div className="mt-8 flex items-center justify-center gap-6">
          <a href="#GetStarted" className="px-6 py-3 rounded-xl border border-slate-300 text-slate-900 hover:bg-slate-50">
            Get Started
          </a>
          <a href="#login" className="px-6 py-3 rounded-xl bg-[#2B6FDF] text-white hover:bg-[#2a63c4]">
            Login
          </a>
        </div>
      </div>
    </section>
  );
};

export default CtaBanner;


