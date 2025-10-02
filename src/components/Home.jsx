import React from 'react';

const Home = () => {
  return (
    <section id="home" className="relative overflow-hidden bg-[#014A93] text-white pt-4">
      <div className="w-full mx-auto px-[50px] py-16 sm:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-4xl sm:text-6xl font-semibold leading-tight tracking-tight">
              MedWhisper:
              <br />
              Multimodal Clinical
              <br />
              AI Assistant
            </h1>
            <p className="mt-6 text-white/85 text-lg max-w-2xl">
              AI-powered medical support that understands your health needs. Get instant,
              reliable information and guidance with a simple conversation.
            </p>
            <div className="mt-8 flex items-center gap-4">
              <a href="#pricing" className="px-6 py-3 rounded-lg bg-[#2B6FDF] text-white hover:bg-[#2a63c4]">
                Get Started
              </a>
              <a href="#login" className="px-6 py-3 rounded-lg border border-white/70 text-white hover:bg-white/10">
                Login In
              </a>
            </div>
          </div>
          <div className="relative">
            <div className="rounded-2xl overflow-hidden ring-1 ring-white/20 shadow-xl bg-white">
              <img src="/Dashboard.png" alt="Product dashboard" className="w-full h-auto" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Home;


