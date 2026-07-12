import React from 'react';

const Gallery = () => {
  const images = ['/assets/images/gold1.jpg', '/assets/images/gold2.jpg', '/assets/images/gold3.jpg'];
  const videos = ['/assets/videos/hero-bg.mp4'];

  return (
    <div className="container" style={{ paddingTop: '4rem' }}>
      <h2 style={{ color: 'var(--gold)', marginBottom: '2rem' }}>Premium Gallery</h2>
      <div className="services-grid">
        {images.map((img, i) => (
          <div key={i} className="service-card fade-in-visible" style={{ padding: '0', overflow: 'hidden', textAlign: 'center', opacity: 1, transform: 'none' }}>
            <img src={img} alt="Gold PX" style={{ width: '100%', height: '200px', objectFit: 'cover' }} onError={(e) => { e.target.style.display = 'none'; }} />
            <h4 style={{ padding: '1rem', color: 'var(--cyan)' }}>Gallery Item {i+1}</h4>
          </div>
        ))}
        {videos.map((v, i) => (
          <div key={i} className="service-card fade-in-visible" style={{ padding: '0', overflow: 'hidden', opacity: 1, transform: 'none' }}>
            <video src={v} controls style={{ width: '100%', height: '200px', objectFit: 'cover' }} onError={(e) => { e.target.style.display = 'none'; }} />
            <h4 style={{ padding: '1rem', color: 'var(--gold)' }}>Demo Video</h4>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Gallery;
