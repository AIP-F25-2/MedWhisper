import React from 'react';

const Team = () => {
  const teamMembers = [
    { name: 'Taranjot Singh Bindra', role: 'Team Lead', image: '/team1.jpg' },
    { name: 'Mitalben Jayantibhai Pethani', role: 'Technical Lead', image: '/team2.jpg' },
    { name: 'Dhruv Dinesh Boricha', role: 'Computer Vision Engineer', image: '/team3.jpg' },
    { name: 'Neha Tamang', role: 'Visualization & UI/UX Designer', image: '/team4.jpg' },
    { name: 'Paramjit Singh', role: 'Front-end Developer', image: '/team5.jpg' },
    { name: 'Indraja Badepalli', role: 'Machine Learning Engineer', image: '/team6.jpg' },
    { name: 'Thejaswee Badepalle', role: 'Data Engineer', image: '/team7.jpg' },
  ];

  return (
    <section id="team" className="py-16 sm:py-24 bg-white">
      <div className="w-full mx-auto px-[50px]">
        <h2 className="text-3xl sm:text-5xl font-bold text-slate-900 text-center mb-12">Meet our Team</h2>
        
        <div className="relative max-w-6xl mx-auto">
          <div className="bg-[#014A93] rounded-3xl p-8 sm:p-12 relative overflow-hidden">
            {/* Decorative wave shapes */}
            <div className="absolute top-0 left-0 w-32 h-32 bg-blue-100 rounded-full opacity-30 -translate-x-16 -translate-y-16"></div>
            <div className="absolute bottom-0 right-0 w-40 h-40 bg-blue-100 rounded-full opacity-30 translate-x-20 translate-y-20"></div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 relative z-10">
              {teamMembers.map((member, index) => (
                <div key={member.name} className="text-center">
                  <div className="w-32 h-32 mx-auto mb-4 rounded-xl border-2 border-blue-200 overflow-hidden bg-slate-100">
                    <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm">
                      Photo
                    </div>
                  </div>
                  <h3 className="text-lg font-bold text-white mb-1">{member.name}</h3>
                  <p className="text-sm text-white/80">{member.role}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Team;
