import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Booking from './pages/Booking';
import Gallery from './pages/Gallery';
import Dashboard from './pages/Dashboard';
import './index.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/booking" element={<Booking />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
