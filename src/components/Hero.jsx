import React from 'react';

const Hero = () => {
  return (
    <section id="home" className="relative overflow-hidden bg-[#014A93] text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div>
            <h1 className="text-3xl sm:text-5xl font-bold tracking-tight">
              AI medical scribing that just works
            </h1>
            <p className="mt-4 text-white/80 text-lg">
              Turn conversations into clinical notes automatically. Secure, accurate, and fast.
            </p>
            <div className="mt-6 flex items-center gap-3">
              <a href="#pricing" className="px-5 py-3 rounded-md bg-white text-[#014A93] hover:bg-white/90">
                Start free trial
              </a>
              <a href="#features" className="px-5 py-3 rounded-md border border-white/30 text-white hover:bg-white/10">
                See features
              </a>
            </div>
            <div className="mt-6 text-xs text-white/70">HIPAA-ready. Works with telehealth or in-person.</div>
          </div>
          <div className="relative">
            <div className="aspect-video rounded-xl border border-white/20 bg-white shadow-sm flex items-center justify-center text-slate-400">
              Demo placeholder
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;


