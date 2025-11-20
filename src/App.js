import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './components/Home';
import HowItWorks from './components/HowItWorks';
import CtaBanner from './components/CtaBanner';
import Team from './components/Team';
import Footer from './components/Footer';
import HoursBanner from './components/HoursBanner';
import AppointmentSection from './components/AppointmentSection';
import TransformBanner from './components/TransformBanner';
import Chatbot from './components/Chatbot';
import Dashboard from './components/Dashboard';

function LandingPage() {
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
      <Chatbot />
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
