import React from 'react';

const steps = [
  { title: 'Ask your health question', caption: 'Connect', desc: 'Type symptoms or concerns directly into our secure platform', cta: 'Explore', image: '/Feature_img1.png' },
  { title: 'Get personalized Health insights', caption: 'Analyze', desc: 'Receive clear, precise information based on your specific health query', cta: 'Discover', image: '/Feature_img2.png' },
  { title: 'Comprehensive guidance for your health journey', caption: 'Next step', desc: 'Recommendations for follow-up care or medical consultation', cta: 'Learn', image: '/Feature_img3.png' },
];

const HowItWorks = () => {
  return (
    <section id="howitworks" className="py-16 sm:py-24 bg-white">
      <div className="w-full mx-auto px-[50px]">
        <h2 className="text-3xl sm:text-5xl font-semibold text-slate-900 text-center">How our Medical Chatbot works</h2>
        <p className="mt-3 text-slate-600 text-center text-lg">Connect with intelligent health support in three easy steps</p>
        <div className="mt-14 grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((s, index) => (
            <article key={s.title} className={`bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden md:col-span-1 ${
              index === 2 ? 'flex flex-col md:flex-row' : ''
            }`}>
              {index === 2 ? (
                <>
                  {/* Portrait image on the left - 290 x 424 */}
                  <div className="bg-slate-100 flex justify-center items-center">
                    <img 
                      src={s.image} 
                      alt={s.title} 
                      className="object-cover"
                      style={{ width: '290px', height: '424px' }}
                    />
                  </div>
                  {/* Text content positioned above the image on the right */}
                  <div className="p-4 flex flex-col justify-start">
                    <div className="text-sm text-slate-500">{s.caption}</div>
                    <h3 className="mt-1 text-lg font-semibold text-slate-900">{s.title}</h3>
                    <p className="mt-2 text-slate-700 text-sm">{s.desc}</p>
                    <div className="mt-4">
                      <button type="button" className="px-3 py-1.5 rounded-md bg-[#2B6FDF] text-white hover:bg-[#2a63c4] text-sm">
                        {s.cta}
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* Regular layout for first two sections - 290 x 197 */}
                  <div className="bg-slate-100 flex justify-center items-center">
                    <img 
                      src={s.image} 
                      alt={s.title} 
                      className="object-cover"
                      style={{ width: '290px', height: '197px' }}
                    />
                  </div>
                  <div className="p-5">
                    <div className="text-sm text-slate-500">{s.caption}</div>
                    <h3 className="mt-2 text-xl font-semibold text-slate-900">{s.title}</h3>
                    <p className="mt-3 text-slate-700 text-sm">{s.desc}</p>
                    <div className="mt-5">
                      <button type="button" className="px-4 py-2 rounded-md bg-[#2B6FDF] text-white hover:bg-[#2a63c4]">
                        {s.cta}
                      </button>
                    </div>
                  </div>
                </>
              )}
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;