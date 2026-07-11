import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';

const Landing = () => {
  useEffect(() => {
    const container = document.getElementById('particles');
    if (container) {
      for(let i=0; i<50; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        p.style.left = Math.random() * 100 + '%';
        p.style.animationDuration = (Math.random() * 5 + 3) + 's';
        p.style.animationDelay = Math.random() * 5 + 's';
        container.appendChild(p);
      }
    }
  }, []);

  return (
    <section className="hero">
      <div id="particles" className="particles"></div>
      <div className="container hero-content">
        <h1>Professional <span className="gradient-text">Lighting</span> Technology</h1>
        <p>World's No.1 Premium Lighting Platform. Pixel-perfect control for weddings, concerts, and corporate events.</p>
        <Link to="/booking" className="btn-gold">Book Your Event</Link>
      </div>
    </section>
  );
};

export default Landing;
