import React from 'react';

const steps = [
  { title: 'Ask your health question', caption: 'Connect', desc: 'Type symptoms or concerns directly into our secure platform.', cta: 'Explore' },
  { title: 'Get personalized Health insights', caption: 'Analyze', desc: 'Receive clear, precise information based on your specific query.', cta: 'Discover' },
  { title: 'Comprehensive guidance for your health journey', caption: 'Next step', desc: 'Recommendations for follow-up care or medical consultation.', cta: 'Learn' },
];

const HowItWorks = () => {
  return (
    <section id="howitworks" className="py-16 sm:py-24 bg-white">
      <div className="w-full mx-auto px-[50px]">
        <h2 className="text-3xl sm:text-5xl font-semibold text-slate-900 text-center">How our Medical Chatbot works</h2>
        <p className="mt-3 text-slate-600 text-center text-lg">Connect with intelligent health support in three steps</p>
        <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((s) => (
            <article key={s.title} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="aspect-[16/11] bg-slate-100">
                <img src="/Dashboard.png" alt={s.title} className="w-full h-full object-cover" />
              </div>
              <div className="p-6">
                <div className="text-sm text-slate-500">{s.caption}</div>
                <h3 className="mt-2 text-xl font-semibold text-slate-900">{s.title}</h3>
                <p className="mt-3 text-slate-700 text-sm">{s.desc}</p>
                <div className="mt-5">
                  <button type="button" className="px-4 py-2 rounded-md bg-[#2B6FDF] text-white hover:bg-[#2a63c4]">{s.cta}</button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;