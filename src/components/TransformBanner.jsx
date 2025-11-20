import React, { useState, useEffect } from 'react';

const TransformBanner = () => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const checkUser = () => {
      const userData = localStorage.getItem('user');
      if (userData) {
        try {
          setUser(JSON.parse(userData));
        } catch (e) {
          setUser(null);
        }
      } else {
        setUser(null);
      }
    };

    checkUser();
    window.addEventListener('userLogin', checkUser);
    window.addEventListener('userLogout', checkUser);
    window.addEventListener('storage', checkUser);

    return () => {
      window.removeEventListener('userLogin', checkUser);
      window.removeEventListener('userLogout', checkUser);
      window.removeEventListener('storage', checkUser);
    };
  }, []);

  return (
    <section className="py-16 sm:py-24 bg-white">
      <div className="w-full mx-auto px-[50px] text-center">
        <h2 className="text-4xl sm:text-6xl font-bold text-slate-900 leading-tight">
          Transform your health experience
          <br />
          today
        </h2>
        <p className="mt-6 max-w-4xl mx-auto text-lg text-slate-600">
          Join thousands of users who have simplified their healthcare journey with our intelligent medical assistant.
        </p>
        {!user && (
          <div className="mt-8 flex items-center justify-center gap-6">
            <a href="#GetStarted" className="px-6 py-3 rounded-xl border border-slate-300 text-slate-900 hover:bg-slate-50">
              Get Started
            </a>
            <a href="#login" className="px-6 py-3 rounded-xl bg-[#2B6FDF] text-white hover:bg-[#2a63c4]">
              Login
            </a>
          </div>
        )}
      </div>
    </section>
  );
};

export default TransformBanner;
