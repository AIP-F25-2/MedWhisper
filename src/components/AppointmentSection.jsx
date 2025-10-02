import React from 'react';

const AppointmentSection = () => {
  return (
    <section className="py-16 sm:py-24 bg-white">
      <div className="w-full mx-auto px-[50px]">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="text-left">
            <h2 className="text-3xl sm:text-5xl font-bold text-slate-900 leading-tight">
              Seamless appointment scheduling
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Simplify your healthcare management with instant appointment booking
            </p>
            
            <div className="mt-12">
              <h3 className="text-2xl sm:text-4xl font-bold text-slate-900 leading-tight">
                Effortless medical coordination
              </h3>
              <p className="mt-4 text-lg text-slate-600">
                Connect with healthcare providers quickly and efficiently through our intelligent platform.
              </p>
              <div className="mt-8">
                <a href="#GetStarted" className="px-6 py-3 rounded-xl border border-slate-300 text-slate-900 hover:bg-slate-50">
                  Get Started
                </a>
              </div>
            </div>
          </div>
          
          <div className="relative flex justify-center">
            <div className="relative w-96 h-96 flex items-center justify-center">
              {/* Doctor figure placeholder */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-blue-100 rounded-3xl"></div>
              
              {/* Central stethoscope interface */}
              <div className="relative z-10 w-48 h-48 bg-white rounded-full shadow-2xl flex items-center justify-center border-4 border-blue-200">
                <div className="text-6xl">🫀</div>
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm">🩺</div>
              </div>
              
              {/* Surrounding medical icons */}
              <div className="absolute top-4 left-8 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-sm border-2 border-blue-200">💊</div>
              <div className="absolute top-4 right-8 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-sm border-2 border-blue-200">➕</div>
              <div className="absolute top-1/2 right-2 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-sm border-2 border-blue-200">💊</div>
              <div className="absolute bottom-8 right-8 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-sm border-2 border-blue-200">💉</div>
              <div className="absolute bottom-8 left-8 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-sm border-2 border-blue-200">🧴</div>
              <div className="absolute top-1/2 left-2 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-sm border-2 border-blue-200">➕</div>
              
              {/* Connecting dotted lines */}
              <div className="absolute inset-0 pointer-events-none">
                <svg className="w-full h-full" viewBox="0 0 400 400">
                  <defs>
                    <pattern id="dots" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
                      <circle cx="5" cy="5" r="1" fill="#3B82F6" opacity="0.4"/>
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
    </section>
  );
};

export default AppointmentSection;
