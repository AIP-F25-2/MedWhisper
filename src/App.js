import Navbar from './components/Navbar';
import Home from './components/Home';
import HowItWorks from './components/HowItWorks';
import CtaBanner from './components/CtaBanner';
import Team from './components/Team';
import Footer from './components/Footer';
import HoursBanner from './components/HoursBanner';
import AppointmentSection from './components/AppointmentSection';
import TransformBanner from './components/TransformBanner';

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Home />
        <HowItWorks />
        <CtaBanner />
        <HoursBanner />
        <AppointmentSection />
        <TransformBanner />
        <Team />
      </main>
      <Footer />
    </div>
  );
}

export default App;
