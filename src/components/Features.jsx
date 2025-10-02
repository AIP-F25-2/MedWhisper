import React from 'react';

const features = [
  { title: 'Accurate summaries', desc: 'Generate structured SOAP notes with medical-grade accuracy.' },
  { title: 'Realtime capture', desc: 'Capture visits live or upload recordings securely.' },
  { title: 'EHR-friendly', desc: 'Copy-paste or export to your existing EHR workflow.' },
  { title: 'Custom templates', desc: 'Match your specialty and personal documentation style.' },
  { title: 'Team collaboration', desc: 'Share with your team while keeping PHI secure.' },
  { title: 'Compliance', desc: 'Encryption at rest and in transit, access controls, audit trails.' },
];

const Features = () => {
  return (
    <section id="features" className="py-16 sm:py-24 bg-white">
      <div className="w-full mx-auto px-[50px]">
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Features</h2>
        <p className="mt-2 text-slate-600 max-w-2xl">Designed for clinicians to save time and improve the quality of documentation.</p>
        <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div key={f.title} className="p-6 rounded-xl border border-slate-200 hover:shadow-sm transition">
              <div className="h-10 w-10 rounded-md bg-brand-50 text-brand-700 flex items-center justify-center font-semibold">✓</div>
              <h3 className="mt-4 font-semibold text-slate-900">{f.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;


