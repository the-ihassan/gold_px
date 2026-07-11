import React from 'react';
import { Link } from 'react-router-dom';
import { FaHome, FaCalendarAlt, FaImages, FaUser } from 'react-icons/fa';

const Navbar = () => {
  return (
    <header className="gold-header">
      <div className="container nav-flex">
        <Link to="/" className="logo">GOLD<span>PX</span></Link>
        <nav className="nav-links">
          <Link to="/"><FaHome/> Home</Link>
          <Link to="/booking"><FaCalendarAlt/> Booking</Link>
          <Link to="/gallery"><FaImages/> Gallery</Link>
          <Link to="/dashboard"><FaUser/> Dashboard</Link>
          <Link to="/booking" className="btn-gold">Book Now</Link>
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
