import React from 'react';

const HoursBanner = () => {
  return (
    <section className="py-16 sm:py-24 bg-gradient-to-br from-blue-50 to-blue-100">
      <div className="w-full mx-auto px-[50px]">
        <div className="relative max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="text-left">
              <h2 className="text-4xl sm:text-6xl font-bold text-white leading-tight">
                24 hours
                <br />
                medical
                <br />
                services
              </h2>
              <p className="mt-4 text-white/70 text-lg">VECTOR ILLUSTRATION</p>
              <p className="mt-2 text-white text-lg">Seamless appointment</p>
            </div>
            <div className="relative flex justify-center">
              <div className="relative w-96 h-96 flex items-center justify-center">
                {/* Doctor figure placeholder */}
                <div className="absolute bottom-0 right-0 w-32 h-40 bg-white/20 rounded-t-full"></div>
                
                {/* Central 24/7 circle */}
                <div className="relative z-10 w-48 h-48 bg-blue-500 rounded-full shadow-2xl flex items-center justify-center border-4 border-white">
                  <div className="text-4xl font-bold text-white">24/7</div>
                </div>
                
                {/* Surrounding medical icons */}
                <div className="absolute top-4 left-8 w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm border-2 border-white">💊</div>
                <div className="absolute top-4 right-8 w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm border-2 border-white">📋</div>
                <div className="absolute top-1/2 right-2 w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm border-2 border-white">🛡️</div>
                <div className="absolute bottom-8 right-8 w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm border-2 border-white">🛒</div>
                <div className="absolute bottom-8 left-8 w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm border-2 border-white">💊</div>
                <div className="absolute top-1/2 left-2 w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm border-2 border-white">🏥</div>
                
                {/* Connecting dotted lines */}
                <div className="absolute inset-0 pointer-events-none">
                  <svg className="w-full h-full" viewBox="0 0 400 400">
                    <defs>
                      <pattern id="dots" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
                        <circle cx="5" cy="5" r="1" fill="white" opacity="0.6"/>
                      </pattern>
                    </defs>
                    <path d="M 200 50 Q 150 100 100 150" stroke="url(#dots)" strokeWidth="2" fill="none"/>
                    <path d="M 200 50 Q 250 100 300 150" stroke="url(#dots)" strokeWidth="2" fill="none"/>
                    <path d="M 350 200 Q 300 200 250 200" stroke="url(#dots)" strokeWidth="2" fill="none"/>
                    <path d="M 200 350 Q 250 300 300 250" stroke="url(#dots)" strokeWidth="2" fill="none"/>
                    <path d="M 200 350 Q 150 300 100 250" stroke="url(#dots)" strokeWidth="2" fill="none"/>
                    <path d="M 50 200 Q 100 200 150 200" stroke="url(#dots)" strokeWidth="2" fill="none"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HoursBanner;
